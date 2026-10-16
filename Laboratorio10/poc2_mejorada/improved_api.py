# poc 2: el diagrama con las mejoras que salieron del comparativo con la variante B
# - alpha/beta adaptativos por servicio
# - retry con backoff, jitter y presupuesto
# - breaker half-open con una sola sonda
# - cache de dos niveles: fresca (1 s) responde de inmediato, vieja (5 s) solo con el breaker abierto
# - mode B = reintentar antes de usar la cache (la version anterior, se deja para comparar)
import asyncio, random, statistics, time
from collections import deque

from simcore import N_SERVICES, PROBLEM_SERVICES, BETA_CAP_MS


class HalfOpenBreaker:

    def __init__(self, threshold=5, cooldown=1.0):
        self.threshold, self.cooldown = threshold, cooldown
        self.fail, self.open_until, self.probing = 0, 0.0, False

    def allow(self, now):
        if now < self.open_until:
            return False
        if self.fail >= self.threshold:
            if self.probing:
                return False
            self.probing = True
            return True
        return True

    def is_open(self, now):
        return now < self.open_until

    def on_success(self):
        self.fail, self.open_until, self.probing = 0, 0.0, False

    def on_failure(self, now):
        self.fail += 1
        self.probing = False
        if self.fail >= self.threshold:
            self.open_until = now + self.cooldown


class RetryBudget:

    def __init__(self, ratio=0.10, cap=20.0):
        self.ratio, self.cap, self.tokens = ratio, cap, cap

    def deposit(self):
        self.tokens = min(self.cap, self.tokens + self.ratio)

    def try_spend(self):
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class ImprovedAPI:
    def __init__(self, backend, alpha_ms, beta_ms, mode="C", max_attempts=3, ttl_fresh_s=1.0, ttl_max_s=5.0,
                 backoff_base_ms=5.0, retry_ratio=0.10, margin_factor=1.5):
        assert mode in ("B", "C")
        self.mode = mode
        self.name = "PoC 2: mejorada" if mode == "C" else "B: retry primero (iteracion previa)"
        self.backend = backend
        self.alpha0, self.beta0 = alpha_ms / 1000.0, beta_ms / 1000.0
        self.m0 = backend.cfg.base_median_ms / 1000.0
        self.max_attempts = max_attempts
        self.ttl_fresh, self.ttl_max = ttl_fresh_s, ttl_max_s
        self.backoff = backoff_base_ms / 1000.0
        self.margin_factor = margin_factor
        svcs = range(1, N_SERVICES + 1)
        self.window = {s: deque(maxlen=200) for s in svcs}
        self.median = {s: self.m0 for s in svcs}
        self._obs = {s: 0 for s in svcs}
        self.breakers = {s: HalfOpenBreaker() for s in svcs}
        self.budget = RetryBudget(retry_ratio)
        self.cache = {}
        self.cache_ages = []
        self.degraded = self.degraded_fresh = self.degraded_stale = 0
        self.failed_calls = self.hedges = self.retries = self.retries_denied = 0
        self.breaker_short_circuits = self.timeouts = 0
        self.notifications = []
        backend.warm_up()
        now = time.monotonic()
        for s in PROBLEM_SERVICES:
            self.cache[s] = now

    def _observe(self, svc, seconds):
        w = self.window[svc]
        w.append(seconds)
        self._obs[svc] += 1
        if len(w) >= 30 and self._obs[svc] % 20 == 0:
            self.median[svc] = statistics.median(w)

    # alpha y beta suben con la mediana observada, sin pasar de 100 ms
    def thresholds(self, svc):
        m = self.median[svc]
        scale = max(1.0, m / self.m0)
        beta = min(self.beta0 * scale, BETA_CAP_MS / 1000.0)
        alpha = min(self.alpha0 * scale, beta - self.margin_factor * m)
        return max(alpha, 0.5 * self.alpha0), beta

    async def _attempt(self, req, svc, attempt):
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        alpha, beta = self.thresholds(svc)
        primary = asyncio.ensure_future(self.backend.call(req, svc, 0, attempt))
        done, _ = await asyncio.wait({primary}, timeout=alpha)
        if done:
            self._observe(svc, loop.time() - t0)
            return True
        self.hedges += 1
        hedge = asyncio.ensure_future(self.backend.call(req, svc, 1, attempt))
        done, pending = await asyncio.wait({primary, hedge}, timeout=max(beta - alpha, 0.001),
                                           return_when=asyncio.FIRST_COMPLETED)
        for p in pending:
            p.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        if done:
            self._observe(svc, loop.time() - t0)
            return True
        return False

    def _cacheable(self, svc):
        return svc in PROBLEM_SERVICES

    def _age(self, svc):
        ts = self.cache.get(svc)
        return None if ts is None else time.monotonic() - ts

    # todo dato de cache se cuenta como degradado y se mide su antiguedad
    def _serve_cache(self, svc, age, tier):
        self.degraded += 1
        if tier == "fresh":
            self.degraded_fresh += 1
        else:
            self.degraded_stale += 1
        self.cache_ages.append(age)
        return "cache"

    def _stale_fallback(self, req, svc):
        age = self._age(svc) if self._cacheable(svc) else None
        if age is not None and age <= self.ttl_max:
            return self._serve_cache(svc, age, "stale")
        self.failed_calls += 1
        self.notifications.append(f"GG req={req} svc={svc}")
        return "failed"

    async def call_service(self, req, svc):
        br = self.breakers[svc]
        self.budget.deposit()
        for attempt in range(1, self.max_attempts + 1):
            if not br.allow(time.monotonic()):
                self.breaker_short_circuits += 1
                return self._stale_fallback(req, svc)
            if await self._attempt(req, svc, attempt):
                br.on_success()
                if self._cacheable(svc):
                    self.cache[svc] = time.monotonic()
                return "ok"
            self.timeouts += 1
            now = time.monotonic()
            br.on_failure(now)
            if self.mode == "C" and self._cacheable(svc):
                age = self._age(svc)
                if age is not None and age <= self.ttl_fresh:
                    return self._serve_cache(svc, age, "fresh")
            if br.is_open(now):
                return self._stale_fallback(req, svc)
            if attempt == self.max_attempts:
                break
            if not self.budget.try_spend():
                self.retries_denied += 1
                break
            self.retries += 1
            await asyncio.sleep(random.uniform(0, self.backoff * 2 ** (attempt - 1)))
        return self._stale_fallback(req, svc)

    async def handle(self, req):
        outs = await asyncio.gather(*(self.call_service(req, s) for s in range(1, N_SERVICES + 1)))
        if "failed" in outs:
            return "failed"
        return "degraded" if "cache" in outs else "ok"
