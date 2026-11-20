import json, os, socket, time
from pathlib import Path
import numpy as np
import torch
from torch._native.registry import deregister_op_overrides
import base

deregister_op_overrides(disable_dispatch_keys='CUDA')
torch.set_num_threads(1)
torch.manual_seed(42)
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
scorer = base.Scorer()
pairs = [('Does the document discuss ACE2 and coronavirus?', text) for text in [
    'The study investigates ACE2 receptor binding by SARS-CoV-2.',
    'This paper discusses agricultural crop prices and international trade.',
    'The authors examine coronavirus transmission and infection in humans. ' * 200,
    'We measured viral binding to the ACE2 receptor in human cells. ' * 30,
]]
records = []
for batch in [1, 4, 8]:
    t = time.perf_counter()
    scores, effective = scorer.score(pairs, batch)
    assert len(scores) == len(pairs)
    for row in scores:
        assert np.isfinite(row['score']) and 0 <= row['score'] <= 1, row
        assert np.isfinite(row['label_mass']) and row['label_mass'] > 0, row
        assert np.all(np.isfinite(row['probabilities'])), row
    records.append(dict(batch=batch, effective=effective, seconds=time.perf_counter()-t, scores=scores))
drift = max(abs(a['score']-b['score']) for a,b in zip(records[0]['scores'],records[1]['scores']))
assert drift <= .001, f'Float32 short-batch score drift too large: {drift}'
base.dump(Path(__file__).parent/'preflight_ok.json', dict(
    ok=True, job=os.environ.get('SLURM_JOB_ID'), node=socket.gethostname(),
    gpu=torch.cuda.get_device_name(), precision='float32', records=records,
    max_batch_score_difference=drift, scope='real-model numerical and padding check; synthetic documents, not quality evidence'))
print('PREFLIGHT_OK', drift, flush=True)
