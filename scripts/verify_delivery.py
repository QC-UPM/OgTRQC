"""Verify a delivery ZIP and rebuild it in an isolated clean extraction."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile
from evidence import ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=ROOT/'dist/supplementary-reproducibility.zip')
    parser.add_argument('--recalculate',action='store_true',help='Also run the complete native campaign and numeric comparisons.')
    args=parser.parse_args()
    work=Path(tempfile.mkdtemp(prefix='supplement-clean-'))
    with ZipFile(args.archive) as archive:
        for name in archive.namelist():
            if not (work/name).resolve().is_relative_to(work):raise ValueError('Unsafe archive path')
            if name.endswith('.ipynb') or Path(name).name in {'main_2.tex','R1.tex','Proton.pdf','poc2.zip'}:
                raise ValueError(f'Excluded external source in ZIP: {name}')
        archive.extractall(work)
    manifest=json.loads((work/'supplementary/manifest.json').read_text())
    for name,digest in manifest['files'].items():
        if hashlib.sha256((work/name).read_bytes()).hexdigest()!=digest:raise ValueError(f'Checksum mismatch: {name}')
    env=dict(os.environ,PYTHONPATH=str(work),MPLBACKEND='Agg')
    commands=[['-m','pytest','-q'],['scripts/build_supplement.py','--no-package']]
    if args.recalculate:
        commands += [['-m','octa_gtrqc_sim.proton.cli','--study','all','--output','generated/native'],['scripts/verify_results.py','--native','generated/native']]
    for command in commands:
        print('Running:', ' '.join(command),flush=True)
        subprocess.run([sys.executable,*command],cwd=work,env=env,check=True)
    record={'scope':'Clean delivery extraction using the installed Poetry interpreter; no original papers or notebooks present.',
            'verified_files':len(manifest['files']),'commands':commands,'all_passed':True,
            'native_recalculation':args.recalculate,'tested_archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest()}
    if args.recalculate:
        result=json.loads((work/'generated/verification.json').read_text())
        record['numeric_comparisons']=len(result['checks']);record['numeric_comparisons_passed']=result['all_passed']
    (ROOT/'validation/delivery_check.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Clean delivery verification passed:',work)


if __name__=='__main__':
    main()
