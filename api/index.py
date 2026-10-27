"""Entry point for Vercel.

Vercel looks for something in api/ to handle requests. All this does is find
the real app one directory up and hand it over - the site itself still lives
in app.py, which is also what runs locally.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

__all__ = ["app"]
