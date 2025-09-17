"""Copy the built frontend into the FastAPI static directory."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> None:
    src = Path("frontend/dist")
    dest = Path("app/web/dist")

    if not src.exists():
        print("frontend/dist not found. Run `npm --prefix frontend run build` first.", file=sys.stderr)
        raise SystemExit(2)

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(src, dest)
    print(f"Copied {src} -> {dest}")


if __name__ == "__main__":
    main()
