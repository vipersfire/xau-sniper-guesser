#!/usr/bin/env python3
"""Initialize the PostgreSQL database schema."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main():
    from data.db import init_db
    print("Initializing database...")
    await init_db()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
