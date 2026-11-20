from pathlib import Path
import json,sys,hashlib,importlib.metadata as md,subprocess
root=Path(__file__).resolve().parent
reference=json.loads((root/'reference_fiqa_run_meta.json').read_text())
alpha=json.loads((root/'alpha.json').read_text())
assert sys.version.split()[0]==reference['python'].split()[0]=='3.11.11'
assert hashlib.sha256((root/'minion_bench.py').read_bytes()).hexdigest()==reference['script_sha256']
assert alpha==reference['alpha_json']
versions={k:md.version(k) for k in reference['libraries']}
assert versions==reference['libraries'],(versions,reference['libraries'])
import minion_bench as bench
assert bench.FROZEN_CONFIG==reference['frozen_config']
smi=subprocess.check_output(['nvidia-smi'],text=True)
assert 'RTX A6000' in smi
result=dict(passed=True,reference_job_id=reference['slurm_job_id'],reference_node=reference['node'],
    python=sys.version.split()[0],versions=versions,source_sha256=reference['script_sha256'],
    alpha=.85,frozen_config_identical=True,intentional_changes=['dataset=trec-covid','fresh dataset-specific calibration','output paths','authorized account'],
    source_environment='reference job 63828 on ds001',
    limits=['GPU is shared; concurrent load may differ',
            'Reference run did not record exact MiniLM cache revision; this run records the prepared revision'])
(root/'comparability_preflight.json').write_text(json.dumps(result,indent=2))
print('COMPARABILITY_PREFLIGHT_PASSED',json.dumps(result),flush=True)
