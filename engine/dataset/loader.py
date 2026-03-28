"""Load and validate instruction-style datasets for LoRA / future QLoRA pipelines."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


class DatasetValidationError(ValueError):
    pass


def _read_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8", errors="replace")
    return json.loads(text)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _read_txt(path: Path) -> list[dict[str, str]]:
    """Each non-empty line: ``prompt<TAB>response`` or ``prompt|response``."""
    out: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        if "\t" in line:
            p, _, r = line.partition("\t")
        elif "|" in line:
            p, _, r = line.partition("|")
        else:
            raise DatasetValidationError(
                f"TXT rows must be 'prompt<TAB>response' or 'prompt|response': {path}",
            )
        out.append({"prompt": p.strip(), "response": r.strip()})
    return out


def load_dataset(path: Path) -> list[dict[str, str]]:
    """Load records with ``prompt`` and ``response`` keys from json, jsonl, or txt."""
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(str(path))
    suffix = path.suffix.lower()
    if path.is_dir():
        # prefer single file inside
        for name in ("train.jsonl", "data.jsonl", "train.json", "data.json"):
            cand = path / name
            if cand.is_file():
                return load_dataset(cand)
        raise DatasetValidationError(f"No supported data file found in directory: {path}")

    if suffix == ".json":
        raw = _read_json(path)
        if isinstance(raw, dict):
            records = [raw]
        elif isinstance(raw, list):
            records = raw
        else:
            raise DatasetValidationError("JSON root must be object or array")
    elif suffix == ".jsonl":
        records = _read_jsonl(path)
    elif suffix == ".txt":
        records = _read_txt(path)
    else:
        raise DatasetValidationError(f"Unsupported dataset format: {suffix}")

    out: list[dict[str, str]] = []
    for i, row in enumerate(records):
        if not isinstance(row, dict):
            raise DatasetValidationError(f"Row {i} is not an object")
        p = row.get("prompt")
        r = row.get("response")
        if not isinstance(p, str) or not isinstance(r, str):
            raise DatasetValidationError(f"Row {i} must have string prompt and response")
        out.append({"prompt": p, "response": r})
    return out


def validate_dataset(records: list[dict[str, str]]) -> None:
    if not records:
        raise DatasetValidationError("Dataset is empty")
    for i, row in enumerate(records):
        if "prompt" not in row or "response" not in row:
            raise DatasetValidationError(f"Row {i} missing prompt/response")
        if not row["prompt"].strip() and not row["response"].strip():
            raise DatasetValidationError(f"Row {i} is empty")


def split_dataset(
    records: list[dict[str, str]],
    *,
    val_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    validate_dataset(records)
    r = max(0.0, min(0.5, float(val_ratio)))
    if r == 0.0:
        return records, []
    rng = random.Random(seed)
    idx = list(range(len(records)))
    rng.shuffle(idx)
    n_val = max(1, int(len(records) * r))
    val_idx = set(idx[:n_val])
    train = [records[i] for i in range(len(records)) if i not in val_idx]
    val = [records[i] for i in range(len(records)) if i in val_idx]
    return train, val
