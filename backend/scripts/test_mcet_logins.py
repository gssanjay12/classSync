import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal
from app.models.token import RefreshToken

client = TestClient(app)

def test_login(identifier, password, expected_status=200):
    res = client.post("/api/v1/auth/login", json={"email": identifier, "password": password})
    print(f"Login '{identifier}' with '{password}' -> Status {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"   Success! User: {data['name']} ({data['email']}), Role: {data['role']}, Token: {data['access_token'][:20]}...")
    else:
        print(f"   Response: {res.text}")
    assert res.status_code == expected_status, f"Expected {expected_status}, got {res.status_code}"
    return res

if __name__ == "__main__":
    print("=== Testing Login with Email ===")
    test_login("727625bad091@mcet.in", "Mcet@12345", 200)
    test_login("727625bad062@mcet.in", "Mcet@12345", 200)
    test_login("727626bad302@mcet.in", "Mcet@12345", 200)

    print("\n=== Testing Login with Name ===")
    test_login("Sanjay GS", "Mcet@12345", 200)
    test_login("Nikith varshan A", "Mcet@12345", 200)
    test_login("Pirajin P", "Mcet@12345", 200)
    test_login("Pradeep S", "Mcet@12345", 200)

    print("\n=== Testing Login with Faculty ===")
    test_login("kumar@college.edu", "Mcet@12345", 200)
    test_login("Prof. Kumar", "Mcet@12345", 200)

    print("\n=== Testing Login with Invalid Password ===")
    test_login("727625bad091@mcet.in", "WrongPassword!999", 401)

    print("\n[ALL LOGIN TESTS PASSED SUCCESSFULLY!]")
