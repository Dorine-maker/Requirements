from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class AnnotationKey:
    model: str
    specification: int
    trial: str


@dataclass(frozen=True)
class AnnotationRecord:
    key: AnnotationKey
    cls: int