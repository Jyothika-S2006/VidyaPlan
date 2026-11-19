#!/bin/bash
set -e

echo "VidyaPlan: initialising database..."
cd /app/backend
python -m app.db.migrate 2>/dev/null || python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from app.db.session import init_db
asyncio.run(init_db())
print('DB initialised')
"

echo "VidyaPlan: loading data (idempotent)..."
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from app.db.session import AsyncSessionLocal, init_db
from app.pipeline.load import load_data
async def main():
    await init_db()
    async with AsyncSessionLocal() as s:
        r = await load_data(s)
        print(f'Data loaded: {r}')
asyncio.run(main())
" || echo "Data load skipped (no CSV or already loaded)"

echo "VidyaPlan: starting server..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
