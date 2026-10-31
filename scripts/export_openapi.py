"""Write the API schema the frontend's types are generated from: python scripts/export_openapi.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.api import create_app  # noqa: E402
from app.store import Store  # noqa: E402

if __name__ == "__main__":
    schema = create_app(Store(":memory:"), None).openapi()
    (ROOT / "web" / "openapi.json").write_text(json.dumps(schema, indent=2) + "\n")
