import os
import sys
import sqlite3
import shutil
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.security import get_password_hash

FINAL_POLL_DB = r"c:\Users\SANJAY\Desktop\classSync\finalpolldb.db"
ROOT_TEST_DB = r"c:\Users\SANJAY\Desktop\classSync\test_classpoll.db"
BACKEND_TEST_DB = r"c:\Users\SANJAY\Desktop\classSync\backend\test_classpoll.db"
BACKEND_MAIN_DB = r"c:\Users\SANJAY\Desktop\classSync\backend\classpoll.db"
ROOT_MAIN_DB = r"c:\Users\SANJAY\Desktop\classSync\classpoll.db"

PASSWORD_PLAIN = "Mcet@12345"

def load_source_students():
    source_db = FINAL_POLL_DB
    if not os.path.exists(source_db):
        raise FileNotFoundError(f"Source DB {source_db} not found")
    
    conn = sqlite3.connect(source_db)
    cur = conn.cursor()
    rows = cur.execute('SELECT "Name", "Roll No", "Email ID", "WhatsApp Number" FROM students ORDER BY "Roll No", "Name"').fetchall()
    conn.close()

    students = []
    for name, roll, email, phone in rows:
        name = name.strip()
        roll = roll.strip().upper()
        email = email.strip().lower()
        phone_str = f"+91{phone}" if phone else None

        # Resolve typos in roll/email numbers so every student is unique:
        # Pirajin P (between Pavanika 064 and Ponmadasamy 066) -> 065
        if name == "Pirajin P" and roll == "727625BAD064":
            roll = "727625BAD065"
            email = "727625bad065@mcet.in"
        # Pradeep S (between Pooja 067 and Pragatheesh 069) -> 068
        elif name == "Pradeep S" and roll == "727625BAD066":
            roll = "727625BAD068"
            email = "727625bad068@mcet.in"

        students.append({
            "name": name,
            "roll": roll,
            "email": email,
            "phone": phone_str
        })
    
    return students

def update_database(db_path, students):
    print(f"\n[*] Processing database: {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    now_iso = datetime.now(timezone.utc).isoformat()
    pw_hash = get_password_hash(PASSWORD_PLAIN)

    # 1. Clear any existing active sessions/tokens/responses
    cur.execute("DELETE FROM refresh_tokens")
    cur.execute("DELETE FROM audit_logs")
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM message_logs")
    cur.execute("UPDATE users SET last_login_at = NULL")

    # 2. Ensure Class 1 (AIDS-A) exists
    cur.execute("SELECT id FROM classes WHERE id = 1")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO classes (id, name, department, year, section, academic_year, class_code, is_active, allow_rep_poll_creation, created_at, updated_at)
            VALUES (1, 'AIDS-A', 'AI & Data Science', 2, 'A', '2026-27', 'ADSA27', 1, 1, ?, ?)
        """, (now_iso, now_iso))

    # Ensure Class 2 exists: AIDS-B
    cur.execute("SELECT id FROM classes WHERE name = 'AIDS-B' OR id = 2")
    c_row = cur.fetchone()
    if c_row:
        class_2_id = c_row[0]
        cur.execute("UPDATE classes SET name = 'AIDS-B', section = 'B', allow_rep_poll_creation = 1, is_active = 1 WHERE id = ?", (class_2_id,))
    else:
        cur.execute("""
            INSERT INTO classes (id, name, department, year, section, academic_year, class_code, is_active, allow_rep_poll_creation, created_at, updated_at)
            VALUES (2, 'AIDS-B', 'AI & Data Science', 2, 'B', '2026-27', 'ADSB28', 1, 1, ?, ?)
        """, (now_iso, now_iso))
        class_2_id = 2

    # 3. Ensure Faculty (Prof. Kumar) exists and is assigned as teacher for both AIDS-A and AIDS-B
    cur.execute("SELECT id FROM users WHERE email = 'kumar@college.edu'")
    f_row = cur.fetchone()
    if f_row:
        fid = f_row[0]
        cur.execute("UPDATE users SET password_hash = ?, last_login_at = NULL WHERE id = ?", (pw_hash, fid))
    else:
        cur.execute("INSERT INTO users (name, email, password_hash, role, status, email_verified, created_at) VALUES ('Prof. Kumar', 'kumar@college.edu', ?, 'FACULTY', 'ACTIVE', 1, ?)", (pw_hash, now_iso))
        fid = cur.lastrowid
        cur.execute("INSERT INTO teacher_profiles (user_id, employee_id, department, phone_number) VALUES (?, 'EMP001', 'AI & Data Science', '+919876543210')", (fid,))

    # Assign faculty to AIDS-A (Class 1) and AIDS-B (Class 2)
    for cid in [1, class_2_id]:
        cur.execute("SELECT id FROM class_teachers WHERE class_id = ? AND teacher_id = ?", (cid, fid))
        if not cur.fetchone():
            cur.execute("INSERT INTO class_teachers (class_id, teacher_id, assigned_by, assigned_at, is_active) VALUES (?, ?, ?, ?, 1)", (cid, fid, fid, now_iso))

    # 4. Clear old class memberships and class representative assignments
    cur.execute("DELETE FROM class_members")
    cur.execute("DELETE FROM class_representatives")

    rep_user_id = None

    print(f"  [+] Registering {len(students)} students into AIDS-B (Section B, Class ID {class_2_id})...")
    for s in students:
        cur.execute("SELECT id FROM users WHERE email = ?", (s["email"],))
        u_row = cur.fetchone()

        if u_row:
            uid = u_row[0]
            cur.execute("""
                UPDATE users 
                SET name = ?, password_hash = ?, role = 'STUDENT', status = 'ACTIVE', email_verified = 1, last_login_at = NULL, updated_at = ?
                WHERE id = ?
            """, (s["name"], pw_hash, now_iso, uid))
            cur.execute("""
                UPDATE student_profiles
                SET register_number = ?, department = 'AI & Data Science', year = 2, section = 'B', phone_number = ?, updated_at = ?
                WHERE user_id = ?
            """, (s["roll"], s["phone"], now_iso, uid))
        else:
            cur.execute("""
                INSERT INTO users (name, email, password_hash, role, status, email_verified, created_at, updated_at)
                VALUES (?, ?, ?, 'STUDENT', 'ACTIVE', 1, ?, ?)
            """, (s["name"], s["email"], pw_hash, now_iso, now_iso))
            uid = cur.lastrowid
            cur.execute("""
                INSERT INTO student_profiles (user_id, register_number, department, year, section, phone_number, created_at, updated_at)
                VALUES (?, ?, 'AI & Data Science', 2, 'B', ?, ?, ?)
            """, (uid, s["roll"], s["phone"], now_iso, now_iso))

        # Add membership in AIDS-B
        cur.execute("INSERT INTO class_members (class_id, student_id, joined_at, is_active, is_muted) VALUES (?, ?, ?, 1, 0)", (class_2_id, uid, now_iso))

        if "sanjay" in s["name"].lower() or s["roll"] == "727625BAD091":
            rep_user_id = uid

    # Assign Sanjay GS as Class Representative for AIDS-B
    if rep_user_id:
        cur.execute("INSERT INTO class_representatives (class_id, student_id, assigned_by, assigned_at, is_active) VALUES (?, ?, ?, ?, 1)", (class_2_id, rep_user_id, fid, now_iso))
        print(f"  [+] Assigned Sanjay GS (User ID {rep_user_id}) as Class Representative for AIDS-B.")

    # 5. Ensure AIDS-B has an active poll
    cur.execute("SELECT id FROM polls WHERE class_id = ?", (class_2_id,))
    poll_row = cur.fetchone()
    if not poll_row:
        cur.execute("""
            INSERT INTO polls (public_id, class_id, creator_id, question, deadline, status, allow_response_editing, created_at, updated_at)
            VALUES ('ADSBPOLL1', ?, ?, 'Will you attend the upcoming workshop on Generative AI?', '2026-09-30 23:59:59', 'ACTIVE', 1, ?, ?)
        """, (class_2_id, fid, now_iso, now_iso))
        poll_id = cur.lastrowid
        cur.execute("INSERT INTO poll_options (poll_id, option_text, position) VALUES (?, 'Yes, attending', 0)", (poll_id,))
        cur.execute("INSERT INTO poll_options (poll_id, option_text, position) VALUES (?, 'No, cannot attend', 1)", (poll_id,))
        cur.execute("INSERT INTO poll_options (poll_id, option_text, position) VALUES (?, 'Need more info', 2)", (poll_id,))
        print(f"  [+] Created active poll in AIDS-B (Poll ID {poll_id}).")

    conn.commit()

    total_b_members = cur.execute("SELECT count(*) FROM class_members WHERE class_id = ?", (class_2_id,)).fetchone()[0]
    total_a_members = cur.execute("SELECT count(*) FROM class_members WHERE class_id = 1").fetchone()[0]
    print(f"  [OK] Total members in AIDS-B: {total_b_members}, in AIDS-A: {total_a_members}")
    conn.close()

def sync_all():
    students = load_source_students()
    print(f"Loaded {len(students)} students from source data.")

    # Update backend main classpoll.db
    update_database(BACKEND_MAIN_DB, students)

    # Sync to root classpoll.db, root test_classpoll.db, and backend test_classpoll.db
    for target in [ROOT_MAIN_DB, ROOT_TEST_DB, BACKEND_TEST_DB]:
        print(f"[*] Copying {BACKEND_MAIN_DB} to {target}...")
        shutil.copyfile(BACKEND_MAIN_DB, target)

    # Also keep the students table in test_classpoll.db
    fconn = sqlite3.connect(FINAL_POLL_DB)
    fcur = fconn.cursor()
    frows = fcur.execute('SELECT "Name", "Roll No", "Email ID", "WhatsApp Number" FROM students').fetchall()
    fconn.close()

    for db_path in [ROOT_TEST_DB, BACKEND_TEST_DB]:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                "Name" TEXT,
                "Roll No" TEXT,
                "Email ID" TEXT,
                "WhatsApp Number" INTEGER
            )
        """)
        cur.execute("DELETE FROM students")
        for r in frows:
            cur.execute('INSERT INTO students ("Name", "Roll No", "Email ID", "WhatsApp Number") VALUES (?, ?, ?, ?)', r)
        conn.commit()
        conn.close()

    print("\n[COMPLETE] Successfully registered all students into AIDS-B across all databases!")

if __name__ == "__main__":
    sync_all()
