import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT / 'frontend' / 'dist'
TARGET = ROOT / 'app' / 'web' / 'dist'

if not FRONTEND_DIST.exists():
  print("frontend/dist not found. Run `npm --prefix frontend run build` first.", file=sys.stderr)
  sys.exit(2)

TARGET.parent.mkdir(parents=True, exist_ok=True)

if TARGET.exists():
  shutil.rmtree(TARGET)

shutil.copytree(FRONTEND_DIST, TARGET)
print(f"Copied {FRONTEND_DIST} -> {TARGET}")
