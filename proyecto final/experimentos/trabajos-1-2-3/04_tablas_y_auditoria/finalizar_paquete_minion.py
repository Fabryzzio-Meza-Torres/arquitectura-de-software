"""Finalize provenance and integrity after successful evidence/report verification."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[1]
out=root/'outputs/MINION_integrado'
new=out/'05_trabajo3_khipu_trec'
verification=json.loads((new/'final_verification.json').read_text())
analysis=json.loads((new/'analysis_summary.json').read_text())
assert verification['passed'] and verification['complete_conditions']==39
assert analysis['passed'] and analysis['notebook_errors']==0 and analysis['figures']==9
assert analysis['capacity_validated'] is False
inventory=json.loads((out/'04_tablas_y_auditoria/inventario_series.json').read_text())
assert len(inventory)==4 and sum(x['summary_rows'] for x in inventory)==156
assert all(x['script_matches_metadata'] for x in inventory)
trec=next(x for x in inventory if x['series']=='trec-covid_khipu')
assert trec['capacity_qps'] is None and trec['external_load_reference_qps']==8
for path in out.rglob('*'):
    assert not (path.is_file() and path.suffix in ['.pyc','.pem','.key']),str(path)
manifest={str(p.relative_to(out)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 for p in sorted(out.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'}
(out/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
archive=root/'outputs/MINION_Trabajos_1_2_3_integrados.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(out.rglob('*')):
        if p.is_file(): z.write(p,arcname=str(Path(out.name)/p.relative_to(out)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for relative,record in manifest.items():
        assert hashlib.sha256(z.read(out.name+'/'+relative)).hexdigest()==record['sha256']
result=dict(passed=True,files=len(manifest),archive_bytes=archive.stat().st_size,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),summary_rows=156,paired_hedging_checks=12,capacity_validated_trec=False)
(root/'outputs/verificacion_paquete_MINION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
