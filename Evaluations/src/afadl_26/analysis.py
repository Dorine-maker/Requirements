from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Iterable

import numpy as np

from .kappa import cohen_kappa
from .parser import parse_annotation_csv, records_to_class_map


def _key_to_tuple(key) -> tuple[str, int, str]:
    return (key.model, key.specification, key.trial)


def align_raters(
    rater_files: dict[str, str | Path],
    *,
    delimiter: str = ";",
    has_header: bool = True,
    validate: bool = True,
    strict: bool = False,
) -> dict:
    """
    Load several rater CSV files and align them on common keys:
    (model, specification, trial).

    Returns a dict with:
      - rows: list of aligned records
      - rater_names
      - common_keys
      - missing_by_rater
    """
    if len(rater_files) < 2:
        raise ValueError("At least two raters are required.")

    class_maps = {}

    for rater_name, path in rater_files.items():
        records = parse_annotation_csv(
            path=path,
            delimiter=delimiter,
            has_header=has_header,
            validate=validate,
        )
        class_maps[rater_name] = records_to_class_map(records)

    key_sets = {name: set(mapping.keys()) for name, mapping in class_maps.items()}
    common_keys = set.intersection(*(keys for keys in key_sets.values()))

    if not common_keys:
        raise ValueError("No common annotation keys across the provided raters.")

    missing_by_rater = {}
    all_keys = set.union(*(keys for keys in key_sets.values()))
    for name, keys in key_sets.items():
        missing_by_rater[name] = sorted(all_keys - keys)

    if strict:
        any_missing = any(missing_by_rater[name] for name in missing_by_rater)
        if any_missing:
            parts = []
            for name, missing in missing_by_rater.items():
                if missing:
                    parts.append(f"{name} missing: {[_key_to_tuple(k) for k in missing]}")
            raise ValueError("Raters do not have identical item sets.\n" + "\n".join(parts))

    rows = []
    for key in sorted(common_keys):
        row = {
            "model": key.model,
            "specification": key.specification,
            "trial": key.trial,
        }
        for rater_name, mapping in class_maps.items():
            row[rater_name] = mapping[key]
        rows.append(row)

    return {
        "rater_names": list(rater_files.keys()),
        "rows": rows,
        "common_keys": sorted(common_keys),
        "n_common": len(common_keys),
        "missing_by_rater": {
            name: [_key_to_tuple(k) for k in missing]
            for name, missing in missing_by_rater.items()
        },
    }


def pairwise_kappas(
    aligned: dict,
    *,
    labels: Iterable[int] = (1, 2, 3, 4),
    weight_scheme: str = "unweighted",
    weight_matrix: np.ndarray | None = None,
) -> dict:
    """
    Compute pairwise Cohen's kappas for all pairs of raters.
    """
    rater_names = aligned["rater_names"]
    rows = aligned["rows"]

    results = {}
    for a, b in combinations(rater_names, 2):
        ratings_a = [row[a] for row in rows]
        ratings_b = [row[b] for row in rows]

        metric = cohen_kappa(
            rater_a=ratings_a,
            rater_b=ratings_b,
            labels=labels,
            weight_scheme=weight_scheme,
            weight_matrix=weight_matrix,
        )
        results[(a, b)] = metric

    return results

def class_distribution_summary(
    aligned: dict,
    *,
    labels: Iterable[int] = (1, 2, 3, 4),
) -> dict:
    """
    Count how many times each rater used each class.
    """
    labels = list(labels)
    rows = aligned["rows"]
    rater_names = aligned["rater_names"]

    counts = {}
    proportions = {}

    for rater in rater_names:
        c = Counter(row[rater] for row in rows)
        counts[rater] = {label: c.get(label, 0) for label in labels}
        total = len(rows)
        proportions[rater] = {
            label: (counts[rater][label] / total if total else 0.0)
            for label in labels
        }

    return {
        "counts": counts,
        "proportions": proportions,
        "n_items": len(rows),
    }


def three_rater_agreement_summary(
    aligned: dict,
    *,
    human_1: str = "human_1",
    human_2: str = "human_2",
    llm: str = "llm_rater",
    labels: Iterable[int] = (1, 2, 3, 4),
) -> dict:
    """
    Detailed agreement summary for exactly 3 raters.
    """
    rows = aligned["rows"]
    labels = list(labels)

    all_agree_count = 0
    all_agree_by_class = Counter()

    exactly_two_agree_count = 0
    all_different_count = 0

    pattern_counts = Counter()

    llm_matches_h1 = 0
    llm_matches_h2 = 0
    humans_agree_count = 0
    humans_agree_llm_matches = 0
    humans_agree_llm_disagrees = 0

    humans_disagree_count = 0
    humans_disagree_llm_sides_h1 = 0
    humans_disagree_llm_sides_h2 = 0
    humans_disagree_llm_sides_neither = 0

    for row in rows:
        h1 = row[human_1]
        h2 = row[human_2]
        l = row[llm]

        if l == h1:
            llm_matches_h1 += 1
        if l == h2:
            llm_matches_h2 += 1

        if h1 == h2 == l:
            all_agree_count += 1
            all_agree_by_class[h1] += 1
            pattern_counts["all_agree"] += 1

        elif h1 == h2 != l:
            exactly_two_agree_count += 1
            humans_agree_count += 1
            humans_agree_llm_disagrees += 1
            pattern_counts["human_1=human_2!=llm"] += 1

        elif h1 == l != h2:
            exactly_two_agree_count += 1
            humans_disagree_count += 1
            humans_disagree_llm_sides_h1 += 1
            pattern_counts["human_1=llm!=human_2"] += 1

        elif h2 == l != h1:
            exactly_two_agree_count += 1
            humans_disagree_count += 1
            humans_disagree_llm_sides_h2 += 1
            pattern_counts["human_2=llm!=human_1"] += 1

        else:
            all_different_count += 1
            humans_disagree_count += 1
            humans_disagree_llm_sides_neither += 1
            pattern_counts["all_different"] += 1

        if h1 == h2:
            humans_agree_count += 0 if h1 == h2 == l else 1
            if l == h1:
                humans_agree_llm_matches += 1

    # Need a correct count of human agreement overall:
    human_human_agree_total = sum(1 for row in rows if row[human_1] == row[human_2])
    human_human_disagree_total = len(rows) - human_human_agree_total

    # Among human-agree cases:
    human_agree_llm_matches_total = sum(
        1
        for row in rows
        if row[human_1] == row[human_2] == row[llm]
    )
    human_agree_llm_disagrees_total = sum(
        1
        for row in rows
        if row[human_1] == row[human_2] and row[llm] != row[human_1]
    )

    # Among human-disagree cases:
    human_disagree_llm_sides_h1_total = sum(
        1
        for row in rows
        if row[human_1] != row[human_2] and row[llm] == row[human_1]
    )
    human_disagree_llm_sides_h2_total = sum(
        1
        for row in rows
        if row[human_1] != row[human_2] and row[llm] == row[human_2]
    )
    human_disagree_llm_sides_neither_total = sum(
        1
        for row in rows
        if row[human_1] != row[human_2]
        and row[llm] != row[human_1]
        and row[llm] != row[human_2]
    )

    total = len(rows)

    return {
        "n_items": total,
        "all_agree_count": all_agree_count,
        "all_agree_rate": all_agree_count / total if total else 0.0,
        "all_agree_by_class": {label: all_agree_by_class.get(label, 0) for label in labels},
        "exactly_two_agree_count": exactly_two_agree_count,
        "exactly_two_agree_rate": exactly_two_agree_count / total if total else 0.0,
        "all_different_count": all_different_count,
        "all_different_rate": all_different_count / total if total else 0.0,
        "pattern_counts": dict(pattern_counts),
        "llm_matches_h1_count": llm_matches_h1,
        "llm_matches_h2_count": llm_matches_h2,
        "llm_matches_h1_rate": llm_matches_h1 / total if total else 0.0,
        "llm_matches_h2_rate": llm_matches_h2 / total if total else 0.0,
        "human_human_agree_total": human_human_agree_total,
        "human_human_disagree_total": human_human_disagree_total,
        "human_agree_llm_matches_total": human_agree_llm_matches_total,
        "human_agree_llm_disagrees_total": human_agree_llm_disagrees_total,
        "human_disagree_llm_sides_h1_total": human_disagree_llm_sides_h1_total,
        "human_disagree_llm_sides_h2_total": human_disagree_llm_sides_h2_total,
        "human_disagree_llm_sides_neither_total": human_disagree_llm_sides_neither_total,
    }


def group_summary_by_field(
    aligned: dict,
    field: str,
    *,
    human_1: str = "human_1",
    human_2: str = "human_2",
    llm: str = "llm_rater",
    labels: Iterable[int] = (1, 2, 3, 4),
) -> dict:
    """
    Compute three-rater agreement summaries grouped by one field,
    e.g. field='model' or field='specification'.
    """
    rows = aligned["rows"]
    groups = defaultdict(list)

    for row in rows:
        groups[row[field]].append(row)

    out = {}
    for group_value, group_rows in groups.items():
        sub_aligned = {
            "rater_names": aligned["rater_names"],
            "rows": group_rows,
        }
        out[group_value] = three_rater_agreement_summary(
            sub_aligned,
            human_1=human_1,
            human_2=human_2,
            llm=llm,
            labels=labels,
        )

    return out