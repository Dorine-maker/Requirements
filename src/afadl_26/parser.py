from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

from .models import AnnotationKey, AnnotationRecord

MODEL_CANONICAL = {
    "gpt": "GPT",
    "claude": "Claude",
    "deepseek": "DeepSeek",
    "mistral": "Mistral",
    "qwen": "Qwen",
}

HEADER_ALIASES = {
    "model": {"model", "model_name", "Model"},
    "specification": {
        "specification",
        "specification_number",
        "spec",
        "spec_number",
        "Specification Number",
    },
    "trial": {"trial", "trial_number", "Requirement Number"},
    "class": {"class", "label", "rating", "category", "Class"},
}

TRIAL_RE = re.compile(r"^T([1-9]|10)$", re.IGNORECASE)


def _canonicalize_header(name: str) -> str:
    normalized = name.strip().lower().replace(" ", "_")
    for canonical, aliases in HEADER_ALIASES.items():
        if normalized in aliases:
            return canonical
    return normalized


def _normalize_model(value: str, validate: bool, line_number: int) -> str:
    model = value.strip()
    if validate:
        key = model.casefold()
        if key not in MODEL_CANONICAL:
            raise ValueError(
                f"Invalid model '{value}' at line {line_number}. "
                f"Expected one of: {sorted(MODEL_CANONICAL.values())}"
            )
        model = MODEL_CANONICAL[key]
    return model


def _normalize_specification(value: str, validate: bool, line_number: int) -> int:
    try:
        spec = int(value.strip())
    except ValueError as exc:
        raise ValueError(
            f"Invalid specification '{value}' at line {line_number}. "
            f"Expected an integer."
        ) from exc

    if validate and not (1 <= spec <= 8):
        raise ValueError(
            f"Invalid specification '{spec}' at line {line_number}. "
            f"Expected a value between 1 and 8."
        )
    return spec


def _normalize_trial(value: str, validate: bool, line_number: int) -> str:
    trial = value.strip().upper()
    if trial.isdigit():
        trial = f"T{trial}"

    if validate and not TRIAL_RE.fullmatch(trial):
        raise ValueError(
            f"Invalid trial '{value}' at line {line_number}. "
            f"Expected T1 to T10."
        )
    return trial


def _normalize_class(value: str, validate: bool, line_number: int) -> int:
    try:
        cls = int(value.strip())
    except ValueError as exc:
        raise ValueError(
            f"Invalid class '{value}' at line {line_number}. "
            f"Expected an integer."
        ) from exc

    if validate and cls not in {1, 2, 3, 4}:
        raise ValueError(
            f"Invalid class '{cls}' at line {line_number}. "
            f"Expected one of 1, 2, 3, 4."
        )
    return cls


def _make_record(
    model_value: str,
    spec_value: str,
    trial_value: str,
    class_value: str,
    validate: bool,
    line_number: int,
) -> AnnotationRecord:
    model = _normalize_model(model_value, validate, line_number)
    specification = _normalize_specification(spec_value, validate, line_number)
    trial = _normalize_trial(trial_value, validate, line_number)
    cls = _normalize_class(class_value, validate, line_number)

    return AnnotationRecord(
        key=AnnotationKey(model=model, specification=specification, trial=trial),
        cls=cls,
    )


def parse_annotation_csv(
    path: str | Path,
    delimiter: str = ";",
    has_header: bool = True,
    validate: bool = True,
) -> list[AnnotationRecord]:
    path = Path(path)
    records: list[AnnotationRecord] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        if has_header:
            reader = csv.DictReader(f, delimiter=delimiter)

            if not reader.fieldnames:
                raise ValueError(f"No header found in file: {path}")

            field_map: dict[str, str] = {}
            for field in reader.fieldnames:
                if field is None:
                    continue
                canonical = _canonicalize_header(field)
                field_map[canonical] = field

            required = ("model", "specification", "trial", "class")
            missing = [name for name in required if name not in field_map]
            if missing:
                raise ValueError(
                    f"Missing required columns {missing} in file {path}. "
                    f"Found columns: {reader.fieldnames}"
                )

            for line_number, row in enumerate(reader, start=2):
                if not row or all(
                    value is None or str(value).strip() == ""
                    for value in row.values()
                ):
                    continue

                record = _make_record(
                    model_value=row[field_map["model"]],
                    spec_value=row[field_map["specification"]],
                    trial_value=row[field_map["trial"]],
                    class_value=row[field_map["class"]],
                    validate=validate,
                    line_number=line_number,
                )
                records.append(record)

        else:
            reader = csv.reader(f, delimiter=delimiter)
            for line_number, row in enumerate(reader, start=1):
                if not row or all(str(value).strip() == "" for value in row):
                    continue

                if len(row) < 4:
                    raise ValueError(
                        f"Line {line_number} in {path} has fewer than 4 columns: {row}"
                    )

                record = _make_record(
                    model_value=row[0],
                    spec_value=row[1],
                    trial_value=row[2],
                    class_value=row[3],
                    validate=validate,
                    line_number=line_number,
                )
                records.append(record)

    return records


def records_to_class_map(
    records: Iterable[AnnotationRecord],
) -> dict[AnnotationKey, int]:
    mapping: dict[AnnotationKey, int] = {}

    for record in records:
        if record.key in mapping:
            raise ValueError(f"Duplicate annotation key found: {record.key}")
        mapping[record.key] = record.cls

    return mapping