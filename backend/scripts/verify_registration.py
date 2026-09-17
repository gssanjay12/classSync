import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from app.main import app

def verify_db_state(db_path):
    print(f"\n--- Checking DB: {db_path} ---")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    classes = cur.execute("SELECT id, name, section FROM classes").fetchall()
    print("Classes:", classes)

    total_students = cur.execute("SELECT count(*) FROM users WHERE role = 'STUDENT'").fetchone()[0]
    total_profiles = cur.execute("SELECT count(*) FROM student_profiles WHERE section = 'B'").fetchone()[0]
    b_members = cur.execute("SELECT count(*) FROM class_members WHERE class_id = 2").fetchone()[0]
    a_members = cur.execute("SELECT count(*) FROM class_members WHERE class_id = 1").fetchone()[0]
    reps = cur.execute("""
        SELECT cr.class_id, c.name, u.name, u.email 
        FROM class_representatives cr
        JOIN classes c ON cr.class_id = c.id
        JOIN users u ON cr.student_id = u.id
    """).fetchall()
    teachers = cur.execute("""
        SELECT ct.class_id, c.name, u.name, u.email 
        FROM class_teachers ct
        JOIN classes c ON ct.class_id = c.id
        JOIN users u ON ct.teacher_id = u.id
    """).fetchall()
    polls = cur.execute("SELECT id, public_id, class_id, question, status FROM polls WHERE class_id = 2").fetchall()

    print(f"Total students: {total_students}")
    print(f"Student profiles with Section 'B': {total_profiles}")
    print(f"AIDS-B members: {b_members} | AIDS-A members: {a_members}")
    print(f"Class Reps: {reps}")
    print(f"Class Teachers: {teachers}")
    print(f"AIDS-B Polls: {polls}")

    assert total_students == 57, f"Expected 57 students, got {total_students}"
    assert total_profiles == 57, f"Expected 57 Section B profiles, got {total_profiles}"
    assert b_members == 57, f"Expected 57 AIDS-B members, got {b_members}"
    assert a_members == 0, f"Expected 0 AIDS-A members, got {a_members}"
    assert len(reps) >= 1 and reps[0][1] == "AIDS-B", "AIDS-B representative missing"
    assert len(polls) >= 1, "AIDS-B active poll missing"
    conn.close()
    print("[PASS] DB State is 100% correct!")

def verify_api():
    print("\n--- Testing API Endpoints via TestClient ---")
    client = TestClient(app)

    # 1. Login Sanjay GS (Student & AIDS-B Rep)
    res = client.post("/api/v1/auth/login", json={"email": "727625bad091@mcet.in", "password": "Mcet@12345"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    sanjay_data = res.json()
    token = sanjay_data["access_token"]
    print(f"[PASS] Sanjay GS login successful! Role: {sanjay_data['role']}")

    # 2. Check /api/v1/users/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["student_profile"]["section"] == "B"
    assert me_data["student_profile"]["department"] == "AI & Data Science"
    assert len(me_data["rep_classes"]) > 0
    assert me_data["rep_classes"][0]["class_name"] == "AIDS-B"
    print(f"[PASS] Profile verified: Name='{me_data['name']}', Section='{me_data['student_profile']['section']}', Rep in='{me_data['rep_classes'][0]['class_name']}'")

    # 3. Login by Register Number
    res_reg = client.post("/api/v1/auth/login", json={"email": "727625BAD062", "password": "Mcet@12345"})
    assert res_reg.status_code == 200, f"Login by reg_no failed: {res_reg.text}"
    print(f"[PASS] Login by register number successful: {res_reg.json()['name']}")

    # 4. Login by Name
    res_name = client.post("/api/v1/auth/login", json={"email": "Pirajin P", "password": "Mcet@12345"})
    assert res_name.status_code == 200, f"Login by name failed: {res_name.text}"
    print(f"[PASS] Login by student name successful: {res_name.json()['name']} ({res_name.json()['email']})")

    # 5. Login Faculty Prof. Kumar
    res_fac = client.post("/api/v1/auth/login", json={"email": "kumar@college.edu", "password": "Mcet@12345"})
    assert res_fac.status_code == 200, f"Faculty login failed: {res_fac.text}"
    fac_token = res_fac.json()["access_token"]
    print(f"[PASS] Faculty login successful: {res_fac.json()['name']}")

    # 6. Check AIDS-B members list as Faculty
    fac_headers = {"Authorization": f"Bearer {fac_token}"}
    members_res = client.get("/api/v1/classes/2/students", headers=fac_headers)
    assert members_res.status_code == 200, f"Failed to get students: {members_res.text}"
    members = members_res.json()
    print(f"[PASS] AIDS-B Class members retrieved: {len(members)} students")
    assert len(members) == 57

    # 7. Check Active Polls for Student via student dashboard & class polls
    dash_res = client.get("/api/v1/dashboards/student", headers=headers)
    assert dash_res.status_code == 200, f"Dashboard failed: {dash_res.text}"
    dash_data = dash_res.json()
    print(f"[PASS] Student dashboard retrieved: {dash_data['active_polls_count']} active poll(s)")
    assert dash_data["active_polls_count"] >= 1

    polls_res = client.get("/api/v1/polls/classes/2/polls", headers=headers)
    assert polls_res.status_code == 200, f"Class polls failed: {polls_res.text}"
    polls = polls_res.json()
    print(f"[PASS] AIDS-B Polls retrieved: {len(polls)} poll(s) found (Question: '{polls[0]['question']}')")
    assert len(polls) >= 1

    print("\n[ALL DATABASE AND API VERIFICATION CHECKS PASSED PERFECTLY!]")

if __name__ == "__main__":
    verify_db_state(r"c:\Users\SANJAY\Desktop\classSync\backend\classpoll.db")
    verify_db_state(r"c:\Users\SANJAY\Desktop\classSync\classpoll.db")
    verify_api()
