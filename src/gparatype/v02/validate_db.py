"""CLI: python -m gparatype.v02.validate_db [path]"""

from __future__ import annotations

import sys
from pathlib import Path

from gparatype.v02.database import default_database_path, validate_database


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    path = Path(args[0]) if args else default_database_path()
    errors = validate_database(path)
    if errors:
        print(f"FAIL {path}")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"OK {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
