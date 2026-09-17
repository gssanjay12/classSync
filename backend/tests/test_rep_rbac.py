import pytest
from datetime import datetime, timezone, timedelta
from app.models.user import User, StudentProfile, TeacherProfile
from app.models.enums import UserRole, UserStatus
from app.core.security import get_password_hash

def test_rep_rbac_and_faculty_management(client, db):
    # 1. Setup Faculty 1 (Creator)
    f1 = User(
        name="Prof. RBAC Lead",
        email="f1_rbac@college.edu",
        password_hash=get_password_hash("Teacher@123"),
        role=UserRole.FACULTY,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    # Setup Faculty 2 (Assigned Teacher)
    f2 = User(
        name="Prof. RBAC Co-Teacher",
        email="f2_rbac@college.edu",
        password_hash=get_password_hash("Teacher@123"),
        role=UserRole.FACULTY,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    # Setup Student (To be assigned REP)
    student = User(
        name="Candidate Sanjay REP",
        email="sanjay_rep_test@college.edu",
        password_hash=get_password_hash("Student@123"),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add_all([f1, f2, student])
    db.flush()

    db.add(TeacherProfile(user_id=f1.id, employee_id="F001", department="AIDS", phone_number="+919876543201"))
    db.add(TeacherProfile(user_id=f2.id, employee_id="F002", department="AIDS", phone_number="+919876543202"))
    db.add(StudentProfile(user_id=student.id, register_number="23AD001", department="AIDS", year=3, section="A", phone_number="+919876543203"))
    db.commit()

    f1_token = client.post("/api/v1/auth/login", json={"email": "f1_rbac@college.edu", "password": "Teacher@123"}).json()["access_token"]
    f1_headers = {"Authorization": f"Bearer {f1_token}"}

    f2_token = client.post("/api/v1/auth/login", json={"email": "f2_rbac@college.edu", "password": "Teacher@123"}).json()["access_token"]
    f2_headers = {"Authorization": f"Bearer {f2_token}"}

    s_token = client.post("/api/v1/auth/login", json={"email": "sanjay_rep_test@college.edu", "password": "Student@123"}).json()["access_token"]
    rep_headers = {"Authorization": f"Bearer {s_token}"}

    # 2. Faculty creates Class with allow_rep_poll_creation = True initially
    cls_res = client.post("/api/v1/classes", json={
        "name": "AIDS-RBAC",
        "department": "AI & Data Science",
        "year": 3,
        "section": "A",
        "academic_year": "2026-27",
        "allow_rep_poll_creation": True
    }, headers=f1_headers)
    assert cls_res.status_code == 200
    class_id = cls_res.json()["id"]

    # Assign Faculty 2 to class
    t_assign_res = client.post(f"/api/v1/classes/{class_id}/teachers", json={
        "teacher_id": f2.id
    }, headers=f1_headers)
    assert t_assign_res.status_code == 200

    # 3. Add student to class
    add_student_res = client.post(f"/api/v1/classes/{class_id}/students", json={
        "student_id": student.id
    }, headers=f1_headers)
    assert add_student_res.status_code == 200

    # 4. Designate student as REP
    assign_rep = client.post(f"/api/v1/classes/{class_id}/reps", json={
        "student_id": student.id
    }, headers=f1_headers)
    assert assign_rep.status_code == 200

    # Global role of student MUST still be STUDENT
    me_res = client.get("/api/v1/auth/me", headers=rep_headers).json()
    assert me_res["role"] == "STUDENT", "REP must retain global role STUDENT"
    assert any(rc["class_id"] == class_id for rc in me_res.get("rep_classes", []))

    # 5. SECURITY CHECK: REP attempts to alter class settings (PATCH /classes/{id})
    # Must be FORBIDDEN (403)
    patch_attempt = client.patch(f"/api/v1/classes/{class_id}", json={
        "allow_rep_poll_creation": False
    }, headers=rep_headers)
    assert patch_attempt.status_code == 403

    # 6. Faculty creates a poll in class
    future_deadline = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    f_poll = client.post(f"/api/v1/classes/{class_id}/polls", json={
        "question": "Faculty Announcement Poll",
        "options": ["Agree", "Disagree"],
        "deadline": future_deadline
    }, headers=f1_headers).json()
    f_poll_id = f_poll["id"]

    # 7. SECURITY CHECK: REP attempts to delete faculty's poll
    # Must be FORBIDDEN (403)
    del_attempt = client.delete(f"/api/v1/polls/{f_poll_id}", headers=rep_headers)
    assert del_attempt.status_code == 403

    # 8. REP creates their own poll (since allow_rep_poll_creation is True)
    rep_poll = client.post(f"/api/v1/classes/{class_id}/polls", json={
        "question": "REP Sports Day Poll",
        "options": ["Cricket", "Football"],
        "deadline": future_deadline
    }, headers=rep_headers)
    assert rep_poll.status_code == 200
    rep_poll_id = rep_poll.json()["id"]

    # 9. REP deletes their OWN poll -> Should succeed (200)
    rep_del_own = client.delete(f"/api/v1/polls/{rep_poll_id}", headers=rep_headers)
    assert rep_del_own.status_code == 200

    # 10. Faculty disables allow_rep_poll_creation
    disable_res = client.patch(f"/api/v1/classes/{class_id}", json={
        "allow_rep_poll_creation": False
    }, headers=f1_headers)
    assert disable_res.status_code == 200

    # 11. REP attempts to create poll now -> Should be FORBIDDEN (403)
    rep_create_blocked = client.post(f"/api/v1/classes/{class_id}/polls", json={
        "question": "Blocked Poll",
        "options": ["A", "B"],
        "deadline": future_deadline
    }, headers=rep_headers)
    assert rep_create_blocked.status_code == 403
    assert "disabled" in rep_create_blocked.json()["detail"].lower()
