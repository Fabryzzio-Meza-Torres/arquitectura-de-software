"""Submit the frozen DAG once; persist IDs after every accepted submission."""
from pathlib import Path
import argparse, json, os, subprocess, time
parser=argparse.ArgumentParser()
parser.add_argument("--preflight-job",type=int,required=True)
parser.add_argument("--smoke-job",type=int,required=True)
args=parser.parse_args()
import base

root=Path(__file__).resolve().parent
assert not (root/'jobs.json').exists(),'Jobs already submitted: inspect jobs.json instead of duplicating'
smoke=root/'smoke_validation/resultados'
assert json.loads((smoke/'calidad_completa.json').read_text())['ok']
assert json.loads((smoke/'rendimiento_completo.json').read_text())['ok']
assert json.loads((smoke/'notebook_verificado.json').read_text())['errors']==0
assert json.loads((root/'preflight_ok.json').read_text())['precision']=='float32'
state=dict(project=str(root),preflight_job=args.preflight_job,smoke_job=args.smoke_job,
 output=str(root/'resultados'),logs=str(root/'logs'),input_package=str(root/'entrada_comun'),
 submitted_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),maximum_allocated_compute_time='7 hours plus queues',
 reference_experiment=dict(failed_pilot_jobs=[64070,64072],bf16_check_job=64075))
def save():base.dump(root/'jobs.json',state)
def submit(key,script,dependency):
 command=['sbatch','--account='+os.environ['SLURM_ACCOUNT'],'--parsable','--kill-on-invalid-dep=yes',f'--dependency={dependency}',script]
 result=subprocess.run(command,cwd=root,capture_output=True,text=True)
 if result.returncode:
  state['submission_error']=dict(stage=key,stderr=result.stderr,stdout=result.stdout);save()
  raise RuntimeError(f'{key}: {result.stderr}')
 job=int(result.stdout.strip().split(';')[0]);state[key]=job;save()
 print(f'{key}={job}',flush=True)
 return job
q=submit('quality_job','quality.sbatch',f'afterok:{args.smoke_job}')
p=submit('performance_job','performance.sbatch',f'afterok:{q}')
r=submit('report_job','report.sbatch',f'afterany:{q}:{p}')
state['submission_complete']=True;save()
print(json.dumps(state),flush=True)
