"""Export only this experiment's reviewable artifacts, never models or environments."""
from pathlib import Path
import json,hashlib,tarfile,subprocess
root=Path(__file__).resolve().parent
analysis=json.loads((root/'analysis_summary.json').read_text())
assert analysis['passed'] and analysis['capacity_validated'] is False
assert json.loads((root/'final_verification.json').read_text())['complete_conditions']==39
acct=subprocess.check_output(['sacct','-j','63909,63911,63913,63917,63919','--parsable2','--format=JobID,JobName,Partition,State,ExitCode,Start,End,Elapsed,NodeList,AllocCPUS,ReqMem,AllocTRES'],text=True)
(root/'slurm_accounting.txt').write_text(acct)
states=subprocess.check_output(['sacct','-X','-j','63919,63913','-n','-P','--format=JobID,State'],text=True)
assert '63919|COMPLETED' in states and '63913|COMPLETED' in states,states
state=json.loads((root/'run_state.json').read_text())
state.update(phase='complete and verified',trec_capacity_qps=None,protocol='complementary_fixed_absolute_load')
(root/'run_state.json').write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n')
files=set(root.glob('*.py'))|set(root.glob('*.sbatch'))|set(root.glob('*.json'))|set(root.glob('*.md'))
for name in ['requirements_fiqa.txt','environment_used.txt','reference_fiqa_summary.csv','allocation_63911.txt','allocation_63919.txt','slurm_accounting.txt','concurrent_jobs_63919_midrun.txt','concurrent_jobs_63919_late.txt','tabla_paper_trec-covid.csv','fitness_por_repeticion.csv','hedging_pareado.csv','hedging_exposicion_por_solicitud.csv','trabajo3_latencia_trec_covid_khipu.ipynb']:
 p=root/name
 assert p.is_file(),name
 files.add(p)
for folder in ['logs','figs','pilot','results_trec_covid_completo_v4','results_trec_covid_carga_fija_v4']:
 files.update(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files={p for p in files if p.name not in ['export_manifest.json'] and p.suffix not in ['.pyc']}
assert all(p.resolve().is_relative_to(root) and not p.is_symlink() for p in files)
manifest={str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)}
(root/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
files.add(root/'export_manifest.json')
archive=root/'trec_khipu_63919_verified.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(files): tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
print(json.dumps(dict(archive=str(archive),files=len(files),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
