from utils.user_manager import UserProfileManager
from datetime import datetime, timedelta
import os
import json

def test_user_manager():
    print("Testing UserProfileManager...")
    mgr = UserProfileManager()
    user = "test_user_v1"
    
    # 1. Check fresh user
    status = mgr.get_profile_status(user)
    print(f"Fresh User Status: {status}")
    assert status['exists'] == False
    assert status['needs_update'] == True
    
    # 2. Update Timestamp
    mgr.update_profile_timestamp(user)
    status = mgr.get_profile_status(user)
    print(f"Updated User Status: {status}")
    assert status['exists'] == True
    assert status['needs_update'] == False
    assert status['days_old'] == 0
    
    # 3. Simulate Old Profile
    # Manually hack the json
    with open("data/user_profiles.json", "r") as f:
        data = json.load(f)
    
    old_date = (datetime.now() - timedelta(days=400)).isoformat()
    data['profiles'][user]['last_updated'] = old_date
    
    with open("data/user_profiles.json", "w") as f:
        json.dump(data, f)
        
    status = mgr.get_profile_status(user)
    print(f"Old User Status: {status}")
    assert status['exists'] == True
    assert status['needs_update'] == True
    assert status['days_old'] >= 400
    
    print("✅ UserProfileManager Test Passed!")

if __name__ == "__main__":
    try:
        test_user_manager()
    except AssertionError as e:
        print(f"❌ Test Failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
