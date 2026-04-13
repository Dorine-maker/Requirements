from __future__ import annotations

from typing import Iterable

import numpy as np


def build_weight_matrix(
    labels: Iterable[int],
    scheme: str = "unweighted",
) -> np.ndarray:
    labels = list(labels)
    k = len(labels)

    if k == 0:
        raise ValueError("labels must not be empty")

    weights = np.zeros((k, k), dtype=float)

    if k == 1:
        return weights

    scheme = scheme.lower()

    for i in range(k):
        for j in range(k):
            if i == j:
                weights[i, j] = 0.0
            elif scheme == "unweighted":
                weights[i, j] = 1.0
            elif scheme == "linear":
                weights[i, j] = abs(i - j) / (k - 1)
            elif scheme == "quadratic":
                weights[i, j] = ((i - j) / (k - 1)) ** 2
            else:
                raise ValueError(
                    "Unknown weight scheme. Use one of: "
                    "'unweighted', 'linear', 'quadratic'."
                )

    return weights


def make_pair_weight_matrix(
    labels: Iterable[int],
    penalties: dict[tuple[int, int], float],
    default_penalty: float = 1.0,
) -> np.ndarray:
    """
    Create a custom disagreement matrix.

    Diagonal is always 0.
    All off-diagonal cells start at default_penalty.
    Then penalties like {(1, 2): 0.25, (1, 4): 1.0} are applied symmetrically.
    """
    labels = list(labels)
    index = {label: i for i, label in enumerate(labels)}
    k = len(labels)

    weights = np.full((k, k), float(default_penalty), dtype=float)
    np.fill_diagonal(weights, 0.0)

    for (a, b), penalty in penalties.items():
        if a not in index or b not in index:
            raise ValueError(
                f"Penalty key ({a}, {b}) contains labels not present in {labels}"
            )
        i = index[a]
        j = index[b]
        weights[i, j] = float(penalty)
        weights[j, i] = float(penalty)

    return weights


def cohen_kappa(
    rater_a: Iterable[int],
    rater_b: Iterable[int],
    labels: Iterable[int] | None = None,
    weight_scheme: str = "unweighted",
    weight_matrix: np.ndarray | None = None,
) -> dict:
    a = list(rater_a)
    b = list(rater_b)

    if len(a) != len(b):
        raise ValueError("Both raters must have the same number of items.")

    if len(a) == 0:
        raise ValueError("Cannot compute kappa on empty inputs.")

    if labels is None:
        labels = sorted(set(a) | set(b))
    else:
        labels = list(labels)

    index = {label: i for i, label in enumerate(labels)}
    k = len(labels)

    observed = np.zeros((k, k), dtype=float)

    for x, y in zip(a, b):
        if x not in index:
            raise ValueError(f"Label '{x}' from rater_a not present in labels={labels}")
        if y not in index:
            raise ValueError(f"Label '{y}' from rater_b not present in labels={labels}")
        observed[index[x], index[y]] += 1.0

    n = observed.sum()
    row_marginals = observed.sum(axis=1)
    col_marginals = observed.sum(axis=0)
    expected = np.outer(row_marginals, col_marginals) / n

    if weight_matrix is None:
        weights = build_weight_matrix(labels=labels, scheme=weight_scheme)
    else:
        weights = np.asarray(weight_matrix, dtype=float)
        if weights.shape != (k, k):
            raise ValueError(
                f"weight_matrix must have shape {(k, k)}, got {weights.shape}"
            )

    if np.any(weights < 0):
        raise ValueError("Weights must be non-negative.")
    if not np.allclose(np.diag(weights), 0.0):
        raise ValueError("The diagonal of the weight matrix must be 0.")
    if not np.allclose(weights, weights.T):
        raise ValueError("The weight matrix must be symmetric.")

    observed_disagreement = float((weights * observed).sum())
    expected_disagreement = float((weights * expected).sum())

    if np.isclose(expected_disagreement, 0.0):
        kappa_value = 1.0 if np.isclose(observed_disagreement, 0.0) else 0.0
    else:
        kappa_value = 1.0 - (observed_disagreement / expected_disagreement)

    return {
        "kappa": float(kappa_value),
        "labels": labels,
        "n_items": int(n),
        "confusion_matrix": observed.astype(int),
        "expected_matrix": expected,
        "weight_matrix": weights,
    }