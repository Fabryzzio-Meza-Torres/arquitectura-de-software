"""Validate the published snapshot without external dependencies or GPU."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parent


def check():
    expected = json.loads((ROOT / 'PUBLIC_SHA256.json').read_text(encoding='utf-8'))
    for name, digest in expected.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    candidates = json.loads((ROOT / 'resultados/candidatos.json').read_text())
    rankings = json.loads((ROOT / 'resultados/rankings.json').read_text())
    assert len(candidates) == 50
    for query, rows in candidates.items():
        ids = {row['id'] for row in rows}
        assert len(ids) == len(rows) <= 20
        assert ids == set(rankings[query]['fusion']) == set(rankings[query]['LLM'])
    assert sum(map(len, candidates.values())) == 893
    scores = json.loads((ROOT / 'resultados/scores_llm.json').read_text())
    assert len(scores) == 893
    assert len({(row['qid'], row['docid']) for row in scores}) == 893
    assert all(math.isfinite(row['score']) and 0 <= row['score'] <= 1 for row in scores)
    with (ROOT / 'resultados/latencia_solicitudes.csv').open(newline='') as stream:
        requests = list(csv.DictReader(stream))
    assert len(requests) == 2000
    for method in ['fusion', 'LLM']:
        rows = [row for row in requests if row['method'] == method]
        assert len(rows) == 1000 and all(row['status'] == 'ok' for row in rows)
    assert all(row['top3'].split('|') == rankings[row['qid']]['LLM'][:3]
               for row in requests if row['method'] == 'LLM')
    notebook = json.loads((ROOT / 'experimentos_ejecutados.ipynb').read_text(encoding='utf-8'))
    cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    assert len(cells) == 5 and all(cell.get('execution_count') is not None for cell in cells)
    assert not [output for cell in cells for output in cell.get('outputs', []) if output['output_type'] == 'error']
    sensitive = re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}')
    for name in expected:
        path = ROOT / name
        assert path.suffix not in {'.sqlite', '.faiss', '.safetensors', '.zip'}, name
        if path.suffix == '.png':
            continue
        content = path.read_text(encoding='utf-8')
        assert not sensitive.search(content), f'Potential secret in {name}'
        # Construct patterns in parts so this validator does not flag its own source.
        private_path = '/' + 'home/'
        assert private_path not in content, f'Private home path in {name}'
        windows_path = re.compile(r'[A-Za-z]:' + r'[\\/]+Users[\\/]')
        assert not windows_path.search(content), f'Private Windows path in {name}'
    print(json.dumps(dict(files_verified=len(expected), queries=50, candidate_pairs=893,
        latency_requests=2000, notebook_code_cells=len(cells), errors=0), indent=2))


if __name__ == '__main__':
    check()
