from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,snapshot_download
root=Path(__file__).resolve().parent
cache=root/'hf_home/hub'
metadata={}
for name,revision in [('BAAI/bge-base-en-v1.5','a5beb1e3e68b9ab74eb54cfd186867f64f240e1a'),
                      ('cross-encoder/ms-marco-MiniLM-L-6-v2',None)]:
    info=HfApi().model_info(name,revision=revision)
    path=snapshot_download(name,revision=info.sha,cache_dir=cache,
        allow_patterns=['config.json','model.safetensors','tokenizer.json','tokenizer_config.json',
            'special_tokens_map.json','vocab.txt','sentence_bert_config.json','config_sentence_transformers.json',
            'modules.json','1_Pooling/config.json','README.md'])
    metadata[name]=dict(revision=info.sha,path=path)
    print('MODEL_READY',name,info.sha,flush=True)
(root/'prepared_models.json').write_text(json.dumps(metadata,indent=2))
files=['corpus.jsonl','queries.jsonl','qrels/test.tsv']
checks={f:hashlib.sha256((root/'data/trec-covid'/f).read_bytes()).hexdigest() for f in files}
(root/'data_hashes.json').write_text(json.dumps(checks,indent=2))
print('MODELS_AND_DATA_PREPARED',flush=True)
