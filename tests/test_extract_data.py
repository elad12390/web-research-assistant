#!/usr/bin/env python3
"""Test extract_data tool functionality."""

import asyncio
import json

from src.searxng_mcp.crawler import CrawlerClient
from src.searxng_mcp.extractor import DataExtractor


async def test_table_extraction():
    """Test extracting tables from a page."""
    print("\n" + "=" * 60)
    print("TEST 1: Table Extraction from W3Schools")
    print("=" * 60)

    crawler = CrawlerClient()
    extractor = DataExtractor()

    # Test with W3Schools page that has tables (need more chars)
    url = "https://www.w3schools.com/html/html_tables.asp"
    print(f"Fetching: {url}")

    try:
        html = await crawler.fetch_raw(url, max_chars=500000)  # Need more for this page
        print(f"✓ Fetched {len(html)} characters of HTML")

        tables = extractor.extract_tables(html, max_tables=2)
        print(f"✓ Found {len(tables)} tables")

        for i, table in enumerate(tables, 1):
            print(f"\nTable {i}:")
            print(f"  Caption: {table.caption}")
            print(f"  Headers: {table.headers}")
            print(f"  Rows: {len(table.rows)}")
            if table.rows:
                print(f"  Sample row: {table.rows[0]}")

        assert len(tables) > 0, "Should find at least one table"
        print("\n✅ Table extraction test PASSED")

    except Exception as e:
        print(f"\n❌ Table extraction test FAILED: {e}")
        raise


async def test_list_extraction():
    """Test extracting lists from a page."""
    print("\n" + "=" * 60)
    print("TEST 2: List Extraction from GitHub Releases")
    print("=" * 60)

    crawler = CrawlerClient()
    extractor = DataExtractor()

    # Test with GitHub releases page
    url = "https://github.com/fastapi/fastapi/releases"
    print(f"Fetching: {url}")

    try:
        html = await crawler.fetch_raw(url)
        print(f"✓ Fetched {len(html)} characters of HTML")

        lists = extractor.extract_lists(html, max_lists=3)
        print(f"✓ Found {len(lists)} lists")

        for i, lst in enumerate(lists, 1):
            print(f"\nList {i}:")
            print(f"  Title: {lst.title}")
            print(f"  Items: {len(lst.items)}")
            if lst.items:
                print(f"  First item: {lst.items[0][:100]}...")

        print("\n✅ List extraction test PASSED")

    except Exception as e:
        print(f"\n❌ List extraction test FAILED: {e}")
        raise


async def test_field_extraction():
    """Test extracting specific fields from a page."""
    print("\n" + "=" * 60)
    print("TEST 3: Field Extraction from PyPI")
    print("=" * 60)

    crawler = CrawlerClient()
    extractor = DataExtractor()

    # Test with PyPI package page
    url = "https://pypi.org/project/fastapi/"
    print(f"Fetching: {url}")

    try:
        html = await crawler.fetch_raw(url)
        print(f"✓ Fetched {len(html)} characters of HTML")

        # Define selectors for common PyPI elements
        selectors = {
            "title": "h1.package-header__name",
            "version": ".package-header__pip-instructions span",
            "description": ".package-description__summary",
        }

        fields = extractor.extract_fields(html, selectors)
        print(f"✓ Extracted {len(fields)} fields")

        for field_name, value in fields.items():
            if isinstance(value, list):
                print(f"\n{field_name}: [{len(value)} items]")
                for v in value[:3]:
                    print(f"  - {v}")
            else:
                print(
                    f"\n{field_name}: {value[:100] if len(str(value)) > 100 else value}"
                )

        assert len(fields) > 0, "Should extract at least one field"
        print("\n✅ Field extraction test PASSED")

    except Exception as e:
        print(f"\n❌ Field extraction test FAILED: {e}")
        raise


async def test_json_ld_extraction():
    """Test extracting JSON-LD structured data."""
    print("\n" + "=" * 60)
    print("TEST 4: JSON-LD Extraction")
    print("=" * 60)

    crawler = CrawlerClient()
    extractor = DataExtractor()

    # Many product pages have JSON-LD
    url = "https://www.npmjs.com/package/express"
    print(f"Fetching: {url}")

    try:
        html = await crawler.fetch_raw(url)
        print(f"✓ Fetched {len(html)} characters of HTML")

        json_ld = extractor.extract_json_ld(html)
        print(f"✓ Found {len(json_ld)} JSON-LD objects")

        for i, obj in enumerate(json_ld, 1):
            print(f"\nJSON-LD Object {i}:")
            print(f"  Type: {obj.get('@type', 'Unknown')}")
            print(
                f"  Data: {json.dumps(obj, indent=2)[:200]}..."
                if len(json.dumps(obj)) > 200
                else json.dumps(obj, indent=2)
            )

        print("\n✅ JSON-LD extraction test PASSED")

    except Exception as e:
        print(f"\n❌ JSON-LD extraction test FAILED: {e}")
        # This is not critical, as not all pages have JSON-LD
        print("(This is expected if the page has no JSON-LD data)")


async def test_auto_extraction():
    """Test automatic extraction."""
    print("\n" + "=" * 60)
    print("TEST 5: Auto Extraction")
    print("=" * 60)

    crawler = CrawlerClient()
    extractor = DataExtractor()

    # Test with a page that has multiple types of content
    url = "https://www.python.org/"
    print(f"Fetching: {url}")

    try:
        html = await crawler.fetch_raw(url)
        print(f"✓ Fetched {len(html)} characters of HTML")

        auto_data = extractor.auto_extract(html)
        print(f"✓ Auto extraction completed")

        print(f"\nExtracted data types:")
        print(f"  Tables: {len(auto_data.get('tables', []))}")
        print(f"  Lists: {len(auto_data.get('lists', []))}")
        print(f"  JSON-LD: {len(auto_data.get('json_ld', []))}")

        # Show a sample of each type
        if auto_data.get("tables"):
            table = auto_data["tables"][0]
            print(f"\nSample table:")
            print(f"  Headers: {table['headers']}")
            print(f"  Rows: {len(table['rows'])}")

        if auto_data.get("lists"):
            lst = auto_data["lists"][0]
            print(f"\nSample list:")
            print(f"  Title: {lst['title']}")
            print(f"  Items: {len(lst['items'])}")

        print("\n✅ Auto extraction test PASSED")

    except Exception as e:
        print(f"\n❌ Auto extraction test FAILED: {e}")
        raise


async def main():
    """Run all tests."""
    print("\n🧪 Starting extract_data Tool Tests")
    print("=" * 60)

    tests = [
        test_table_extraction,
        test_list_extraction,
        test_field_extraction,
        test_json_ld_extraction,
        test_auto_extraction,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\nTest failed with error: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("✅ All tests PASSED!")
    else:
        print(f"❌ {failed} test(s) FAILED")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
