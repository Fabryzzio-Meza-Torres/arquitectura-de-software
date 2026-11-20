from pathlib import Path
import json, hashlib, urllib.request, zipfile
from huggingface_hub import HfApi, snapshot_download

root = Path(__file__).resolve().parent
metadata = {}
for ds in ['fiqa', 'trec-covid']:
    archive = root / 'data' / f'{ds}.zip'
    if not archive.exists():
        tmp = archive.with_suffix('.part')
        urllib.request.urlretrieve(f'https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{ds}.zip', tmp)
        tmp.replace(archive)
    with zipfile.ZipFile(archive) as z:
        for file in ['corpus.jsonl', 'queries.jsonl', 'qrels/test.tsv']:
            target = root / 'data' / ds / file
            if not target.exists():
                z.extract(f'{ds}/{file}', root / 'data')
    metadata[ds] = {'zip_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
    print('DATA_PREPARED', ds, flush=True)
name = 'cross-encoder/ms-marco-MiniLM-L6-v2'
info = HfApi().model_info(name)
snapshot_download(name, revision=info.sha, local_dir=root / 'models' / 'reranker',
    allow_patterns=['config.json', 'model.safetensors', 'pytorch_model.bin', 'tokenizer.json',
                    'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt'])
metadata['reranker'] = {'specified_alias': 'cross-encoder/ms-marco-MiniLM-L-6-v2',
    'canonical_model': name, 'revision': info.sha, 'precision': 'float32'}
(root / 'prepared_test.json').write_text(json.dumps(metadata, indent=2))
print('TEST_PREPARATION_COMPLETE', flush=True)
