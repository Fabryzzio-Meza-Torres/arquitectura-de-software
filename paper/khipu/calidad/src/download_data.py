"""Descarga y verifica datasets BEIR (NFCorpus, TREC-COVID y FiQA-2018).

Uso:
  python src/download_data.py                      # los dos, en data/
  python src/download_data.py --datasets nfcorpus

Deja data/<nombre>/{corpus.jsonl, queries.jsonl, qrels/*.tsv} y registra md5 y sha256 en data/MANIFEST.json.
Si el dataset ya está descargado, no vuelve a bajarlo (usar --force para repetir).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import force_utf8_output  # noqa: E402

BASE_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{name}.zip"
DATASETS = ["nfcorpus", "trec-covid", "fiqa"]
# md5 publicado en el README de BEIR. Para nfcorpus y fiqa no lo verificamos: se registra el calculado.
KNOWN_MD5 = {"trec-covid": "ce62140cb23feb9becf6270d0d1fe6d1"}


def file_hashes(path: Path) -> tuple[str, str]:
    md5, sha = hashlib.md5(), hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def _ssl_context():
    """En algunos Windows falla la verificación de certificados; con certifi instalado se usa su lista de confianza."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=60, context=_ssl_context()) as resp, open(tmp, "wb") as out:
        total, done = int(resp.headers.get("Content-Length") or 0), 0
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / 1e6:.0f}/{total / 1e6:.0f} MB", end="", flush=True)
    print()
    tmp.replace(dest)


def _safe_extract(zpath: Path, dest: Path) -> None:
    dest_resolved = dest.resolve()
    with zipfile.ZipFile(zpath) as z:
        for member in z.namelist():
            if not (dest_resolved / member).resolve().is_relative_to(dest_resolved):
                raise ValueError(f"Ruta insegura dentro del zip: {member}")
        z.extractall(dest)


def download(name: str, data_root: Path, base_url: str = BASE_URL, force: bool = False) -> dict:
    target = data_root / name
    if (target / "corpus.jsonl").exists() and not force:
        print(f"[{name}] ya existe, no se descarga.")
        return {"name": name, "status": "ya_existia"}

    zpath = data_root / "_zips" / f"{name}.zip"
    if force or not zpath.exists():
        url = base_url.format(name=name)
        print(f"[{name}] descargando {url}")
        _fetch(url, zpath)
    md5, sha = file_hashes(zpath)
    expected = KNOWN_MD5.get(name)
    entry = {"name": name, "status": "descargado", "md5": md5, "sha256": sha, "bytes": zpath.stat().st_size,
             "md5_esperado": expected, "md5_coincide": None if expected is None else md5 == expected}
    if expected and md5 != expected:
        print(f"[{name}] AVISO: el md5 no coincide con el publicado ({md5} != {expected}).")
    _safe_extract(zpath, data_root)
    if not (target / "corpus.jsonl").exists():
        raise FileNotFoundError(f"Tras descomprimir no existe {target / 'corpus.jsonl'}")
    return entry


def update_manifest(data_root: Path, entries: list) -> None:
    path = data_root / "MANIFEST.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for e in entries:
        if e["status"] == "descargado":
            manifest[e["name"]] = {k: v for k, v in e.items() if k not in ("name", "status")}
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", nargs="+", default=DATASETS)
    ap.add_argument("--data-root", default=str(Path(__file__).resolve().parents[1] / "data"))
    ap.add_argument("--base-url", default=BASE_URL, help="plantilla con {name}; sirve para pruebas locales (file://)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    root = Path(args.data_root)
    entries = [download(n, root, args.base_url, args.force) for n in args.datasets]
    update_manifest(root, entries)
    print("Listo. Manifiesto en", root / "MANIFEST.json")


if __name__ == "__main__":
    force_utf8_output()
    try:
        main()
    except Exception as e:  # mensaje claro si falla la red
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
