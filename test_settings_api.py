
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("🧪 Testing Settings API...")
    
    # 1. Get Config
    print("\n1. GET /api/system-config")
    try:
        resp = requests.get(f"{BASE_URL}/api/system-config")
        print(f"Status: {resp.status_code}")
        data = resp.json()
        if data.get('success'):
            print("✅ Config retrieved successfully")
            print(f"Current Max Keywords: {data['config']['collection_settings']['max_keywords']}")
        else:
            print(f"❌ Failed: {data}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # 2. Update Config
    print("\n2. PUT /api/system-config (Update max_keywords to 10)")
    try:
        update_data = {
            "collection_settings.max_keywords": 10
        }
        resp = requests.put(f"{BASE_URL}/api/system-config", json=update_data)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        if data.get('success'):
            print("✅ Config updated successfully")
            print(f"New Max Keywords: {data['config']['collection_settings']['max_keywords']}")
            if data['config']['collection_settings']['max_keywords'] == 10:
                print("✅ Verification: Value matches")
            else:
                print("❌ Verification: Value mismatch")
        else:
            print(f"❌ Failed: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 3. Get Presets
    print("\n3. GET /api/niche-presets")
    try:
        resp = requests.get(f"{BASE_URL}/api/niche-presets")
        print(f"Status: {resp.status_code}")
        data = resp.json()
        if data.get('success'):
            print(f"✅ Presets retrieved: {list(data['presets'].keys())}")
        else:
            print(f"❌ Failed: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 4. Restore Default (Optimization)
    print("\n4. Restoring default (max_keywords = 4)")
    requests.put(f"{BASE_URL}/api/system-config", json={"collection_settings.max_keywords": 4})

if __name__ == "__main__":
    # Wait for server to start
    time.sleep(2)
    test_api()
