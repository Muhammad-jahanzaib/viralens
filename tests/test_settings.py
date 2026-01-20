#!/usr/bin/env python3
"""
Test script for Settings Manager

Tests CompetitorManager and KeywordManager functionality.
"""

from utils.settings_manager import CompetitorManager, KeywordManager

print("=" * 70)
print("TESTING SETTINGS MANAGER")
print("=" * 70)

# Test 1: CompetitorManager
print("\n📊 Testing CompetitorManager...")
print("-" * 70)

manager = CompetitorManager()

# Test adding a competitor (using BBC as it's a known channel)
print("\n1. Testing add() with Channel ID auto-detection...")
try:
    result = manager.add(
        name="BBC News",
        url="https://www.youtube.com/@BBCNews",
        notes="Test competitor"
    )
    print(f"✅ Added: {result['name']}")
    print(f"   Channel ID: {result['channel_id']}")
    print(f"   URL: {result['url']}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test getting all competitors
print("\n2. Testing get_all()...")
all_competitors = manager.get_all()
print(f"✅ Total competitors: {len(all_competitors)}")
for comp in all_competitors:
    print(f"   - {comp['name']} (ID: {comp['id']}, Enabled: {comp['enabled']})")

# Test getting active competitors
print("\n3. Testing get_active()...")
active = manager.get_active()
print(f"✅ Active competitors: {len(active)}")

# Test toggling
if all_competitors:
    print("\n4. Testing toggle_enabled()...")
    first_id = all_competitors[0]['id']
    new_state = manager.toggle_enabled(first_id)
    print(f"✅ Toggled competitor ID {first_id}: enabled={new_state}")

    # Toggle back
    manager.toggle_enabled(first_id)
    print(f"✅ Toggled back")

# Test 2: KeywordManager
print("\n" + "=" * 70)
print("📊 Testing KeywordManager...")
print("-" * 70)

kw_manager = KeywordManager()

# Test getting default keywords
print("\n1. Testing default keywords...")
all_keywords = kw_manager.get_all()
print(f"✅ Total keywords: {len(all_keywords)}")
for kw in all_keywords:
    print(f"   - {kw['keyword']} (Category: {kw['category']}, Enabled: {kw['enabled']})")

# Test getting active keywords
print("\n2. Testing get_active()...")
active_kw = kw_manager.get_active()
print(f"✅ Active keywords: {active_kw}")

# Test getting by category
print("\n3. Testing get_by_category()...")
primary = kw_manager.get_by_category("primary")
print(f"✅ Primary keywords: {primary}")

secondary = kw_manager.get_by_category("secondary")
print(f"✅ Secondary keywords: {secondary}")

# Test adding keyword
print("\n4. Testing add()...")
try:
    new_kw = kw_manager.add("Kate Middleton", category="primary")
    print(f"✅ Added: {new_kw['keyword']} (ID: {new_kw['id']})")
except Exception as e:
    print(f"❌ Error: {e}")

# Summary
print("\n" + "=" * 70)
print("✅ TESTS COMPLETE!")
print("=" * 70)
print(f"\nFiles created:")
print(f"  - data/competitors.json")
print(f"  - data/keywords.json")
print(f"  - data/backups/ (backup directory)")
print("\nYou can now manage competitors and keywords dynamically!")
