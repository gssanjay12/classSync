import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.models.user import User, StudentProfile, TeacherProfile
from app.models.class_model import Class, ClassMember, ClassTeacher, ClassRepresentative
from app.models.poll import Poll, PollOption, Response
from app.models.message_log import MessageLog
from app.models.enums import UserRole, UserStatus, PollStatus
from app.core.security import get_password_hash
from app.services.whatsapp import clean_phone_number, WhatsAppService


def test_clean_phone_number_normalization():
    # 10-digit Indian number without country code
    assert clean_phone_number("9876543210") == "919876543210"

    # With leading zero
    assert clean_phone_number("09876543210") == "919876543210"

    # Already formatted with 91
    assert clean_phone_number("919876543210") == "919876543210"

    # Formatted with plus, spaces, dashes
    assert clean_phone_number("+91 98765-43210") == "919876543210"
    assert clean_phone_number("+91 (987) 654-3210") == "919876543210"

    # Other international numbers (E.164)
    assert clean_phone_number("+14155552671") == "14155552671"

    # Invalid / malformed numbers
    assert clean_phone_number(None) is None
    assert clean_phone_number("") is None
    assert clean_phone_number("   ") is None
    assert clean_phone_number("12345") is None  # Too short
    assert clean_phone_number("12345678901234567") is None  # Too long


def test_unconfigured_mode_does_not_fake_success(client, db):
    """When WhatsApp is not enabled/configured, system must NOT simulate success."""
    with patch.object(settings, "WHATSAPP_ENABLED", False):
        assert WhatsAppService.is_configured() is False

        # Create faculty
        faculty = User(
            name="Prof. Raman",
            email="raman_unconf@college.edu",
            password_hash=get_password_hash("Teacher@123"),
            role=UserRole.FACULTY,
            status=UserStatus.ACTIVE,
            email_verified=True
        )
        db.add(faculty)
        db.flush()

        # Create student
        student = User(
            name="Gita",
            email="gita_unconf@college.edu",
            password_hash=get_password_hash("Student@123"),
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified=True
        )
        db.add(student)
        db.flush()
        db.add(StudentProfile(user_id=student.id, register_number="727625BUN01", department="AIDS", year=3, section="A", phone_number="+919876543210"))

        # Create class & poll
        cls = Class(name="AIDS-UNCONF", department="AIDS", year=3, section="A", academic_year="2026-27", class_code="AIDS-UNCONF")
        db.add(cls)
        db.flush()
        db.add(ClassTeacher(class_id=cls.id, teacher_id=faculty.id))
        db.add(ClassMember(class_id=cls.id, student_id=student.id))

        future_deadline = datetime.now(timezone.utc) + timedelta(days=2)
        poll = Poll(
            class_id=cls.id,
            creator_id=faculty.id,
            question="Unconfigured Test Poll?",
            deadline=future_deadline,
            status=PollStatus.ACTIVE,
            public_id="unconf_poll_123"
        )
        db.add(poll)
        db.commit()

        f_token = client.post("/api/v1/auth/login", json={"email": "raman_unconf@college.edu", "password": "Teacher@123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {f_token}"}

        # Send reminder
        res = client.post(f"/api/v1/polls/{poll.id}/remind", json={}, headers=headers)
        assert res.status_code == 200
        data = res.json()

        # Critical: Must report NOT configured and FAILED, never SENT
        assert data["whatsapp_configured"] is False
        assert data["sent_count"] == 0
        assert data["failed_count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["delivery_status"] == "FAILED"
        assert "not configured" in data["results"][0]["error_message"].lower()

        # Check DB log
        log = db.query(MessageLog).filter(MessageLog.poll_id == poll.id).first()
        assert log is not None
        assert log.delivery_status == "FAILED"
        assert "not configured" in log.error_message.lower()


def test_configured_whatsapp_dispatch_with_mocked_meta_api(client, db):
    """When configured, reminder uses Meta WhatsApp Cloud API endpoint and records WAMID."""
    with patch.object(settings, "WHATSAPP_ENABLED", True), \
         patch.object(settings, "WHATSAPP_PHONE_NUMBER_ID", "109876543211111"), \
         patch.object(settings, "WHATSAPP_ACCESS_TOKEN", "EAAXfake_access_token_secure"), \
         patch.object(settings, "WHATSAPP_USE_TEMPLATE", True):

        assert WhatsAppService.is_configured() is True

        faculty = User(
            name="Prof. Meta",
            email="meta_faculty@college.edu",
            password_hash=get_password_hash("Teacher@123"),
            role=UserRole.FACULTY,
            status=UserStatus.ACTIVE,
            email_verified=True
        )
        db.add(faculty)
        db.flush()

        student = User(
            name="Karthik R",
            email="karthik_meta@college.edu",
            password_hash=get_password_hash("Student@123"),
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified=True
        )
        db.add(student)
        db.flush()
        db.add(StudentProfile(user_id=student.id, register_number="727625BMETA01", department="AIDS", year=3, section="A", phone_number="+919876543210"))

        cls = Class(name="AIDS-META", department="AIDS", year=3, section="A", academic_year="2026-27", class_code="AIDS-META")
        db.add(cls)
        db.flush()
        db.add(ClassTeacher(class_id=cls.id, teacher_id=faculty.id))
        db.add(ClassMember(class_id=cls.id, student_id=student.id))

        future_deadline = datetime.now(timezone.utc) + timedelta(days=2)
        poll = Poll(
            class_id=cls.id,
            creator_id=faculty.id,
            question="Meta Cloud API Verification Poll?",
            deadline=future_deadline,
            status=PollStatus.ACTIVE,
            public_id="meta_poll_789"
        )
        db.add(poll)
        db.commit()

        f_token = client.post("/api/v1/auth/login", json={"email": "meta_faculty@college.edu", "password": "Teacher@123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {f_token}"}

        # Mock httpx.Client.post for Meta WhatsApp Cloud API
        mock_meta_resp = MagicMock()
        mock_meta_resp.status_code = 200
        mock_meta_resp.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
            "messages": [{"id": "wamid.HBgLMTE5OTg3NjU0MzIxMBUCMR..."}]
        }

        with patch("app.services.whatsapp.httpx.Client") as mock_client_cls:
            mock_client_instance = mock_client_cls.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_meta_resp

            res = client.post(f"/api/v1/polls/{poll.id}/remind", json={}, headers=headers)
            assert res.status_code == 200
            data = res.json()

            assert data["whatsapp_configured"] is True
            assert data["sent_count"] == 1
            assert data["failed_count"] == 0
            assert len(data["results"]) == 1
            assert data["results"][0]["delivery_status"] == "SENT"
            assert data["results"][0]["provider_message_id"] == "wamid.HBgLMTE5OTg3NjU0MzIxMBUCMR..."
            assert data["results"][0]["student_register_number"] == "727625BMETA01"

            # Check that mock_post was called with template payload
            mock_client_instance.post.assert_called_once()
            call_kwargs = mock_client_instance.post.call_args[1]
            assert "json" in call_kwargs
            payload = call_kwargs["json"]
            assert payload["type"] == "template"
            assert payload["to"] == "919876543210"
            assert payload["template"]["name"] == settings.WHATSAPP_TEMPLATE_NAME


def test_reject_reminder_for_already_responded_student(client, db):
    """Faculty cannot send reminder to student who has already submitted."""
    faculty = User(
        name="Prof. Responded",
        email="resp_faculty@college.edu",
        password_hash=get_password_hash("Teacher@123"),
        role=UserRole.FACULTY,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(faculty)
    db.flush()

    student = User(
        name="Anand",
        email="anand_resp@college.edu",
        password_hash=get_password_hash("Student@123"),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(student)
    db.flush()
    db.add(StudentProfile(user_id=student.id, register_number="727625BRESP01", department="AIDS", year=3, section="A", phone_number="+919876543210"))

    cls = Class(name="AIDS-RESP", department="AIDS", year=3, section="A", academic_year="2026-27", class_code="AIDS-RESP")
    db.add(cls)
    db.flush()
    db.add(ClassTeacher(class_id=cls.id, teacher_id=faculty.id))
    db.add(ClassMember(class_id=cls.id, student_id=student.id))

    future_deadline = datetime.now(timezone.utc) + timedelta(days=2)
    poll = Poll(
        class_id=cls.id,
        creator_id=faculty.id,
        question="Already responded poll?",
        deadline=future_deadline,
        status=PollStatus.ACTIVE,
        public_id="resp_poll_456"
    )
    db.add(poll)
    db.flush()
    opt = PollOption(poll_id=poll.id, option_text="Yes", position=0)
    db.add(opt)
    db.flush()

    # Record response from student
    db.add(Response(poll_id=poll.id, student_id=student.id, option_id=opt.id))
    db.commit()

    f_token = client.post("/api/v1/auth/login", json={"email": "resp_faculty@college.edu", "password": "Teacher@123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {f_token}"}

    # Attempting to remind specifically this student must be rejected
    res = client.post(f"/api/v1/polls/{poll.id}/remind", json={"student_ids": [student.id]}, headers=headers)
    assert res.status_code == 400
    assert "already responded" in res.json()["detail"].lower()


def test_reject_reminder_for_expired_poll(client, db):
    """Reminders must be rejected if poll deadline has passed or poll is closed."""
    faculty = User(
        name="Prof. Expired",
        email="exp_faculty@college.edu",
        password_hash=get_password_hash("Teacher@123"),
        role=UserRole.FACULTY,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(faculty)
    db.flush()

    cls = Class(name="AIDS-EXP", department="AIDS", year=3, section="A", academic_year="2026-27", class_code="AIDS-EXP")
    db.add(cls)
    db.flush()
    db.add(ClassTeacher(class_id=cls.id, teacher_id=faculty.id))

    past_deadline = datetime.now(timezone.utc) - timedelta(days=1)
    poll = Poll(
        class_id=cls.id,
        creator_id=faculty.id,
        question="Expired Poll?",
        deadline=past_deadline,
        status=PollStatus.ACTIVE,
        public_id="exp_poll_000"
    )
    db.add(poll)
    db.commit()

    f_token = client.post("/api/v1/auth/login", json={"email": "exp_faculty@college.edu", "password": "Teacher@123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {f_token}"}

    res = client.post(f"/api/v1/polls/{poll.id}/remind", json={}, headers=headers)
    assert res.status_code == 400
    assert "closed or expired" in res.json()["detail"].lower()


def test_student_missing_phone_marked_failed(client, db):
    """If student has no phone number, reminder must fail gracefully without calling provider."""
    faculty = User(
        name="Prof. NoPhone",
        email="nophone_faculty@college.edu",
        password_hash=get_password_hash("Teacher@123"),
        role=UserRole.FACULTY,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(faculty)
    db.flush()

    student = User(
        name="Student Without Phone",
        email="nophone_student@college.edu",
        password_hash=get_password_hash("Student@123"),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(student)
    db.flush()
    db.add(StudentProfile(user_id=student.id, register_number="727625BNOPHONE", department="AIDS", year=3, section="A", phone_number=None))

    cls = Class(name="AIDS-NOPHONE", department="AIDS", year=3, section="A", academic_year="2026-27", class_code="AIDS-NOPHONE")
    db.add(cls)
    db.flush()
    db.add(ClassTeacher(class_id=cls.id, teacher_id=faculty.id))
    db.add(ClassMember(class_id=cls.id, student_id=student.id))

    future_deadline = datetime.now(timezone.utc) + timedelta(days=2)
    poll = Poll(
        class_id=cls.id,
        creator_id=faculty.id,
        question="Missing Phone Poll?",
        deadline=future_deadline,
        status=PollStatus.ACTIVE,
        public_id="nophone_poll_111"
    )
    db.add(poll)
    db.commit()

    f_token = client.post("/api/v1/auth/login", json={"email": "nophone_faculty@college.edu", "password": "Teacher@123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {f_token}"}

    res = client.post(f"/api/v1/polls/{poll.id}/remind", json={}, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["failed_count"] == 1
    assert data["results"][0]["delivery_status"] == "FAILED"
    assert "not available" in data["results"][0]["error_message"].lower()


def test_rep_permission_and_isolation(client, db):
    """REP can send reminders for their assigned class, but not for unrelated classes."""
    rep = User(
        name="REP Priya",
        email="rep_priya@college.edu",
        password_hash=get_password_hash("Student@123"),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(rep)
    db.flush()

    s_class_a = User(
        name="Student In Class A",
        email="s_a@college.edu",
        password_hash=get_password_hash("Student@123"),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified=True
    )
    db.add(s_class_a)
    db.flush()
    db.add(StudentProfile(user_id=s_class_a.id, register_number="727625BSA01", department="AIDS", year=3, section="A", phone_number="+919876543210"))

    class_a = Class(name="Class A", department="AIDS", year=3, section="A", academic_year="2026-27", class_code="CLASS-A")
    class_b = Class(name="Class B", department="CSE", year=3, section="A", academic_year="2026-27", class_code="CLASS-B")
    db.add(class_a)
    db.add(class_b)
    db.flush()

    # Designate Priya as REP for Class A only
    db.add(ClassRepresentative(class_id=class_a.id, student_id=rep.id))
    db.add(ClassMember(class_id=class_a.id, student_id=s_class_a.id))

    future_deadline = datetime.now(timezone.utc) + timedelta(days=2)
    poll_a = Poll(class_id=class_a.id, creator_id=rep.id, question="Class A Poll?", deadline=future_deadline, status=PollStatus.ACTIVE, public_id="poll_a_123")
    poll_b = Poll(class_id=class_b.id, creator_id=rep.id, question="Class B Poll?", deadline=future_deadline, status=PollStatus.ACTIVE, public_id="poll_b_123")
    db.add(poll_a)
    db.add(poll_b)
    db.commit()

    rep_token = client.post("/api/v1/auth/login", json={"email": "rep_priya@college.edu", "password": "Student@123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {rep_token}"}

    # Allowed: REP Priya sending reminder for Poll A (her assigned class)
    res_a = client.post(f"/api/v1/polls/{poll_a.id}/remind", json={}, headers=headers)
    assert res_a.status_code == 200

    # Forbidden: REP Priya attempting to remind Poll B (not assigned)
    res_b = client.post(f"/api/v1/polls/{poll_b.id}/remind", json={}, headers=headers)
    assert res_b.status_code == 403


def test_whatsapp_webhook_flow(client, db):
    """Verifies WhatsApp Cloud API webhook challenge verification and status updates."""
    # 1. GET Challenge Verification
    verify_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    challenge_val = "1158201444"

    res_verify = client.get(
        f"/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.challenge={challenge_val}&hub.verify_token={verify_token}"
    )
    assert res_verify.status_code == 200
    assert res_verify.text == challenge_val

    # Bad token -> 403
    res_bad = client.get(
        f"/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.challenge={challenge_val}&hub.verify_token=wrong_token"
    )
    assert res_bad.status_code == 403

    # 2. POST Delivery Status Update (DELIVERED, READ)
    wamid_test = "wamid.HBgLTESTMESSAGE12345"
    log = MessageLog(
        poll_id=1,
        student_id=1,
        sent_by=1,
        recipient_phone="+919876543210",
        message_type="POLL_REMINDER",
        provider="WHATSAPP_CLOUD_API",
        provider_message_id=wamid_test,
        delivery_status="SENT"
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "10000001",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {},
                            "statuses": [
                                {
                                    "id": wamid_test,
                                    "status": "delivered",
                                    "timestamp": "1726589230",
                                    "recipient_id": "919876543210"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    res_status = client.post("/api/v1/webhooks/whatsapp", json=webhook_payload)
    assert res_status.status_code == 200
    assert res_status.json()["updated"] == 1

    # Verify log status updated to DELIVERED
    db.refresh(log)
    assert log.delivery_status == "DELIVERED"
    assert log.updated_at is not None
