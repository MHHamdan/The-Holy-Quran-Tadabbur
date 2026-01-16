"""
Entry point for running ingestion as a module.

Usage:
    python -m app.ingest --steps all --dry-run
"""

from app.ingest.cli import main

if __name__ == "__main__":
    main()
