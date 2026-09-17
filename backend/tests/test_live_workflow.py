import httpx

base = "http://127.0.0.1:8000/api/v1"

def run_test():
    print("=== STARTING LIVE PRODUCTION WORKFLOW VERIFICATION ===")

    # 1. Faculty Login
    r_faculty = httpx.post(f"{base}/auth/login", json={"email": "kumar@college.edu", "password": "Teacher@123"})
    print("1. Faculty login status:", r_faculty.status_code, "Role:", r_faculty.json().get("role"))
    assert r_faculty.status_code == 200
    faculty_token = r_faculty.json()["access_token"]
    h_faculty = {"Authorization": f"Bearer {faculty_token}"}

    # 2. Faculty dashboard stats
    r_stats = httpx.get(f"{base}/dashboards/faculty", headers=h_faculty)
    print("2. Faculty stats:", r_stats.json())
    assert r_stats.status_code == 200
    assert "my_classes_count" in r_stats.json()

    # 3. Faculty assigned classes
    r_classes = httpx.get(f"{base}/classes", headers=h_faculty)
    classes = [c["name"] for c in r_classes.json()]
    print("3. Faculty assigned classes:", classes)
    assert "AIDS-A" in classes
    class_id = r_classes.json()[0]["id"]

    # 4. Search student directory (e.g. Priya)
    r_search = httpx.get(f"{base}/students/search?q=Priya", headers=h_faculty)
    print("4. Directory Search (Priya): Found", len(r_search.json()), "matches")
    assert r_search.status_code == 200
    assert len(r_search.json()) >= 1

    # 5. Faculty inspects poll 1 participants
    r_parts_before = httpx.get(f"{base}/polls/1/participants", headers=h_faculty)
    print("5. Poll 1 status code:", r_parts_before.status_code)
    assert r_parts_before.status_code == 200
    p_before = r_parts_before.json()
    print(f"   Participants: Total={p_before['total_students']}, Done={p_before['completed_count']}, Not Done={p_before['pending_count']}")

    # 6. Faculty triggers official WhatsApp Cloud API reminders for poll 1
    r_remind = httpx.post(f"{base}/polls/1/remind", json={"custom_message": "Automated test reminder"}, headers=h_faculty)
    print("6. WhatsApp Reminder Dispatch status:", r_remind.status_code, "Result:", r_remind.json())
    assert r_remind.status_code == 200
    assert "sent_count" in r_remind.json()

    # 7. Verify Message Logs
    r_msgs = httpx.get(f"{base}/polls/1/messages", headers=h_faculty)
    print("7. WhatsApp Message Logs retrieved:", len(r_msgs.json()), "messages recorded")
    assert r_msgs.status_code == 200
    assert len(r_msgs.json()) >= 1

    # 8. REP Sanjay Login (Class Representative)
    r_rep = httpx.post(f"{base}/auth/login", json={"email": "sanjay@college.edu", "password": "Student@123"})
    print("8. Sanjay (REP) Login status:", r_rep.status_code, "Role:", r_rep.json().get("role"))
    assert r_rep.status_code == 200
    assert r_rep.json()["role"] == "STUDENT"
    rep_token = r_rep.json()["access_token"]
    h_rep = {"Authorization": f"Bearer {rep_token}"}

    # 9. REP inspects poll 1 participants (allowed for assigned class)
    r_rep_parts = httpx.get(f"{base}/polls/1/participants", headers=h_rep)
    print("9. REP Poll Participation inspection:", r_rep_parts.status_code)
    assert r_rep_parts.status_code == 200

    # 10. Student Rahul Login
    r_rahul = httpx.post(f"{base}/auth/login", json={"email": "rahul@college.edu", "password": "Student@123"})
    print("10. Student Rahul Login status:", r_rahul.status_code)
    assert r_rahul.status_code == 200
    rahul_token = r_rahul.json()["access_token"]
    h_rahul = {"Authorization": f"Bearer {rahul_token}"}

    # 11. Student fetches own history
    r_history = httpx.get(f"{base}/dashboards/student/history", headers=h_rahul)
    print("11. Student Rahul Participation History count:", len(r_history.json()))
    assert r_history.status_code == 200

    print("\n[SUCCESS] ALL 11 PRODUCTION LIVE E2E CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_test()
