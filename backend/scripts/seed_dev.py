import sys
import os
from datetime import datetime, timezone, timedelta

# Ensure app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, engine, Base
import app.models
from app.models.user import User, StudentProfile, TeacherProfile
from app.models.class_model import Class, ClassMember, ClassTeacher, ClassRepresentative
from app.models.poll import Poll, PollOption, Response
from app.models.enums import UserRole, UserStatus, PollStatus
from app.core.security import get_password_hash, generate_poll_public_id

def seed():
    from sqlalchemy import text
    with engine.connect() as conn:
        # Schema additions if not present
        try:
            conn.execute(text("ALTER TABLE student_profiles ADD COLUMN phone_number VARCHAR(20)"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE teacher_profiles ADD COLUMN phone_number VARCHAR(20)"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE class_members ADD COLUMN is_muted BOOLEAN DEFAULT 0"))
        except Exception:
            pass
        # Clean up legacy roles
        try:
            conn.execute(text("DELETE FROM users WHERE email LIKE '%admin%' OR role = 'ADMIN'"))
            conn.execute(text("UPDATE users SET role = 'FACULTY' WHERE role IN ('TEACHER', 'ADMIN')"))
            conn.execute(text("UPDATE users SET role = 'STUDENT' WHERE role = 'REP'"))
        except Exception:
            pass
        conn.commit()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("[*] Seeding ClassPoll production-oriented data...")

        # 2. Faculty Member
        teacher = db.query(User).filter(User.email == "kumar@college.edu").first()
        if not teacher:
            teacher = User(
                name="Prof. Kumar",
                email="kumar@college.edu",
                password_hash=get_password_hash("Teacher@123"),
                role=UserRole.FACULTY,
                status=UserStatus.ACTIVE,
                email_verified=True
            )
            db.add(teacher)
            db.flush()
            t_profile = TeacherProfile(
                user_id=teacher.id,
                employee_id="EMP001",
                department="AI & Data Science",
                phone_number="+919876543210"
            )
            db.add(t_profile)
            print("  [+] Faculty created: kumar@college.edu / Teacher@123")
        else:
            teacher.role = UserRole.FACULTY
            if teacher.teacher_profile:
                teacher.teacher_profile.phone_number = "+919876543210"

        # 3. Classes
        class_a = db.query(Class).filter(Class.name == "AIDS-A").first()
        if not class_a:
            class_a = Class(
                name="AIDS-A",
                department="AI & Data Science",
                year=2,
                section="A",
                academic_year="2026-27",
                class_code="ADSA27",
                is_active=True,
                allow_rep_poll_creation=True
            )
            db.add(class_a)
            db.flush()
            print("  [+] Class created: AIDS-A (Code: ADSA27)")

        class_b = db.query(Class).filter(Class.name == "AIDS-B").first()
        if not class_b:
            class_b = Class(
                name="AIDS-B",
                department="AI & Data Science",
                year=2,
                section="B",
                academic_year="2026-27",
                class_code="ADSB28",
                is_active=True,
                allow_rep_poll_creation=False
            )
            db.add(class_b)
            db.flush()
            print("  [+] Class created: AIDS-B (Code: ADSB28)")

        # Assign Faculty to AIDS-A
        teacher_assign = db.query(ClassTeacher).filter(
            ClassTeacher.class_id == class_a.id,
            ClassTeacher.teacher_id == teacher.id
        ).first()
        if not teacher_assign:
            teacher_assign = ClassTeacher(
                class_id=class_a.id,
                teacher_id=teacher.id,
                assigned_by=teacher.id,
                is_active=True
            )
            db.add(teacher_assign)
            print("  [+] Assigned Prof. Kumar to AIDS-A")

        # 4. Students (All have global role = STUDENT, Sanjay is class-level REP)
        student_data = [
            ("Sanjay G S", "sanjay@college.edu", "23AD006", "A", "+919876543211", True),  # Is REP for AIDS-A
            ("Arun M", "arun@college.edu", "23AD001", "A", "+919876543212", False),
            ("Bala K", "bala@college.edu", "23AD002", "A", "+919876543213", False),
            ("Rahul V", "rahul@college.edu", "23AD003", "A", "+919876543214", False),     # Pending response
            ("Vignesh S", "vignesh@college.edu", "23AD007", "A", "+919876543215", False), # Pending response
        ]

        created_students = {}
        for name, email, reg_no, sec, phone, is_rep in student_data:
            s_user = db.query(User).filter(User.email == email).first()
            if not s_user:
                s_user = User(
                    name=name,
                    email=email,
                    password_hash=get_password_hash("Student@123"),
                    role=UserRole.STUDENT, # Strictly STUDENT globally
                    status=UserStatus.ACTIVE,
                    email_verified=True
                )
                db.add(s_user)
                db.flush()
                s_profile = StudentProfile(
                    user_id=s_user.id,
                    register_number=reg_no,
                    department="AI & Data Science",
                    year=2,
                    section=sec,
                    phone_number=phone
                )
                db.add(s_profile)
                
                # Enroll in AIDS-A
                c_member = ClassMember(
                    class_id=class_a.id,
                    student_id=s_user.id,
                    is_active=True,
                    is_muted=False
                )
                db.add(c_member)

                if is_rep:
                    rep_assign = ClassRepresentative(
                        class_id=class_a.id,
                        student_id=s_user.id,
                        assigned_by=teacher.id,
                        is_active=True
                    )
                    db.add(rep_assign)
                print(f"  [+] Student created: {email} (Reg: {reg_no}, REP: {is_rep})")
            else:
                s_user.role = UserRole.STUDENT
                if s_user.student_profile:
                    s_user.student_profile.phone_number = phone
            created_students[email] = s_user

        # Divya in AIDS-B
        divya = db.query(User).filter(User.email == "divya@college.edu").first()
        if not divya:
            divya = User(
                name="Divya R",
                email="divya@college.edu",
                password_hash=get_password_hash("Student@123"),
                role=UserRole.STUDENT,
                status=UserStatus.ACTIVE,
                email_verified=True
            )
            db.add(divya)
            db.flush()
            d_profile = StudentProfile(
                user_id=divya.id,
                register_number="23AD050",
                department="AI & Data Science",
                year=2,
                section="B",
                phone_number="+919876543216"
            )
            db.add(d_profile)
            db.add(ClassMember(class_id=class_b.id, student_id=divya.id, is_active=True))
            print("  [+] Student created: divya@college.edu in AIDS-B")
        else:
            divya.role = UserRole.STUDENT
            if divya.student_profile:
                divya.student_profile.phone_number = "+919876543216"

        # Unenrolled student: Priya S (for faculty to search and add to class)
        priya = db.query(User).filter(User.email == "priya@college.edu").first()
        if not priya:
            priya = User(
                name="Priya S",
                email="priya@college.edu",
                password_hash=get_password_hash("Student@123"),
                role=UserRole.STUDENT,
                status=UserStatus.ACTIVE,
                email_verified=True
            )
            db.add(priya)
            db.flush()
            p_profile = StudentProfile(
                user_id=priya.id,
                register_number="23AD020",
                department="AI & Data Science",
                year=2,
                section="A",
                phone_number="+919876543220"
            )
            db.add(p_profile)
            print("  [+] Unenrolled student created: priya@college.edu (Reg: 23AD020)")

        # 5. Sample Poll in AIDS-A
        poll = db.query(Poll).filter(Poll.class_id == class_a.id).first()
        if not poll:
            poll = Poll(
                public_id="8F72KQX9",
                class_id=class_a.id,
                creator_id=teacher.id,
                question="Will you attend tomorrow's industrial visit?",
                deadline=datetime.now(timezone.utc) + timedelta(days=3),
                status=PollStatus.ACTIVE,
                allow_response_editing=True
            )
            db.add(poll)
            db.flush()

            opt_yes = PollOption(poll_id=poll.id, option_text="Yes", position=0)
            opt_no = PollOption(poll_id=poll.id, option_text="No", position=1)
            db.add(opt_yes)
            db.add(opt_no)
            db.flush()

            # Seed some responses
            # Arun: Yes, Bala: Yes, Sanjay: No
            # Rahul and Vignesh: Pending (NOT DONE)
            sanjay = created_students.get("sanjay@college.edu")
            arun = created_students.get("arun@college.edu")
            bala = created_students.get("bala@college.edu")

            if arun:
                db.add(Response(poll_id=poll.id, student_id=arun.id, option_id=opt_yes.id))
            if bala:
                db.add(Response(poll_id=poll.id, student_id=bala.id, option_id=opt_yes.id))
            if sanjay:
                db.add(Response(poll_id=poll.id, student_id=sanjay.id, option_id=opt_no.id))

            print("  [+] Sample poll created: 'Will you attend tomorrow's industrial visit?'")
            print("      Code: 8F72KQX9 | 3 Responses recorded (60% completion rate)")

        db.commit()
        print("\n[OK] Production institutional data seed complete!")
        print("--------------------------------------------------")
        print("Faculty: kumar@college.edu    / Teacher@123")
        print("REP:     sanjay@college.edu   / Student@123 (AIDS-A REP)")
        print("Student: arun@college.edu     / Student@123 (Voted Yes)")
        print("Student: rahul@college.edu    / Student@123 (Pending / Non-responder)")
        print("Student: priya@college.edu    / Student@123 (Unenrolled, Reg: 23AD020)")
        print("Class:   AIDS-A (Code: ADSA27)")
        print("--------------------------------------------------")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
