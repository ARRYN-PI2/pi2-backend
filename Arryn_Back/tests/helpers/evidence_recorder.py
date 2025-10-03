"""Utilities to persist evidence collected during test execution."""
from __future__ import annotations

import atexit
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


_EVIDENCE: List[Dict[str, Any]] = []


def _serialize(obj: Any) -> Any:
    """Fallback serializer for non-standard JSON types."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def record_evidence(test_name: str, details: Dict[str, Any]) -> None:
    """Store evidence for later export.

    Args:
        test_name: Fully qualified name of the test collecting evidence.
        details: Arbitrary JSON-serializable dictionary with the evidence captured.
    """
    _EVIDENCE.append({
        "test": test_name,
        "details": details,
    })


def _dump_evidence() -> None:
    if not _EVIDENCE:
        return

    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "test_evidence.json"
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_records": len(_EVIDENCE),
        "records": _EVIDENCE,
    }

    output_path.write_text(json.dumps(payload, indent=2, default=_serialize), encoding="utf-8")


atexit.register(_dump_evidence)
