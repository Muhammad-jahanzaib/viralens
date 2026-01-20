
import requests
import io
import pandas as pd
import os

BASE_URL = "http://localhost:8000"

def test_excel_endpoints():
    print("🧪 Testing Excel Endpoints...")
    
    # 1. Test Competitor Template
    print("\n1. Testing Competitor Template...")
    try:
        r = requests.get(f"{BASE_URL}/api/competitors/template")
        if r.status_code == 200:
            df = pd.read_excel(io.BytesIO(r.content))
            required = ['Name', 'URL']
            if all(col in df.columns for col in required):
                print("✅ Template received with valid columns")
            else:
                print(f"❌ Template missing columns. Found: {df.columns}")
        else:
            print(f"❌ Failed to get template: {r.status_code}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

    # 2. Test Competitor Export
    print("\n2. Testing Competitor Export...")
    try:
        r = requests.get(f"{BASE_URL}/api/competitors/export")
        if r.status_code == 200:
            df = pd.read_excel(io.BytesIO(r.content))
            print(f"✅ Export received with {len(df)} rows")
        else:
            print(f"❌ Failed to export: {r.status_code}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

    # 3. Test Keyword Import (Valid)
    print("\n3. Testing Keyword Import (Valid)...")
    try:
        # Create dummy excel
        df = pd.DataFrame({'Keyword': ['Test Keyword'], 'Category': ['primary']})
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        
        files = {'file': ('test.xlsx', output, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        r = requests.post(f"{BASE_URL}/api/keywords/import", files=files)
        
        if r.status_code == 200:
            print(f"✅ Import successful: {r.json().get('message')}")
        else:
            print(f"❌ Import failed: {r.text}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

    # 4. Test Keyword Import (Invalid)
    print("\n4. Testing Keyword Import (Invalid Columns)...")
    try:
        # Create bad excel
        df = pd.DataFrame({'WrongCol': ['Test']})
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        
        files = {'file': ('bad.xlsx', output, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        r = requests.post(f"{BASE_URL}/api/keywords/import", files=files)
        
        if r.status_code == 400 and 'Missing required column' in r.text:
            print("✅ Import correctly rejected invalid file")
        else:
            print(f"❌ Failed to reject invalid file: {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_excel_endpoints()
