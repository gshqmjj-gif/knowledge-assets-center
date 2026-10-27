#!/usr/bin/env python3
"""
Hermes Knowledge Base Main Entrypoint
"""
import sys
from pathlib import Path

# 确保在路径中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli import app

if __name__ == "__main__":
    app()
