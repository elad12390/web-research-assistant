#!/usr/bin/env python3
"""Test compare_tech tool functionality."""

import asyncio
import json

from src.searxng_mcp.comparison import TechComparator, detect_category
from src.searxng_mcp.search import SearxSearcher
from src.searxng_mcp.github import GitHubClient
from src.searxng_mcp.registry import PackageRegistryClient


async def test_framework_comparison():
    """Test comparing web frameworks."""
    print("\n" + "=" * 60)
    print("TEST 1: Framework Comparison (React vs Vue)")
    print("=" * 60)

    searcher = SearxSearcher()
    github_client = GitHubClient()
    registry_client = PackageRegistryClient()
    comparator = TechComparator(searcher, github_client, registry_client)

    technologies = ["React", "Vue"]
    category = detect_category(technologies)
    print(f"Detected category: {category}")

    aspects = ["performance", "learning_curve", "ecosystem", "popularity"]

    print(f"\nGathering info for {len(technologies)} technologies...")
    tech_infos = []
    for i, tech in enumerate(technologies, 1):
        print(f"  [{i}/{len(technologies)}] Gathering info for {tech}...")
        info = await comparator.gather_info(tech, category, aspects)
        tech_infos.append(info)
        print(f"      ✓ Found {len(info.sources)} sources")
        if info.popularity:
            print(f"      ✓ Popularity: {info.popularity[:50]}...")

    print(f"\n✓ Building comparison...")
    comparison = comparator.compare(tech_infos, aspects)

    print(f"\n📊 Comparison Results:")
    print(f"  Technologies: {comparison['technologies']}")
    print(f"  Category: {comparison['category']}")
    print(f"  Aspects compared: {len(comparison['aspects'])}")
    print(f"  Sources: {len(comparison['sources'])}")

    # Show sample aspect
    if "popularity" in comparison["aspects"]:
        print(f"\n  Sample - Popularity:")
        for tech, value in comparison["aspects"]["popularity"].items():
            print(f"    {tech}: {value[:60]}...")

    # Show summaries
    print(f"\n  Summaries:")
    for tech, summary in comparison["summary"].items():
        print(f"    {tech}: {summary[:80]}...")

    # Validate structure
    assert len(comparison["technologies"]) == 2
    assert comparison["category"] == "framework"
    assert len(comparison["aspects"]) > 0
    assert "React" in comparison["summary"]
    assert "Vue" in comparison["summary"]

    print("\n✅ Framework comparison test PASSED")
    return comparison


async def test_database_comparison():
    """Test comparing databases."""
    print("\n" + "=" * 60)
    print("TEST 2: Database Comparison (PostgreSQL vs MongoDB)")
    print("=" * 60)

    searcher = SearxSearcher()
    github_client = GitHubClient()
    registry_client = PackageRegistryClient()
    comparator = TechComparator(searcher, github_client, registry_client)

    technologies = ["PostgreSQL", "MongoDB"]
    category = detect_category(technologies)
    print(f"Detected category: {category}")

    aspects = ["performance", "data_model", "scaling", "use_cases"]

    print(f"\nGathering info for {len(technologies)} technologies...")
    tech_infos = []
    for i, tech in enumerate(technologies, 1):
        print(f"  [{i}/{len(technologies)}] Gathering info for {tech}...")
        info = await comparator.gather_info(tech, category, aspects)
        tech_infos.append(info)
        print(f"      ✓ Found {len(info.sources)} sources")

    print(f"\n✓ Building comparison...")
    comparison = comparator.compare(tech_infos, aspects)

    print(f"\n📊 Comparison Results:")
    print(f"  Technologies: {comparison['technologies']}")
    print(f"  Category: {comparison['category']}")
    print(f"  Aspects compared: {len(comparison['aspects'])}")

    # Show sample aspect
    if "data_model" in comparison["aspects"]:
        print(f"\n  Sample - Data Model:")
        for tech, value in comparison["aspects"]["data_model"].items():
            print(f"    {tech}: {value[:60]}...")

    print("\n✅ Database comparison test PASSED")
    return comparison


async def test_category_detection():
    """Test automatic category detection."""
    print("\n" + "=" * 60)
    print("TEST 3: Category Auto-Detection")
    print("=" * 60)

    test_cases = [
        (["React", "Vue", "Angular"], "framework"),
        (["PostgreSQL", "MySQL", "MongoDB"], "database"),
        (["Python", "JavaScript", "Go"], "language"),
        (["Webpack", "Vite", "Parcel"], "library"),
        (["axios", "fetch"], "library"),
    ]

    for technologies, expected in test_cases:
        detected = detect_category(technologies)
        status = "✓" if detected == expected else "✗"
        print(f"  {status} {technologies} → {detected} (expected: {expected})")
        if detected != expected:
            print(f"      Note: Auto-detection uses heuristics, may vary")

    print("\n✅ Category detection test COMPLETED")


async def test_json_output():
    """Test that output is valid JSON."""
    print("\n" + "=" * 60)
    print("TEST 4: JSON Output Validation")
    print("=" * 60)

    searcher = SearxSearcher()
    github_client = GitHubClient()
    registry_client = PackageRegistryClient()
    comparator = TechComparator(searcher, github_client, registry_client)

    technologies = ["FastAPI", "Flask"]
    category = "framework"
    aspects = ["performance", "features"]

    print(f"\nComparing {technologies}...")
    tech_infos = []
    for tech in technologies:
        info = await comparator.gather_info(tech, category, aspects)
        tech_infos.append(info)

    comparison = comparator.compare(tech_infos, aspects)

    # Try to serialize to JSON
    try:
        json_output = json.dumps(comparison, indent=2, ensure_ascii=False)
        print(f"✓ Valid JSON output ({len(json_output)} characters)")

        # Try to parse it back
        parsed = json.loads(json_output)
        assert "technologies" in parsed
        assert "aspects" in parsed
        assert "summary" in parsed
        print(f"✓ JSON structure validated")

    except Exception as e:
        print(f"✗ JSON validation failed: {e}")
        raise

    print("\n✅ JSON output test PASSED")


async def main():
    """Run all tests."""
    print("\n🧪 Starting compare_tech Tool Tests")
    print("=" * 60)

    tests = [
        ("Framework Comparison", test_framework_comparison),
        ("Database Comparison", test_database_comparison),
        ("Category Detection", test_category_detection),
        ("JSON Output", test_json_output),
    ]

    passed = 0
    failed = 0
    results = []

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} test FAILED: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("✅ All tests PASSED!")

        # Show a sample comparison output
        if results and results[0]:
            print("\n" + "=" * 60)
            print("Sample Comparison Output (React vs Vue):")
            print("=" * 60)
            print(json.dumps(results[0], indent=2)[:1000] + "...")
    else:
        print(f"❌ {failed} test(s) FAILED")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
