import os
import sys
import shutil
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timezone, timedelta
from app.core.security import get_password_hash

DB_MAIN = "classpoll.db"
DB_TEST = "test_classpoll.db"

def clean_database(db_path):
    print(f"[*] Processing database: {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Identify previous extraneous/test students (non @college.edu)
    cur.execute("SELECT id, name, email FROM users WHERE role = 'STUDENT' AND email NOT LIKE '%@college.edu'")
    dirty_users = cur.fetchall()
    print(f"  [-] Found {len(dirty_users)} non-institutional student accounts to remove:")
    for uid, uname, uemail in dirty_users:
        print(f"      Removing user ID {uid}: {uname} ({uemail})")
        cur.execute("DELETE FROM student_profiles WHERE user_id = ?", (uid,))
        cur.execute("DELETE FROM class_members WHERE student_id = ?", (uid,))
        cur.execute("DELETE FROM class_representatives WHERE student_id = ?", (uid,))
        cur.execute("DELETE FROM responses WHERE student_id = ?", (uid,))
        cur.execute("DELETE FROM message_logs WHERE student_id = ?", (uid,))
        cur.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (uid,))
        cur.execute("DELETE FROM users WHERE id = ?", (uid,))

    # 2. Reset previous student poll responses & message logs so polls are fresh
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM message_logs")
    print("  [-] Cleared previous student responses and message logs.")

    # 3. Ensure institutional users exist with clean passwords and college emails
    faculty_pw = get_password_hash("Teacher@123")
    student_pw = get_password_hash("Student@123")

    # Faculty
    cur.execute("SELECT id FROM users WHERE email = 'kumar@college.edu'")
    f_row = cur.fetchone()
    if f_row:
        cur.execute("UPDATE users SET name = 'Prof. Kumar', password_hash = ?, role = 'FACULTY', status = 'ACTIVE' WHERE id = ?", (faculty_pw, f_row[0]))
    else:
        cur.execute("INSERT INTO users (name, email, password_hash, role, status, email_verified, created_at) VALUES ('Prof. Kumar', 'kumar@college.edu', ?, 'FACULTY', 'ACTIVE', 1, ?)", (faculty_pw, datetime.now(timezone.utc).isoformat()))
        fid = cur.lastrowid
        cur.execute("INSERT INTO teacher_profiles (user_id, employee_id, department, phone_number) VALUES (?, 'EMP001', 'AI & Data Science', '+919876543210')", (fid,))

    # Institutional Students
    students = [
        ("Sanjay G S", "sanjay@college.edu", "23AD006", "A", "+919876543211", True),
        ("Arun M", "arun@college.edu", "23AD001", "A", "+919876543212", False),
        ("Bala K", "bala@college.edu", "23AD002", "A", "+919876543213", False),
        ("Rahul V", "rahul@college.edu", "23AD003", "A", "+919876543214", False),
        ("Vignesh S", "vignesh@college.edu", "23AD007", "A", "+919876543215", False),
        ("Divya R", "divya@college.edu", "23AD050", "B", "+919876543216", False),
        ("Priya S", "priya@college.edu", "23AD020", "A", "+919876543220", False),
    ]

    for name, email, reg_no, sec, phone, is_rep in students:
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        s_row = cur.fetchone()
        if s_row:
            uid = s_row[0]
            cur.execute("UPDATE users SET name = ?, password_hash = ?, role = 'STUDENT', status = 'ACTIVE' WHERE id = ?", (name, student_pw, uid))
            cur.execute("UPDATE student_profiles SET register_number = ?, section = ?, phone_number = ? WHERE user_id = ?", (reg_no, sec, phone, uid))
        else:
            cur.execute("INSERT INTO users (name, email, password_hash, role, status, email_verified, created_at) VALUES (?, ?, ?, 'STUDENT', 'ACTIVE', 1, ?)", (name, email, student_pw, datetime.now(timezone.utc).isoformat()))
            uid = cur.lastrowid
            cur.execute("INSERT INTO student_profiles (user_id, register_number, department, year, section, phone_number) VALUES (?, ?, 'AI & Data Science', 2, ?, ?)", (uid, reg_no, sec, phone))

    conn.commit()

    # Print summary of remaining users
    cur.execute("SELECT id, name, email, role FROM users ORDER BY role, name")
    all_users = cur.fetchall()
    print(f"  [+] Active institutional users in {db_path} ({len(all_users)} total):")
    for u in all_users:
        print(f"      - {u[1]} ({u[2]}) | Role: {u[3]}")

    conn.close()

if __name__ == "__main__":
    clean_database(DB_MAIN)
    # Replicate main clean database to test_classpoll.db
    print(f"[*] Copying clean {DB_MAIN} to {DB_TEST}...")
    shutil.copyfile(DB_MAIN, DB_TEST)
    clean_database(DB_TEST)
    print("\n[SUCCESS] Both classpoll.db and test_classpoll.db are cleaned and synchronized!")
