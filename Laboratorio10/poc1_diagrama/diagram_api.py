# poc 1: la arquitectura del diagrama tal cual, sin mejoras
import asyncio, time

from simcore import Breaker, N_SERVICES, PROBLEM_SERVICES


class DiagramAPI:
    name = "PoC 1: diagrama"

    def __init__(self, backend, alpha_ms, beta_ms, max_attempts=3):
        self.backend = backend
        self.alpha, self.beta = alpha_ms / 1000.0, beta_ms / 1000.0
        self.max_attempts = max_attempts
        self.breakers = {s: Breaker() for s in range(1, N_SERVICES + 1)}
        self.cache = {}
        self.cache_ages = []
        self.degraded = self.failed_calls = self.hedges = self.retries = 0
        self.breaker_short_circuits = self.timeouts = 0
        self.notifications = []
        backend.warm_up()
        now = time.monotonic()
        for s in PROBLEM_SERVICES:
            self.cache[s] = now

    # hedged request: si pasa alpha se manda a la otra replica, gana la primera y se cancela la otra
    async def _attempt(self, req, svc, attempt):
        primary = asyncio.ensure_future(self.backend.call(req, svc, 0, attempt))
        done, _ = await asyncio.wait({primary}, timeout=self.alpha)
        if done:
            return True
        self.hedges += 1
        hedge = asyncio.ensure_future(self.backend.call(req, svc, 1, attempt))
        done, pending = await asyncio.wait({primary, hedge}, timeout=self.beta - self.alpha,
                                           return_when=asyncio.FIRST_COMPLETED)
        for p in pending:
            p.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        return bool(done)

    def _serve_cache(self, svc):
        self.degraded += 1
        self.cache_ages.append(time.monotonic() - self.cache[svc])
        return "cache"

    # beta vencido -> circuit breaker + fallback: con cache responde, sin cache hace retry (max 3), despues GG
    async def call_service(self, req, svc):
        br = self.breakers[svc]
        for attempt in range(1, self.max_attempts + 1):
            if not br.allow(time.monotonic()):
                self.breaker_short_circuits += 1
                if svc in self.cache:
                    return self._serve_cache(svc)
                break
            if await self._attempt(req, svc, attempt):
                br.on_success()
                if svc in PROBLEM_SERVICES:
                    self.cache[svc] = time.monotonic()
                return "ok"
            self.timeouts += 1
            br.on_failure(time.monotonic())
            if svc in self.cache:
                return self._serve_cache(svc)
            if attempt < self.max_attempts:
                self.retries += 1
        self.failed_calls += 1
        self.notifications.append(f"GG req={req} svc={svc}")
        return "failed"

    async def handle(self, req):
        outs = await asyncio.gather(*(self.call_service(req, s) for s in range(1, N_SERVICES + 1)))
        if "failed" in outs:
            return "failed"
        return "degraded" if "cache" in outs else "ok"
