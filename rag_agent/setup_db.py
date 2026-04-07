"""
setup_db.py
Creates and populates the sample SQLite database used by the RAG agent.
Run once:  python setup_db.py
(The app also runs this automatically on first launch via retrieval_agent.py)
"""

import sqlite3
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH  = os.path.join(DATA_DIR, "company.db")

os.makedirs(DATA_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── Create tables ────────────────────────────────────────────────────────────
cur.executescript("""
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE employees (
    id            INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    role          TEXT,
    salary        REAL,
    hire_date     TEXT,
    remote        INTEGER  -- 1 = remote, 0 = on-site
);
""")

# ── Seed data ─────────────────────────────────────────────────────────────────
departments = [
    (1, "Engineering"),
    (2, "Marketing"),
    (3, "Finance"),
    (4, "HR"),
    (5, "Product"),
]

employees = [
    (1,  "Alice Johnson",  1, "Senior Engineer",       120000, "2019-03-15", 1),
    (2,  "Bob Smith",      1, "Software Engineer",      95000, "2021-07-01", 1),
    (3,  "Carol Lee",      1, "Engineering Manager",   140000, "2018-11-20", 0),
    (4,  "David Chen",     2, "Marketing Lead",         85000, "2020-05-10", 1),
    (5,  "Eva Patel",      2, "Content Strategist",     72000, "2022-02-28", 1),
    (6,  "Frank Müller",   3, "CFO",                   180000, "2017-09-01", 0),
    (7,  "Grace Kim",      3, "Financial Analyst",      78000, "2021-01-15", 0),
    (8,  "Henry Brown",    4, "HR Director",            95000, "2019-06-30", 0),
    (9,  "Iris Wang",      5, "Product Manager",       110000, "2020-10-12", 1),
    (10, "James Okafor",   1, "Junior Engineer",        68000, "2023-03-01", 1),
    (11, "Kate Nguyen",    5, "UX Designer",            82000, "2022-08-15", 1),
    (12, "Liam Torres",    2, "SEO Specialist",         65000, "2023-01-10", 1),
]

cur.executemany("INSERT INTO departments VALUES (?, ?)", departments)
cur.executemany("INSERT INTO employees   VALUES (?, ?, ?, ?, ?, ?, ?)", employees)

conn.commit()
conn.close()
print(f"✅ Database created at {DB_PATH}")


if __name__ == "__main__":
    pass  # already ran above
