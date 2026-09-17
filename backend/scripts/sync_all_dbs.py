import shutil
import sqlite3

FINAL_POLL_DB = r"c:\Users\SANJAY\Desktop\classSync\finalpolldb.db"
TARGETS = [
    r"c:\Users\SANJAY\Desktop\classSync\classpoll.db",
    r"c:\Users\SANJAY\Desktop\classSync\test_classpoll.db",
    r"c:\Users\SANJAY\Desktop\classSync\backend\test_classpoll.db",
    r"c:\Users\SANJAY\Desktop\classSync\backend\classpoll.db",
]

# Ensure backend/classpoll.db is the golden source for application tables
golden_src = r"c:\Users\SANJAY\Desktop\classSync\backend\classpoll.db"

# Copy golden source to all targets
for target in [r"c:\Users\SANJAY\Desktop\classSync\classpoll.db", r"c:\Users\SANJAY\Desktop\classSync\test_classpoll.db", r"c:\Users\SANJAY\Desktop\classSync\backend\test_classpoll.db"]:
    shutil.copyfile(golden_src, target)

# Ensure students table from finalpolldb.db is present in test_classpoll.db files
fconn = sqlite3.connect(FINAL_POLL_DB)
fcur = fconn.cursor()
frows = fcur.execute('SELECT "Name", "Roll No", "Email ID", "WhatsApp Number" FROM students').fetchall()
fconn.close()

for db_path in [r"c:\Users\SANJAY\Desktop\classSync\test_classpoll.db", r"c:\Users\SANJAY\Desktop\classSync\backend\test_classpoll.db"]:
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

# Verify state across all 4 databases
print("\n=== VERIFICATION ACROSS ALL DATABASES ===")
for db_path in TARGETS:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    users_cnt = cur.execute("SELECT count(*) FROM users").fetchone()[0]
    students_prof_cnt = cur.execute("SELECT count(*) FROM student_profiles").fetchone()[0]
    refresh_cnt = cur.execute("SELECT count(*) FROM refresh_tokens").fetchone()[0]
    audit_cnt = cur.execute("SELECT count(*) FROM audit_logs WHERE action = 'LOGIN'").fetchone()[0]
    last_logins_cnt = cur.execute("SELECT count(*) FROM users WHERE last_login_at IS NOT NULL").fetchone()[0]
    has_students_tbl = cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='students'").fetchone()[0]
    raw_students = cur.execute("SELECT count(*) FROM students").fetchone()[0] if has_students_tbl else 0
    print(f"DB: {db_path}")
    print(f"  Users: {users_cnt} | Student Profiles: {students_prof_cnt} | Raw students rows: {raw_students}")
    print(f"  Active Refresh Tokens: {refresh_cnt} | Login Audit Logs: {audit_cnt} | Non-null last_login: {last_logins_cnt}")
    conn.close()
