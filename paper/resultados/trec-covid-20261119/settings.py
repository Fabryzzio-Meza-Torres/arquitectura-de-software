"""Public filesystem configuration; model weights and data stay outside Git."""
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get('MINION_DATA_ROOT', ROOT / 'data' / 'trec-covid')).expanduser()
BGE_PATH = Path(os.environ.get('MINION_BGE_PATH', ROOT / 'models' / 'bge-base-en-v1.5')).expanduser()


def llm_metadata():
    metadata = json.loads((ROOT / 'modelo_preparado.json').read_text(encoding='utf-8'))
    configured = os.environ.get('MINION_LLM_PATH')
    if not configured:
        raise RuntimeError('Set MINION_LLM_PATH to the local snapshot of the recorded Qwen model revision.')
    model_path = Path(configured).expanduser().resolve()
    if not model_path.is_dir():
        raise FileNotFoundError('MINION_LLM_PATH must point to an existing model snapshot directory.')
    metadata['path'] = str(model_path)
    return metadata
