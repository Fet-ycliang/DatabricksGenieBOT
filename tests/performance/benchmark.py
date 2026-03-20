"""
Performance Benchmark Script
"""
import time
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.services.genie import GenieService
from app.core.config import DefaultConfig

async def run_benchmark():
    config = DefaultConfig()
    try:
        service = GenieService(config)
        print("Starting benchmark...")
        start = time.time()
        # Simulate workload
        await asyncio.sleep(1)
        end = time.time()
        print(f"Benchmark finished in {end - start:.2f}s")
    except Exception as e:
        print(f"Benchmark failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
