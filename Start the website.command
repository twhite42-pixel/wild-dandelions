#!/bin/bash
# Double-click this file in Finder to start the Wild Dandelions website.
cd "$(dirname "$0")" || exit 1
echo ""
echo "  Starting Wild Dandelions..."
echo "  Open your browser to:  http://localhost:5050"
echo "  Close this window when you are finished."
echo ""
exec ./.venv/bin/python app.py
