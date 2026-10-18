"""Restore the complete Spanish sequence source without running experiments."""
import json
import hashlib
from pathlib import Path


def create_full_flow(here):
    output = here / "results/sequence"
    metadata = json.loads((output / "secuencia_completa.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256((output / "trace.json").read_bytes()).hexdigest()
    if digest != metadata["source_trace_sha256"]:
        raise ValueError("Update the editable sequence and its timestamps after recording a new trace")
    source = (output / "secuencia_completa.mmd").read_text(encoding="utf-8")
    (output / "flujo_completo.mmd").write_text(source, encoding="utf-8")
    (output / "flujo_completo.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


if __name__ == "__main__":
    print(create_full_flow(Path(__file__).resolve().parent))
