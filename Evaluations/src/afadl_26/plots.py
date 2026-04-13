from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

from .analysis import class_distribution_summary, three_rater_agreement_summary


def plot_class_distribution(
    aligned: dict,
    *,
    labels: Iterable[int] = (1, 2, 3, 4),
    normalize: bool = False,
    title: str = "Class distribution by rater",
    save_path: str | Path | None = None,
):
    labels = list(labels)
    summary = class_distribution_summary(aligned, labels=labels)
    rater_names = aligned["rater_names"]

    values = []
    for rater in rater_names:
        if normalize:
            values.append([summary["proportions"][rater][label] for label in labels])
        else:
            values.append([summary["counts"][rater][label] for label in labels])

    values = np.array(values)

    x = np.arange(len(labels))
    width = 0.8 / len(rater_names)

    fig, ax = plt.subplots(figsize=(8, 5))

    for i, rater in enumerate(rater_names):
        ax.bar(
            x + i * width - (len(rater_names) - 1) * width / 2,
            values[i],
            width=width,
            label=rater,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([str(label) for label in labels])
    ax.set_xlabel("Class")
    ax.set_ylabel("Proportion" if normalize else "Count")
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig, ax


def plot_unanimous_agreement_by_class(
    aligned: dict,
    *,
    human_1: str = "human_1",
    human_2: str = "human_2",
    llm: str = "llm_rater",
    labels: Iterable[int] = (1, 2, 3, 4),
    title: str = "All-3 agreement count by class",
    save_path: str | Path | None = None,
):
    labels = list(labels)
    summary = three_rater_agreement_summary(
        aligned,
        human_1=human_1,
        human_2=human_2,
        llm=llm,
        labels=labels,
    )

    counts = [summary["all_agree_by_class"].get(label, 0) for label in labels]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([str(label) for label in labels], counts)
    ax.set_xlabel("Class")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig, ax


def plot_agreement_patterns(
    aligned: dict,
    *,
    human_1: str = "human_1",
    human_2: str = "human_2",
    llm: str = "llm_rater",
    labels: Iterable[int] = (1, 2, 3, 4),
    title: str = "Three-rater agreement patterns",
    save_path: str | Path | None = None,
):
    summary = three_rater_agreement_summary(
        aligned,
        human_1=human_1,
        human_2=human_2,
        llm=llm,
        labels=labels,
    )

    categories = [
        "all_agree",
        "human_1=human_2!=llm",
        "human_1=llm!=human_2",
        "human_2=llm!=human_1",
        "all_different",
    ]
    counts = [summary["pattern_counts"].get(cat, 0) for cat in categories]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(range(len(categories)), counts)
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=20, ha="right")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig, ax