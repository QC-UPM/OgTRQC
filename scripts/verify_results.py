"""Compare a native campaign with retained reviewed numeric reference outputs.

Run with Poetry after the native campaign. External notebooks are not needed. The comparison fails closed and
writes a JSON record; tolerances allow optimizer and eigensolver roundoff.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def verify(native: Path, reference: Path) -> dict:
    """Compare independent native and archived calculation outputs.

    Args:
        native: Root produced by ``proton-study --study all``.
        reference: Compact reviewed numeric reference outputs.

    Returns:
        JSON-serializable comparison record with residuals and tolerances.

    Notes:
        Failed comparisons are recorded; the command-line entry point exits
        nonzero after writing the complete result.
    """
    checks = []

    def compare(name: str, actual, expected, atol: float, rtol: float = 0.) -> None:
        a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
        passed = a.shape == b.shape and bool(np.allclose(a, b, atol=atol, rtol=rtol))
        error = float(np.max(abs(a - b))) if a.shape == b.shape else None
        checks.append(dict(name=name, passed=passed, max_absolute_error=error, atol=atol, rtol=rtol))

    def require(name: str, passed: bool) -> None:
        checks.append(dict(name=name, passed=bool(passed)))

    main = json.loads((Path(__file__).resolve().parents[1] / 'data/reference_scalars.json').read_text())
    scores = pd.read_csv(native / 'calibration/scores.csv').set_index('model')
    compare('holdout_rmse', scores.loc['distributed', 'RMSE'], main['external_source_data']['holdout_RMSE'], 2e-7)
    compare('holdout_r2', scores.loc['distributed', 'R2'], main['external_source_data']['holdout_R2'], 2e-7)
    continuum = json.loads((native / 'continuum/metadata.json').read_text())
    compare('constant_D_convergence_order', continuum['observed_order'], main['matched_continuum']['observed_order'], 1e-5)
    uncertainty = json.loads((native / 'uncertainty/metadata.json').read_text())
    require('all_100_bootstrap_refits_converged', uncertainty['successful_replicates'] == uncertainty['requested_replicates'] == 100)
    compare('bootstrap_evaluation_rmse_interval', uncertainty['evaluation_only_rmse_interval'],
            main['external_source_data']['holdout_RMSE_95_CI'], 1e-6)
    compare('prediction_interval_coverage', uncertainty['coverage'], main['external_source_data']['predictive_interval_coverage'], 1 / 87)
    r2 = reference / 'identifiability'
    actual = pd.read_csv(native / 'identifiability/additional_profile_intervals.csv').set_index('parameter')
    expected = pd.read_csv(r2 / 'additional_profile_intervals.csv').set_index('parameter')
    compare('five_profile_endpoints', actual[['lower', 'upper']], expected.loc[actual.index, ['lower', 'upper']], 2e-6)
    actual_grid = pd.read_csv(native / 'identifiability/original_alpha_profile_31_points.csv')
    expected_grid = pd.read_csv(r2 / 'original_alpha_profile_31_points.csv')
    compare('original_alpha_grid', actual_grid.alpha_A, expected_grid.alpha_A, 2e-5)
    compare('original_alpha_profile_sse', actual_grid.sse, expected_grid.sse, 1e-6)
    r3 = reference / 'refinement'
    actual = pd.read_csv(native / 'refinement/full_generator.csv')
    expected = pd.read_csv(r3 / 'full_generator_refinement.csv')
    require('R3_same_meshes_and_cases', actual[['case', 'N']].equals(expected[['case', 'N']]))
    compare('R3_full_generator_errors', actual.relative_L2_error, expected.relative_L2_error, 2e-10, 2e-5)
    compare('R3_full_generator_gaps', actual.gap_s_1, expected.gap_s_1, 2e-11, 2e-7)
    require('R3_mass_conservation', actual.mass_error.max() < 1e-10)
    require('R3_gap_bound', bool((actual.gap_s_1 >= actual.lower_bound_s_1).all()))
    require('R3_entropy_dissipation', bool((actual.entropy_derivative_s_1 < 0).all()))
    require('R3_detailed_balance', actual.db_residual.max() < 1e-12)
    addendum = reference / 'review'
    actual = pd.read_csv(native / 'review/scores.csv')
    expected = pd.read_csv(addendum / 'leave_one_field_out.csv')
    mapping = {'Single exponential': 'single', 'Stretched exponential': 'stretched',
               'Distributed relaxation': 'distributed', 'Biexponential (six parameters)': 'biexponential'}
    expected.model = expected.model.map(mapping)
    expected = expected.rename(columns={'field_kV_cm': 'field_kv_cm'})
    columns = ['field_kv_cm', 'model']
    a = actual.set_index(columns).sort_index()
    b = expected.set_index(columns).sort_index()
    compare('all_16_retrospective_RMSEs', a.RMSE, b.RMSE, 2e-6)
    compare('all_16_training_SSEs', a.train_sse, b.train_sse, 2e-6)
    actual_sensitivity = pd.read_csv(native / 'transport_sensitivity/sensitivity.csv')
    expected_sensitivity = pd.read_csv(addendum / 'transport_sensitivity.csv')
    compare('transport_coefficient_diffusivities', actual_sensitivity.D_eff_m2_s, expected_sensitivity.D_eff_m2_s, 0., 2e-6)
    starts = pd.read_csv(native / 'start_sensitivity/audit.csv')
    require('optimizer_start_audit', starts.success.all() and abs(starts.rss_difference).max() < 1e-6)
    record = dict(all_passed=all(c['passed'] for c in checks), checks=checks,
                  scope='Current native-to-recorded-reference comparison; not a new notebook replay or physical experiment.')
    return record


def main() -> None:
    """Write comparison results and exit nonzero if any check failed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, default=Path('generated/native'))
    parser.add_argument('--reference', type=Path, default=Path('validation/reference'))
    parser.add_argument('--output', type=Path, default=Path('generated/verification.json'))
    args = parser.parse_args()
    record = verify(args.native, args.reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))
    if not record['all_passed']:
        raise SystemExit('Migration comparison failed; inspect the JSON record.')


if __name__ == '__main__':
    main()
