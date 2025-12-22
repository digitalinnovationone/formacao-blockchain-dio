"""
Debug script to inspect Polymarket API response
Run: python debug_api.py
"""

import httpx
import json

def main():
    client = httpx.Client(timeout=30)

    print("=" * 60)
    print("POLYMARKET API DEBUG")
    print("=" * 60)

    # Test 1: Get recent markets and show structure
    print("\n1. Fetching sample markets...")
    try:
        response = client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 10, "closed": "true"}
        )
        response.raise_for_status()
        data = response.json()

        markets = data if isinstance(data, list) else data.get("data", [])

        if markets:
            print(f"   Got {len(markets)} markets")
            sample = markets[0]
            print(f"\n   Sample market keys: {list(sample.keys())}")
            print(f"\n   Sample question: {sample.get('question', 'N/A')[:100]}")
            print(f"   Sample slug: {sample.get('slug', 'N/A')}")
            print(f"   Sample tags: {sample.get('tags', 'N/A')}")

            # Check for SOL keywords in any market
            print("\n   Checking for SOL-related markets...")
            for m in markets:
                q = (m.get("question") or "").lower()
                s = (m.get("slug") or "").lower()
                if "sol" in q or "sol" in s or "solana" in q:
                    print(f"   FOUND: {m.get('question', 'N/A')[:80]}")
                    print(f"          slug: {m.get('slug', 'N/A')}")
        else:
            print("   No markets returned")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Try searching with different params
    print("\n2. Trying different search strategies...")

    search_tests = [
        {"slug_contains": "sol", "limit": 5},
        {"slug_contains": "updown", "limit": 5},
        {"tag": "crypto", "limit": 5},
        {"active": "true", "limit": 5},
        {"limit": 5},  # No filter
    ]

    for params in search_tests:
        try:
            response = client.get(
                "https://gamma-api.polymarket.com/markets",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            markets = data if isinstance(data, list) else data.get("data", [])

            sol_count = 0
            for m in markets:
                q = (m.get("question") or "").lower()
                s = (m.get("slug") or "").lower()
                if "sol" in q or "sol" in s or "solana" in q:
                    sol_count += 1

            print(f"   {params} -> {len(markets)} markets, {sol_count} SOL-related")

        except Exception as e:
            print(f"   {params} -> Error: {e}")

    # Test 3: Try events endpoint
    print("\n3. Trying events endpoint...")
    try:
        response = client.get(
            "https://gamma-api.polymarket.com/events",
            params={"limit": 10, "slug_contains": "sol"}
        )
        response.raise_for_status()
        data = response.json()

        events = data if isinstance(data, list) else data.get("data", [])
        print(f"   Got {len(events)} events")

        for e in events[:3]:
            print(f"   - {e.get('title', e.get('slug', 'N/A'))[:60]}")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 4: Direct slug search
    print("\n4. Searching for SOL updown markets directly...")
    try:
        response = client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 100}
        )
        response.raise_for_status()
        data = response.json()
        markets = data if isinstance(data, list) else data.get("data", [])

        found = []
        for m in markets:
            q = (m.get("question") or "").lower()
            s = (m.get("slug") or "").lower()
            if ("sol" in s or "solana" in q) and ("up" in q or "down" in q):
                found.append(m)

        print(f"   Found {len(found)} SOL up/down markets in first 100")
        for m in found[:5]:
            print(f"   - {m.get('question', 'N/A')[:70]}")
            print(f"     slug: {m.get('slug', 'N/A')}")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 5: Save full response for analysis
    print("\n5. Saving sample response to debug_response.json...")
    try:
        response = client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 5}
        )
        response.raise_for_status()
        data = response.json()

        with open("debug_response.json", "w") as f:
            json.dump(data, f, indent=2)

        print("   Saved! Check debug_response.json")

    except Exception as e:
        print(f"   Error: {e}")

    client.close()
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE - Share the output above")
    print("=" * 60)


if __name__ == "__main__":
    main()
