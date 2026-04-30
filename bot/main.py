#!/usr/bin/env python3
"""
Main entry point for Vera Bot.
Run with: python -m uvicorn main:app --host 0.0.0.0 --port 8080
"""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
