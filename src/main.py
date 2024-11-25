#!/usr/bin/env python3
# main.py

import asyncio

import uvicorn

from app import app


async def main() -> None:
    config = uvicorn.Config("main:app", port=8000, log_level="info", reload=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
