"""Offline experimental data and provenance from the supplied v3.1 notebook."""

from dataclasses import dataclass
from importlib.resources import files
import hashlib
import json

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class PolarizationDataset:
    """Published field-relaxation traces with an explicit calibration boundary.

    Attributes:
        time_s: The 87 experimental observation times, in seconds.
        fields_kv_cm: Applied fields in kV/cm: 133, 267, 400, and 533.
        observed: Normalized polarization, with shape ``(87, 4)``.
        source_matrix: Unmodified 87 by 12 publisher matrix embedded in v3.1.
        provenance: Source DOI, workbook hash, matrix hash, and notebook hashes.

    Notes:
        Columns 0--2 are the primary calibration set. Column 3 is the strict
        external holdout. Retrospective field folds must be labelled separately.
        The workbook hash is inherited provenance, not a claim that the original
        workbook is bundled or was downloaded again.
    """

    time_s: NDArray[np.float64]
    fields_kv_cm: NDArray[np.float64]
    observed: NDArray[np.float64]
    source_matrix: NDArray[np.float64]
    provenance: dict

    @classmethod
    def load(cls) -> 'PolarizationDataset':
        """Load package resources and verify the embedded matrix integrity.

        Returns:
            Dataset with the exact normalization and clipping used in v3.1.

        Raises:
            ValueError: If the matrix shape or its little-endian float64 hash
                differs from the supplied notebook's embedded data.
        """
        root = files('octa_gtrqc_sim.proton').joinpath('data')
        matrix = np.asarray(json.loads(root.joinpath('fig2h.json').read_text()), dtype='<f8')
        digest = hashlib.sha256(matrix.tobytes()).hexdigest()
        expected = '859f76869eb087bc05e0aba24f3543bddb90b03842d10bb49d0dc66d1814354a'
        if matrix.shape != (87, 12) or digest != expected:
            raise ValueError('Embedded experimental matrix failed its integrity check.')
        observed = np.column_stack((matrix[:, 10] / matrix[0, 10], matrix[:, 9],
                                    matrix[:, 6], matrix[:, 3]))
        provenance = json.loads(root.joinpath('provenance.json').read_text())
        provenance['embedded_matrix_sha256'] = digest
        return cls(matrix[:, 0] * 1e-3, np.array([133., 267., 400., 533.]),
                   np.clip(observed, 0., 1.2), matrix, provenance)
