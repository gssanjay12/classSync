import httpx

base = "http://127.0.0.1:8000/api/v1"

tests = [
    ("College Email: rahul@college.edu", "rahul@college.edu", "Student@123", "Rahul V"),
    ("Full Name: Rahul V", "Rahul V", "Student@123", "Rahul V"),
    ("College Email: sanjay@college.edu", "sanjay@college.edu", "Student@123", "Sanjay G S"),
    ("Full Name: Sanjay G S", "Sanjay G S", "Student@123", "Sanjay G S"),
    ("College Email: kumar@college.edu", "kumar@college.edu", "Teacher@123", "Prof. Kumar"),
    ("Full Name: Prof. Kumar", "Prof. Kumar", "Teacher@123", "Prof. Kumar"),
    ("Full Name: Priya S", "Priya S", "Student@123", "Priya S"),
    ("College Email: priya@college.edu", "priya@college.edu", "Student@123", "Priya S"),
    ("Full Name: Arun M", "Arun M", "Student@123", "Arun M"),
    ("College Email: arun@college.edu", "arun@college.edu", "Student@123", "Arun M"),
    ("Full Name: Bala K", "Bala K", "Student@123", "Bala K"),
    ("College Email: bala@college.edu", "bala@college.edu", "Student@123", "Bala K"),
    ("Full Name: Vignesh S", "Vignesh S", "Student@123", "Vignesh S"),
    ("College Email: vignesh@college.edu", "vignesh@college.edu", "Student@123", "Vignesh S"),
    ("Full Name: Divya R", "Divya R", "Student@123", "Divya R"),
    ("College Email: divya@college.edu", "divya@college.edu", "Student@123", "Divya R"),
]

passed = 0
for label, ident, pw, expected_name in tests:
    res = httpx.post(f"{base}/auth/login", json={"email": ident, "password": pw})
    if res.status_code == 200 and res.json()["name"] == expected_name:
        passed += 1
        print(f"[PASS] {label} -> Logged in as '{expected_name}' ({res.json()['role']})")
    else:
        print(f"[FAIL] {label} -> Status: {res.status_code}, Response: {res.text}")

print(f"\nResult: {passed}/{len(tests)} passed!")
