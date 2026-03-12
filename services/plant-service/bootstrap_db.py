"""
Idempotent DB bootstrap for plant-service:
- Adds new columns to existing tables (ALTER TABLE ADD COLUMN IF NOT EXISTS)
- Creates all new tables via SQLAlchemy metadata (idempotent)
"""

import asyncio
import os
import re


async def main():
    import asyncpg

    db_url = os.environ.get("DATABASE_URL", "")
    m = re.match(
        r"postgresql\+asyncpg://(?P<user>[^:]+):(?P<pw>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<db>.+)",
        db_url,
    )
    if not m:
        print(f"Cannot parse DATABASE_URL ({db_url!r}), skipping bootstrap.")
        return

    conn = await asyncpg.connect(
        user=m.group("user"),
        password=m.group("pw"),
        host=m.group("host"),
        port=int(m.group("port")),
        database=m.group("db"),
    )

    try:
        print("Running plant-service DB bootstrap...")

        # -- Add new columns to plants --
        plant_alters = [
            "ALTER TABLE plants ADD COLUMN IF NOT EXISTS properties JSONB NOT NULL DEFAULT '[]'",
            "ALTER TABLE plants ADD COLUMN IF NOT EXISTS image_url TEXT",
            "ALTER TABLE plants ADD COLUMN IF NOT EXISTS identifying_features JSONB NOT NULL DEFAULT '[]'",
            "ALTER TABLE plants ADD COLUMN IF NOT EXISTS region VARCHAR(255)",
            "ALTER TABLE plants ADD COLUMN IF NOT EXISTS category VARCHAR(128)",
        ]
        for stmt in plant_alters:
            await conn.execute(stmt)
            print(f"  {stmt[:60]}...")

        # -- Add new columns to chemical_compounds --
        compound_alters = [
            "ALTER TABLE chemical_compounds ADD COLUMN IF NOT EXISTS inchi TEXT",
            "ALTER TABLE chemical_compounds ADD COLUMN IF NOT EXISTS properties JSONB NOT NULL DEFAULT '[]'",
        ]
        for stmt in compound_alters:
            await conn.execute(stmt)
            print(f"  {stmt[:60]}...")

        # -- Add new columns to scientific_articles --
        article_alters = [
            "ALTER TABLE scientific_articles ADD COLUMN IF NOT EXISTS country VARCHAR(100)",
        ]
        for stmt in article_alters:
            await conn.execute(stmt)
            print(f"  {stmt[:60]}...")

        # -- Create new tables via SQLAlchemy --
        print("Creating new tables via SQLAlchemy metadata...")
        from sqlalchemy.ext.asyncio import create_async_engine
        from src.models import Base

        engine = create_async_engine(db_url, echo=False)
        async with engine.begin() as sa_conn:
            await sa_conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

        print("Plant-service DB bootstrap complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
