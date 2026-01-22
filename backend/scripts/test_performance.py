#!/usr/bin/env python3
"""
Performance Testing Script
Tests the gateway performance improvements
"""
import asyncio
import httpx
import time
import statistics
from typing import List, Tuple


async def test_request(client: httpx.AsyncClient, api_key: str, base_url: str) -> Tuple[float, int]:
    """Make a single test request and return latency and status code."""
    start = time.time()
    try:
        response = await client.post(
            f"{base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Say 'hello' in one word"}],
                "max_tokens": 5
            },
            timeout=30.0
        )
        latency = (time.time() - start) * 1000  # Convert to ms
        return latency, response.status_code
    except Exception as e:
        print(f"Request failed: {e}")
        return 0, 0


async def load_test(api_key: str, base_url: str = "http://localhost:8000", num_requests: int = 50):
    """Run load test with specified number of requests."""
    print(f"\n🚀 Starting performance test with {num_requests} requests...\n")
    
    async with httpx.AsyncClient() as client:
        # Warmup request
        print("Warming up...")
        await test_request(client, api_key, base_url)
        await asyncio.sleep(1)
        
        # Run test requests
        print(f"Running {num_requests} concurrent requests...\n")
        start_time = time.time()
        
        tasks = [test_request(client, api_key, base_url) for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Filter successful requests
        latencies = [r[0] for r in results if r[1] == 200]
        failed = len([r for r in results if r[1] != 200])
        
        if not latencies:
            print("❌ All requests failed!")
            return
        
        # Calculate statistics
        latencies.sort()
        
        print("=" * 60)
        print("📊 PERFORMANCE RESULTS")
        print("=" * 60)
        print(f"Total Requests:       {num_requests}")
        print(f"Successful:           {len(latencies)}")
        print(f"Failed:               {failed}")
        print(f"Total Time:           {total_time:.2f}s")
        print(f"Throughput:           {num_requests / total_time:.2f} req/s")
        print()
        print("LATENCY DISTRIBUTION:")
        print(f"  Min:                {min(latencies):.2f}ms")
        print(f"  P25:                {latencies[len(latencies)//4]:.2f}ms")
        print(f"  P50 (Median):       {latencies[len(latencies)//2]:.2f}ms")
        print(f"  P75:                {latencies[int(len(latencies)*0.75)]:.2f}ms")
        print(f"  P90:                {latencies[int(len(latencies)*0.90)]:.2f}ms")
        print(f"  P95:                {latencies[int(len(latencies)*0.95)]:.2f}ms")
        print(f"  P99:                {latencies[int(len(latencies)*0.99)]:.2f}ms")
        print(f"  Max:                {max(latencies):.2f}ms")
        print(f"  Average:            {statistics.mean(latencies):.2f}ms")
        print("=" * 60)
        
        # Performance evaluation
        p99 = latencies[int(len(latencies)*0.99)]
        print("\n🎯 PERFORMANCE EVALUATION:")
        if p99 < 15:
            print("✅ EXCELLENT: P99 < 15ms (Target achieved!)")
        elif p99 < 50:
            print("✅ GOOD: P99 < 50ms")
        elif p99 < 100:
            print("⚠️  ACCEPTABLE: P99 < 100ms (Room for improvement)")
        else:
            print("❌ NEEDS OPTIMIZATION: P99 > 100ms")
        print()


async def test_cache_performance(api_key: str, base_url: str = "http://localhost:8000"):
    """Test API key cache performance."""
    print("\n🔍 Testing API Key Cache Performance...\n")
    
    async with httpx.AsyncClient() as client:
        # First request (cache miss)
        print("Making first request (cache miss)...")
        latency1, status1 = await test_request(client, api_key, base_url)
        
        # Second request (should hit cache)
        print("Making second request (cache hit)...")
        latency2, status2 = await test_request(client, api_key, base_url)
        
        # Third request (cache hit)
        print("Making third request (cache hit)...\n")
        latency3, status3 = await test_request(client, api_key, base_url)
        
        if all(s == 200 for s in [status1, status2, status3]):
            print("=" * 60)
            print("CACHE PERFORMANCE:")
            print(f"  Request 1 (miss):   {latency1:.2f}ms")
            print(f"  Request 2 (hit):    {latency2:.2f}ms")
            print(f"  Request 3 (hit):    {latency3:.2f}ms")
            
            if latency2 < latency1 * 0.8:
                print("\n✅ Cache is working! Requests 2-3 are faster")
            else:
                print("\n⚠️  Cache may not be enabled or effective")
            print("=" * 60)
        else:
            print("❌ Some requests failed, cache test inconclusive")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_performance.py <API_KEY> [BASE_URL] [NUM_REQUESTS]")
        print("Example: python test_performance.py sk-gw-abc123 http://localhost:8000 50")
        sys.exit(1)
    
    api_key = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    num_requests = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    
    # Run tests
    asyncio.run(test_cache_performance(api_key, base_url))
    asyncio.run(load_test(api_key, base_url, num_requests))
