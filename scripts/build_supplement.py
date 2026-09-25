"""Generate the current figures, supplementary.tex, PDF and delivery ZIPs."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
from evidence import ROOT
from export_publication_figures import main as export_figures
from render_supplement import generate
from package_supplement import build_archives


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-refresh',action='store_true',help='Compile delivered source/figures without regenerating them.')
    parser.add_argument('--no-package',action='store_true',help='Compile without creating ZIP archives.')
    args=parser.parse_args()
    if not shutil.which('pdflatex'):
        raise SystemExit('Install pdfLaTeX or compile supplementary.tex and figures/ on Overleaf.')
    if not args.no_refresh:
        export_figures()
        generate()
    with tempfile.TemporaryDirectory(prefix='supplement-build-') as tmp:
        work=Path(tmp)
        shutil.copyfile(ROOT/'supplementary/supplementary.tex',work/'supplementary.tex')
        shutil.copytree(ROOT/'supplementary/figures',work/'figures')
        command=['pdflatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','-no-shell-escape','supplementary.tex']
        for _ in range(3):
            result=subprocess.run(command,cwd=work,capture_output=True,text=True)
            if result.returncode:
                print(result.stdout[-6000:]);raise SystemExit('Supplement compilation failed')
        log=(work/'supplementary.log').read_text(errors='replace')
        (Path(tempfile.gettempdir())/'proton-supplement-build.log').write_text(log)
        if any(t in log for t in ['There were undefined references','There were undefined citations']):
            raise SystemExit('Unresolved cross-references')
        shutil.copyfile(work/'supplementary.pdf',ROOT/'supplementary/supplementary.pdf')
        print('Built supplementary/supplementary.pdf')
        for line in log.splitlines():
            if 'Overfull' in line:print(line)
    if not args.no_package:build_archives()


if __name__=='__main__':
    main()
