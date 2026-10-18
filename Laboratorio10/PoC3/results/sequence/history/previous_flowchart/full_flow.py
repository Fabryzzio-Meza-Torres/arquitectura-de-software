"""Generate the complete timed flow from saved traces, without sending requests."""
import hashlib
import json
from html import escape
from pathlib import Path


def create_full_flow(here):
    source = here / "results/sequence/trace.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    case = next(c for c in data["cases"] if c["variant"] == "poc3")
    slow = set(case["slow_services"])
    events = case["events"]
    def first(kind, replica=None):
        return min(e["ms"] for e in events if e["event"] == kind and e.get("svc") in slow
                   and (replica is None or e.get("replica") == replica))
    others = max(e["ms"] for e in events if e.get("svc") not in slow
                 and e["event"] in ("return", "service_outcome"))
    winners = []
    for svc in case["slow_services"]:
        returned = [e for e in events if e["event"] == "return" and e.get("svc") == svc]
        if returned:
            winners.append(f"S{svc}: t={max(e['ms'] for e in returned):.1f} ms")
    preload = ", ".join(f"S{s}" for s in case["initial_cache_services"])
    # Every branch comes from ImprovedAPI.call_service/_attempt. Clock labels are
    # saved observations; alpha/beta and TTL labels are configured policy limits.
    diagram = f'''flowchart TB
    P["PRECARGA - antes de t=0<br/>3 servicios aleatorios: {preload}<br/>Independientes de los 2 servicios lentos"]
    A["SOLICITUD - t=0 ms<br/>Consultar 10 servicios en paralelo"]
    B["MISMA POLITICA POR SERVICIO<br/>2 primarios lentos aleatorios; otros 8 completados a t={others:.1f} ms"]
    C{{"Circuit breaker permite consultar?"}}
    D["SERVICIO PROBLEMATICO<br/>Un bloque agrupa los 2 primarios lentos<br/>Inicio observado: t={first('send', 0):.1f} ms"]
    H["HEDGING / REPLICA<br/>Si el original sigue pendiente al superar alpha, consultar otra instancia<br/>alpha inicial: 17 ms; replicas iniciadas a t={first('send', 1):.1f} ms"]
    V["RESPUESTA VALIDA POR SERVICIO<br/>{' / '.join(winners)}<br/>Primera valida gana; cancelar pendientes, actualizar cache y cerrar circuito"]
    F["INTENTO FALLIDO<br/>Error o ninguna respuesta valida antes de beta<br/>beta inicial: 34,1 ms desde el inicio de cada intento<br/>Contar fallo; desde 5 fallos, abrir circuito por 1 s"]
    Q{{"Hay cache fresca con edad hasta 1 s?"}}
    R{{"Circuito permite, quedan intentos<br/>y hay presupuesto de reintento?"}}
    J["REINTENTO CON BACKOFF Y JITTER<br/>Espera aleatoria: 0-5 ms, luego 0-10 ms<br/>Hasta 3 intentos; presupuesto ratio 10 %, capacidad 20"]
    S{{"Hay cache con edad hasta 5 s?"}}
    K["RESPUESTA CON CACHE<br/>Dato vigente segun TTL; resultado degradado<br/>Precargar no fuerza latencia cero"]
    X["SIN DATO VALIDO<br/>Cache ausente o vencida: marcar fallo"]
    Z["RESPUESTA FINAL DE LA API<br/>Esperar los 10 resultados: fallo si alguno falla;<br/>degradada si usa cache; ok si todos responden<br/>Ejemplo observado: t={case['total_ms']:.1f} ms, resultado {case['outcome']}"]
    P --> A
    A --> B
    B --> C
    C -->|"Si: cerrado o prueba semiabierta"| D
    C -->|"No: abierto o prueba ya en curso"| S
    D -->|"Valida antes de alpha"| V
    D -->|"Sin respuesta; sigue pendiente"| H
    D -->|"Error sin tareas pendientes"| F
    H -->|"Primera valida antes de beta"| V
    H -->|"Timeout o error"| F
    F --> Q
    Q -->|"Si"| K
    Q -->|"No"| R
    R -->|"Si"| J
    J --> C
    R -->|"No"| S
    S -->|"Si"| K
    S -->|"No"| X
    V --> Z
    K --> Z
    X --> Z
'''
    output = here / "results/sequence"
    (output / "flujo_completo.mmd").write_text(diagram, encoding="utf-8")
    metadata = {
        "new_experiment_requests": 0,
        "source_trace_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_case": "poc3", "seed": case["seed"], "request": case["request"],
        "measured_total_ms": case["total_ms"], "preloaded_services": case["initial_cache_services"],
        "slow_services": case["slow_services"],
        "clock_labels": "Observed milliseconds in one saved request, not p50/p95/p99",
        "conditional_branches": "Policy routes, not all executed by the displayed request",
        "alpha_beta": "Initial values; adaptive in operation; beta is measured from each attempt start",
        "breaker_recovery": "After 1 s, a single logical attempt probes; success closes, failure reopens",
        "parallelism": "The same policy applies to all ten services. Eight others are condensed; times are not summed"
    }
    (output / "flujo_completo.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    # Fixed layout keeps the retry cycle readable; numbered references replace
    # long return arrows. SVG is native vector output with an explicit background.
    left, right, width = 48, 780, 672
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1640" viewBox="0 0 1500 1640">',
           '<rect width="1500" height="1640" fill="#ffffff"/>',
           '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#64748b"/></marker></defs>']
    def text(x, y, value, size=20, bold=False, color="#24364b"):
        svg.append(f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(value)}</text>')
    def box(x, y, title, lines, tone="normal", height=144):
        fill, border = {"normal": ("#eff8f6", "#238479"), "policy": ("#fff8ed", "#bd8536"),
                        "setup": ("#eef3fb", "#7286a7")}[tone]
        svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="12" fill="{fill}" stroke="{border}" stroke-width="2"/>')
        text(x + 22, y + 34, title, 23, True)
        for i, line in enumerate(lines):
            text(x + 22, y + 67 + i * 27, line, 19)
    def arrow(x1, y1, x2, y2):
        svg.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>')
    text(48, 52, "PoC3 | Flujo completo y tiempos", 34, True)
    text(48, 88, "Izquierda: una solicitud medida. Derecha: las rutas de proteccion si algo falla.", 22)
    text(48, 119, "Un bloque agrupa los 2 servicios problematicos; la politica se aplica por separado a los 10 servicios.", 20)
    text(left, 169, "RECORRIDO OBSERVADO", 21, True, "#187c70")
    text(right, 169, "RUTAS ALTERNATIVAS / LIMITES", 21, True, "#a16d24")
    box(left, 190, "0. Precarga antes de la solicitud", ["3 servicios aleatorios con datos disponibles en cache.",
        f"Ejemplo: {preload}; seleccion independiente de los lentos.", "Los datos siguen sujetos al TTL; no fuerzan latencia cero."], "setup")
    box(left, 366, "1. Solicitud y consultas en paralelo | t=0 ms", ["La API consulta los 10 servicios; exactamente 2 demoran.",
        f"Los otros 8 terminan a t={others:.1f} ms en este ejemplo.", "El tiempo total no es la suma de las llamadas paralelas."])
    decisions = [e["ms"] for e in events if e["event"] == "breaker_decision" and e.get("svc") in slow]
    box(left, 542, "2. Comprobar el circuit breaker", [f"Decision observada: t={min(decisions):.1f}-{max(decisions):.1f} ms.",
        "Cerrado: permite las 2 consultas problematicas.", "Si ya estuviera abierto, se usa la ruta A." ])
    box(left, 718, f"3. Servicio problematico | t={first('send', 0):.1f} ms", ["Se inicia una consulta original por servicio.",
        "Si responde antes de alpha, se acepta el dato valido.", "alpha inicial = 17 ms; se adapta con las observaciones."])
    box(left, 894, f"4. Hedging y replicas | t={first('send', 1):.1f} ms", ["Como los originales siguen pendientes, se activan replicas.",
        "Original y replica compiten: gana la primera valida.", "beta inicial = 34,1 ms desde el inicio de cada intento."])
    box(left, 1070, "5. Resolver cada servicio y cancelar pendientes", [" / ".join(winners),
        "Cancelar lo que queda pendiente; actualizar la cache.", "Cada respuesta valida reinicia y cierra su circuito."])
    box(right, 190, "Como leer los tiempos", ["t=... ms: instante observado desde esta solicitud.",
        "alpha/beta: limites iniciales por intento, adaptativos.", "TTL, backoff y cooldown: reglas, no tiempos observados."], "setup")
    box(right, 366, "A. Si el circuito esta abierto", ["Desde 5 intentos fallidos, suspende consultas por 1 s.",
        "Despues permite una prueba: exito cierra; fallo reabre.", "Omite el servicio y valida cache hasta 5 s: ir a E."], "policy")
    box(right, 542, "B. Si el intento termina sin dato valido", ["Error o ninguna respuesta valida antes de beta.",
        "Cuenta un fallo y cancela las tareas pendientes.", "El fallo puede abrir el circuito; luego se evalua C."], "policy")
    box(right, 718, "C. Intentar respuesta con cache fresca", ["Si la edad del dato es hasta 1 s, responde con cache.",
        "Se marca como degradada, no como dato nuevo.", "Si no hay dato fresco, se evalua el reintento D."], "policy")
    box(right, 894, "D. Reintentar si la politica lo permite", ["Circuito disponible + menos de 3 intentos + presupuesto.",
        "Backoff aleatorio: 0-5 ms y luego 0-10 ms; volver a 2.", "Presupuesto: ratio 10 %, capacidad 20. Si no, ir a E."], "policy")
    box(right, 1070, "E. Ultimo respaldo con cache vigente", ["Hasta 5 s de edad: devuelve dato y marca degradada.",
        "Sin cache o con dato vencido: marca fallo.", "Responder rapido sin dato valido sigue siendo un fallo."], "policy")
    for y in (334, 510, 686, 862, 1038):
        arrow(left + width / 2, y, left + width / 2, y + 29)
    for y in (686, 862, 1038):
        arrow(right + width / 2, y, right + width / 2, y + 29)
    # Two branches are shown without crossing the timelines. Others use the
    # lettered/numbered references in their boxes.
    arrow(left + width, 966, right, 966)
    text(721, 947, "si falla", 15)
    # Align the cross-column failure branch with B rather than the retry box.
    svg.pop(); svg.pop()
    svg.append('<path d="M720,966 L746,966 L746,614 L780,614" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>')
    text(721, 798, "B", 17, True)
    arrow(left + width / 2, 1214, left + width / 2, 1264)
    arrow(right + width / 2, 1214, right + width / 2, 1264)
    svg.append('<rect x="48" y="1270" width="1404" height="164" rx="12" fill="#eef3fb" stroke="#7286a7" stroke-width="2"/>')
    text(72, 1307, f"6. Agregar los 10 resultados y responder | ejemplo observado: t={case['total_ms']:.1f} ms", 25, True)
    text(72, 1344, "Si alguno falla: fallo. Si usa cache y ninguno falla: degradada. Si todos responden: ok.", 22)
    text(72, 1382, "En la solicitud mostrada, las replicas respondieron a tiempo: resultado ok.", 22)
    text(48, 1490, "Ejemplo de una traza guardada: no es un p95/p99 ni una promesa de latencia maxima.", 21, True)
    text(48, 1524, "Las rutas A-E describen decisiones alternativas; no se ejecutaron todas en el ejemplo de la izquierda.", 20)
    text(48, 1558, "No se ejecutaron nuevas solicitudes ni se repitio el benchmark de 50 000 para generar esta imagen.", 20)
    svg.append('</svg>')
    (output / "flujo_completo.svg").write_text("\n".join(svg), encoding="utf-8")
    return output


if __name__ == "__main__":
    print(create_full_flow(Path(__file__).resolve().parent))
