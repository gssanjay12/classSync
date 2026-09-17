import pytest
from datetime import datetime, timezone, timedelta
from app.models.user import User, StudentProfile, TeacherProfile
from app.models.enums import UserRole, UserStatus
from app.core.security import get_password_hash

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}

def test_login_faculty_and_student(client, db):
    # Setup Faculty
    faculty = User(
        name="Prof. Kumar",
        email="kumar_test@college.edu",
        password_hash=get_password_hash("Teacher@123"),
        role=UserRole.FACULTY,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(faculty)
    db.flush()
    db.add(TeacherProfile(user_id=faculty.id, employee_id="EMP001", department="AIDS", phone_number="+919876543210"))

    # Setup Student
    student = User(
        name="Student Alpha",
        email="alpha_test@college.edu",
        password_hash=get_password_hash("Student@123"),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(student)
    db.flush()
    db.add(StudentProfile(user_id=student.id, register_number="23AD001", department="AIDS", year=3, section="A", phone_number="+919876543211"))
    db.commit()

    # Login Faculty
    f_login = client.post("/api/v1/auth/login", json={
        "email": "kumar_test@college.edu",
        "password": "Teacher@123"
    })
    assert f_login.status_code == 200
    assert f_login.json()["role"] == "FACULTY"

    # Login Student
    s_login = client.post("/api/v1/auth/login", json={
        "email": "alpha_test@college.edu",
        "password": "Student@123"
    })
    assert s_login.status_code == 200
    assert s_login.json()["role"] == "STUDENT"

def test_student_search_and_roster_management(client, db):
    # Setup Faculty
    faculty = User(
        name="Prof. Sharma",
        email="sharma_test@college.edu",
        password_hash=get_password_hash("Teacher@123"),
        role=UserRole.FACULTY,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(faculty)

    # Setup Students
    s1 = User(
        name="Priya Sharma",
        email="priya_test@college.edu",
        password_hash=get_password_hash("Student@123"),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(s1)
    db.flush()
    db.add(StudentProfile(user_id=s1.id, register_number="23AD020", department="AIDS", year=3, section="A", phone_number="+919876543220"))
    db.commit()

    f_token = client.post("/api/v1/auth/login", json={
        "email": "sharma_test@college.edu",
        "password": "Teacher@123"
    }).json()["access_token"]
    f_headers = {"Authorization": f"Bearer {f_token}"}

    # 1. Search student by register number
    search_res = client.get("/api/v1/students/search?q=23AD020", headers=f_headers)
    assert search_res.status_code == 200
    results = search_res.json()
    assert len(results) >= 1
    assert results[0]["register_number"] == "23AD020"
    assert results[0]["name"] == "Priya Sharma"

    # 2. Search student by name
    search_res2 = client.get("/api/v1/students/search?q=Priya", headers=f_headers)
    assert search_res2.status_code == 200
    assert any(r["name"] == "Priya Sharma" for r in search_res2.json())

    # 3. Create Class by Faculty
    cls_res = client.post("/api/v1/classes", json={
        "name": "AIDS-B",
        "department": "AIDS",
        "year": 3,
        "section": "B",
        "academic_year": "2026-27"
    }, headers=f_headers)
    assert cls_res.status_code == 200
    class_id = cls_res.json()["id"]

    # 4. Add student to class by student_id
    add_res = client.post(f"/api/v1/classes/{class_id}/students", json={
        "student_id": s1.id
    }, headers=f_headers)
    assert add_res.status_code == 200
    assert add_res.json()["name"] == "Priya Sharma"

    # 5. Mute student in class
    mute_res = client.patch(f"/api/v1/classes/{class_id}/members/{s1.id}/mute", json={
        "is_muted": True
    }, headers=f_headers)
    assert mute_res.status_code == 200
    assert "muted" in mute_res.json()["message"]

    # Check student roster shows muted
    roster_res = client.get(f"/api/v1/classes/{class_id}/students", headers=f_headers)
    assert roster_res.status_code == 200
    m_student = next(m for m in roster_res.json() if m["user_id"] == s1.id)
    assert m_student["is_muted"] == True

    # 6. Unmute student
    unmute_res = client.patch(f"/api/v1/classes/{class_id}/members/{s1.id}/mute", json={
        "is_muted": False
    }, headers=f_headers)
    assert unmute_res.status_code == 200
    assert "unmuted" in unmute_res.json()["message"]

def test_poll_workflow_and_mute_enforcement(client, db):
    # Setup Faculty & 2 Students
    faculty = User(name="Prof. David", email="david_test@college.edu", password_hash=get_password_hash("Teacher@123"), role=UserRole.FACULTY, status=UserStatus.ACTIVE, email_verified=True)
    db.add(faculty)

    s1 = User(name="Student One", email="s1_test@college.edu", password_hash=get_password_hash("Student@123"), role=UserRole.STUDENT, status=UserStatus.ACTIVE, email_verified=True)
    s2 = User(name="Student Two", email="s2_test@college.edu", password_hash=get_password_hash("Student@123"), role=UserRole.STUDENT, status=UserStatus.ACTIVE, email_verified=True)
    db.add_all([s1, s2])
    db.flush()

    db.add(StudentProfile(user_id=s1.id, register_number="23CS101", department="CSE", year=2, section="A", phone_number="+919876543231"))
    db.add(StudentProfile(user_id=s2.id, register_number="23CS102", department="CSE", year=2, section="A", phone_number="+919876543232"))
    db.commit()

    f_token = client.post("/api/v1/auth/login", json={"email": "david_test@college.edu", "password": "Teacher@123"}).json()["access_token"]
    s1_token = client.post("/api/v1/auth/login", json={"email": "s1_test@college.edu", "password": "Student@123"}).json()["access_token"]
    s2_token = client.post("/api/v1/auth/login", json={"email": "s2_test@college.edu", "password": "Student@123"}).json()["access_token"]

    f_headers = {"Authorization": f"Bearer {f_token}"}
    s1_headers = {"Authorization": f"Bearer {s1_token}"}
    s2_headers = {"Authorization": f"Bearer {s2_token}"}

    # Faculty creates class
    cls_res = client.post("/api/v1/classes", json={"name": "CSE-2A", "department": "CSE", "year": 2, "section": "A", "academic_year": "2026-27"}, headers=f_headers)
    class_id = cls_res.json()["id"]

    # Enroll both students
    client.post(f"/api/v1/classes/{class_id}/students", json={"student_id": s1.id}, headers=f_headers)
    client.post(f"/api/v1/classes/{class_id}/students", json={"student_id": s2.id}, headers=f_headers)

    # Mute student 2
    client.patch(f"/api/v1/classes/{class_id}/members/{s2.id}/mute", json={"is_muted": True}, headers=f_headers)

    # Faculty creates a poll
    future_deadline = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    poll_res = client.post(f"/api/v1/classes/{class_id}/polls", json={
        "question": "Attending symposium?",
        "options": ["Yes", "No"],
        "deadline": future_deadline,
        "allow_response_editing": False
    }, headers=f_headers)
    assert poll_res.status_code == 200
    poll = poll_res.json()
    poll_id = poll["id"]
    opt_yes = poll["options"][0]["id"]

    # Student 1 (unmuted) responds -> should SUCCEED
    res1 = client.post(f"/api/v1/polls/{poll_id}/respond", json={"option_id": opt_yes}, headers=s1_headers)
    assert res1.status_code == 200
    assert res1.json()["has_responded"] == True

    # Student 2 (muted) responds -> must be FORBIDDEN (403)
    res2 = client.post(f"/api/v1/polls/{poll_id}/respond", json={"option_id": opt_yes}, headers=s2_headers)
    assert res2.status_code == 403
    assert "muted" in res2.json()["detail"].lower()

    # Participant Breakdown check
    part_res = client.get(f"/api/v1/polls/{poll_id}/participants", headers=f_headers)
    assert part_res.status_code == 200
    part_data = part_res.json()
    assert part_data["completed_count"] == 1
    assert part_data["pending_count"] == 1
    assert any(d["name"] == "Student One" for d in part_data["done_students"])
    assert any(nd["name"] == "Student Two" for nd in part_data["not_done_students"])

    # WhatsApp Reminder dispatch
    remind_res = client.post(f"/api/v1/polls/{poll_id}/remind", json={
        "custom_message": "Urgent response needed"
    }, headers=f_headers)
    assert remind_res.status_code == 200
    assert remind_res.json()["sent_count"] >= 0

    # Message logs
    msgs_res = client.get(f"/api/v1/polls/{poll_id}/messages", headers=f_headers)
    assert msgs_res.status_code == 200
    assert isinstance(msgs_res.json(), list)
