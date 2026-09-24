"""Physical invariants and notebook-to-package regression checks."""

from dataclasses import replace
import ast
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.optimize._numdiff import approx_derivative

from octa_gtrqc_sim.proton.dataset import PolarizationDataset
from octa_gtrqc_sim.proton.structure import StructuralModel
from octa_gtrqc_sim.proton.transport import DeviceConfig, TransportModel, KB_EV_K
from octa_gtrqc_sim.proton.diagnostics import RecoverabilityDiagnostic
from octa_gtrqc_sim.proton.relaxation import RelaxationModel, RelaxationKind, experimental_metrics
from octa_gtrqc_sim.proton.audits import RefinementStudy, ContinuumStudy, TransportSensitivityStudy
from octa_gtrqc_sim.proton.studies import CalibrationStudy
from octa_gtrqc_sim.proton.presentation import PaperPresenter, ArtifactView

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def data():
    return PolarizationDataset.load()


@pytest.fixture(scope='module')
def fit(data):
    return RelaxationModel().fit(data)


def test_embedded_data_integrity_and_partition(data):
    assert data.source_matrix.shape == (87, 12)
    assert data.observed.shape == (87, 4)
    assert data.time_s[-1] == 1.
    np.testing.assert_array_equal(data.fields_kv_cm, [133., 267., 400., 533.])
    assert data.provenance['embedded_matrix_sha256'].startswith('859f76869e')


def test_structural_calibration_and_variational_force():
    model = StructuralModel()
    assert model.k_a == pytest.approx(10.3784205761, rel=1e-9)
    assert model.k_r == pytest.approx(36.6666666667)
    assert model.e_a == pytest.approx(.17403869463781)
    c = np.array([.1, .4, .3, .2])
    qa, qr = model.equilibrium(c)
    f, fr = model.forces(c, qa, qr)
    np.testing.assert_allclose(f, 0)
    assert fr == 0.
    perturbed = qa + .01
    force, _ = model.forces(c, perturbed, qr)
    step = 1e-7
    shifted = perturbed.copy()
    shifted[1] += step
    gradient = (model.free_energy(c, shifted, qr) - model.free_energy(c, perturbed, qr)) / step
    assert gradient == pytest.approx(-force[1], rel=1e-5)
    assert model.free_energy(c, qa, qr) < model.free_energy(c, perturbed, qr)


@pytest.mark.parametrize('profile', [[], [-.1, .2], [.2, 1.1], [np.nan, .2], [[.1, .2]]])
def test_invalid_occupancy_is_rejected(profile):
    with pytest.raises(ValueError):
        TransportModel().freeze(np.asarray(profile))


@pytest.mark.parametrize('n', [16, 32, 64])
@pytest.mark.parametrize('case', ['symmetric', 'ramp'])
def test_transport_physical_invariants(n, case):
    model = TransportModel()
    generator = model.freeze(RefinementStudy.background(n, case))
    audit = generator.audit()
    assert audit['db_residual'] < 1e-12
    assert audit['relative_column_residual'] < 1e-12
    assert audit['relative_stationarity_error'] < 1e-12
    assert audit['gap_s_1'] >= audit['lower_bound_s_1'] > 0
    assert audit['entropy_derivative_s_1'] < 0
    initial = np.full(n, 1 / n)
    result = generator.propagate(initial, 10.)
    assert result.min() >= 0
    assert result.sum() == pytest.approx(1., abs=1e-12)


def test_generator_matches_original_notebook_function():
    # Test-only extraction of one reviewed pure function, with explicit globals.
    # Production code never loads or executes notebook source.
    source = json.loads((ROOT / 'notebooks/reference/Hx_NdNiO3_single_cell_evidence_calibrated_PoC_v3_1.ipynb').read_text())
    tree = ast.parse(''.join(source['cells'][0]['source']))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'coupled_local_generator')
    model = TransportModel()
    st, cfg = model.structure, model.config
    ns = dict(np=np, CFG=SimpleNamespace(length_m=cfg.length_m), Q_A_TARGET_A=st.q_a_unit,
              Q_R_BULK_A=st.q_r_bulk_a, D_REP_M2_S=cfg.diffusivity_m2_s, EA_MODEL_EV=cfg.activation_ev,
              KB_EV_K=KB_EV_K, T_REF_K=300., E_A_RELAX_EV=st.e_a, E_R_RELAX_EV_FU=st.e_r,
              TRAP_FIT=SimpleNamespace(x=[0., cfg.chi_transport]))
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<reference generator>', 'exec'), ns)
    c = .3 + .12 * np.cos(2 * np.pi * (np.arange(32) + .5) / 32) + .05 * (-1.)**np.arange(32)
    original, qa, potential, qr, _ = ns['coupled_local_generator'](c, 300., 2e5, 0.)
    migrated = model.freeze(c)
    np.testing.assert_allclose(migrated.matrix.toarray(), original, rtol=3e-15, atol=1e-18)
    np.testing.assert_allclose(migrated.q_a, qa)
    np.testing.assert_allclose(migrated.potential_ev, potential)
    assert migrated.q_r == pytest.approx(qr)


def test_recoverability_is_diagnostic_only_and_reflection_invariant():
    c = np.linspace(.1, .5, 32)
    model = TransportModel()
    before = model.freeze(c).matrix.toarray()
    value = RecoverabilityDiagnostic.evaluate(c)
    assert value > 0
    assert RecoverabilityDiagnostic.evaluate(c[::-1]) == pytest.approx(value)
    assert np.mean(abs(c - c.mean())) <= np.sqrt(2 * value)
    for level in (0., .3, 1.):
        assert RecoverabilityDiagnostic.evaluate(np.full(32, level)) == pytest.approx(0.)
    np.testing.assert_array_equal(before, model.freeze(c).matrix.toarray())


def test_holdout_matches_paper(data, fit):
    model = RelaxationModel()
    pred = model.predict(fit.theta, data.time_s, 533.)
    metrics = experimental_metrics(data.observed[:, 3], pred)
    assert fit.training_indices == (0, 1, 2)
    assert metrics['RMSE'] == pytest.approx(.02633725, abs=2e-7)
    assert metrics['R2'] == pytest.approx(.9908062, abs=2e-7)
    assert fit.theta[1] * model.energy_scale == pytest.approx(6.52887, abs=2e-5)


def test_holdout_cannot_influence_fit(data, fit):
    modified = data.observed.copy()
    modified[:, 3] = 42.
    altered = replace(data, observed=modified)
    fresh = RelaxationModel().fit(altered)
    np.testing.assert_array_equal(fresh.theta, fit.theta)


def test_analytic_jacobian_against_finite_differences(data, fit):
    model = RelaxationModel()
    _, analytic = model.prediction_jacobian(fit.theta, data.time_s, data.fields_kv_cm[:3])
    numeric = approx_derivative(lambda th: model.residual(th, data), fit.theta, method='3-point')
    np.testing.assert_allclose(analytic, numeric, atol=1e-8, rtol=2e-5)


def test_mesh_parity_limitation_remains_visible():
    model = TransportModel()
    values = [model.freeze(RefinementStudy.background(n, 'ramp')).q_r for n in (16, 32, 64)]
    np.testing.assert_allclose(np.asarray(values[:-1]) / values[1:], 2., rtol=1e-12)
    assert model.freeze(RefinementStudy.background(32, 'ramp'), smooth_limit=True).q_r == 0
    alternating = [.3 + .05 * (-1.)**np.arange(n) for n in (16, 32, 64)]
    np.testing.assert_allclose([model.freeze(c).q_r for c in alternating], .01)


def test_transport_coefficient_is_independent_of_relaxation():
    result = TransportSensitivityStudy().run()
    table = result.tables['sensitivity']
    np.testing.assert_allclose(table.operator_change, table.operator_change_formula, atol=1e-13)
    assert np.all(np.diff(table.sort_values('chi').D_eff_m2_s) <= 0)


def test_continuum_order_and_bound():
    result = ContinuumStudy().run()
    assert result.metadata['observed_order'] == pytest.approx(2.029, abs=.002)
    assert result.metadata['entropy_derivative_s_1'] < 0
    assert result.tables['convergence'].gap_bound_ratio.min() >= 1


def test_presenter_renders_portable_outputs(tmp_path):
    outputs = PaperPresenter(ArtifactView(tmp_path)).run('hidden_state')
    assert len(outputs) == 1
    metadata = json.loads((outputs[0] / 'metadata.json').read_text())
    assert 'Synthetic' in metadata['scope']
    assert (outputs[0] / 'manifest.json').exists()
