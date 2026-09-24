"""Poetry console entry point for paper-aligned MVP studies."""

import argparse
from octa_gtrqc_sim.proton.presentation import ArtifactView, PaperPresenter


def main() -> None:
    """Parse CLI options and dispatch reproducible studies through the presenter."""
    parser = argparse.ArgumentParser(description='Paper-aligned Hx–NdNiO3 reduced models (MVP).')
    parser.add_argument('--study', choices=['calibration', 'review', 'uncertainty', 'identifiability',
                                          'transport_sensitivity', 'refinement', 'hidden_state',
                                          'start_sensitivity', 'continuum', 'all'], default='calibration')
    parser.add_argument('--output', default='paper_results', help='Artifact destination directory.')
    parser.add_argument('--bootstrap-repetitions', type=int, default=100)
    parser.add_argument('--original-profile-only', action='store_true', help='Skip the five additional R2.5 profiles.')
    parser.add_argument('--reference-cells', type=int, default=8192)
    args = parser.parse_args()
    presenter = PaperPresenter(ArtifactView(args.output), progress=lambda text: print(text, flush=True))
    for root in presenter.run(args.study, bootstrap_repetitions=args.bootstrap_repetitions,
                              additional_profiles=not args.original_profile_only, reference_cells=args.reference_cells):
        print(f'Artifacts: {root}')


if __name__ == '__main__':
    main()
