"""Package only the current supplement, figures and reproducibility sources."""
import hashlib
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED
from evidence import ROOT, verify_inputs


def build_archives():
    verify_inputs()
    files = set()
    for directory in ['octa_gtrqc_sim', 'scripts', 'tests', 'data', 'validation', 'supplementary', 'docs/source']:
        files.update(p for p in (ROOT / directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.ipynb'} and p.name != 'manifest.json')
    files.update(ROOT / name for name in ['README.md','LICENSE','pyproject.toml','poetry.lock','data/manifest.json'])
    files.update((ROOT / 'validation/native').glob('*/manifest.json'))
    files.add(ROOT / 'supplementary/figures/manifest.json')
    if any(p.name in {'main_2.tex','R1.tex','Proton.pdf','poc2.zip'} for p in files):
        raise ValueError('External manuscript or notebook archive entered the delivery')
    commit = subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
    record = {'scope':'Supplement and figure generation only; external papers and notebooks excluded.',
              'base_commit':commit.stdout.strip() if commit.returncode==0 else None,
              'files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
    manifest = ROOT / 'supplementary/manifest.json'
    manifest.write_text(json.dumps(record,indent=2)+'\n')
    files.add(manifest)
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    selections=[('supplementary-overleaf.zip',{ROOT/'supplementary/supplementary.tex',ROOT/'supplementary/README.md',*(ROOT/'supplementary/figures').glob('*.pdf')},ROOT/'supplementary'),
                ('supplementary-reproducibility.zip',files,ROOT)]
    for name,paths,base in selections:
        with ZipFile(out/name,'w',ZIP_DEFLATED) as archive:
            for path in sorted(paths):archive.write(path,path.relative_to(base).as_posix())
        print(out/name)


if __name__=='__main__':
    build_archives()
