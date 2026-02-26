"""
homework.py — Homework: Build a mini "Gradebook DB" using raw SQL (prep for ORM)

Run:
  python homework.py

Deliverables:
  1) Implement the TODO functions.
  2) Demonstrate your work in main() by:
     - creating the schema
     - adding sample data (at least 3 students, 3 assignments, 6 grades)
     - printing:
        a) all students
        b) grade report per student (JOIN)
        c) class leaderboard by average percent (aggregation)

Rules:
  - Use parameterized queries (? placeholders) for all SQL that includes variables.
  - Keep your schema normalized:
      students, assignments, grades (with foreign keys)
  - Do not store lists inside a single column (no JSON arrays for grades).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Iterable

DB_PATH = Path("homework_gradebook.db")


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def reset_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()


def create_schema(conn: sqlite3.Connection) -> None:
    """
    Create these tables:

    students:
      - id (PK)
      - name (required)
      - email (required, UNIQUE)

    assignments:
      - id (PK)
      - title (required)
      - max_points (required, > 0)

    grades:
      - id (PK)
      - student_id (FK -> students.id)
      - assignment_id (FK -> assignments.id)
      - score (required, >= 0)
      - UNIQUE(student_id, assignment_id) to prevent duplicates
    """
    conn.execute("""
                 CREATE TABLE students (
                                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                                           name TEXT NOT NULL,
                                           email TEXT NOT NULL UNIQUE
                 )
                 """)
    conn.execute("""
                 CREATE TABLE assignments (
                                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                                              title TEXT NOT NULL,
                                              max_points INTEGER NOT NULL CHECK (max_points > 0)
                 )
                 """)
    conn.execute("""
                 CREATE TABLE grades (
                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                         student_id INTEGER NOT NULL,
                                         assignment_id INTEGER NOT NULL,
                                         score INTEGER NOT NULL CHECK (score >= 0),
                                         FOREIGN KEY(student_id) REFERENCES students(id),
                                         FOREIGN KEY(assignment_id) REFERENCES assignments(id),
                                         UNIQUE(student_id, assignment_id)
                 )
                 """)


def add_student(conn: sqlite3.Connection, name: str, email: str) -> int:
    """Insert into students and return new id."""
    cur = conn.execute(
        "INSERT INTO students (name, email) VALUES (?, ?)",
        (name, email)
    )
    return cur.lastrowid


def add_assignment(conn: sqlite3.Connection, title: str, max_points: int) -> int:
    """Insert into assignments and return new id."""
    cur = conn.execute(
        "INSERT INTO assignments (title, max_points) VALUES (?, ?)",
        (title, max_points)
    )
    return cur.lastrowid


def record_grade(conn: sqlite3.Connection, student_id: int, assignment_id: int, score: int) -> int:
    """Insert into grades and return new id."""
    cur = conn.execute(
        "INSERT INTO grades (student_id, assignment_id, score) VALUES (?, ?, ?)",
        (student_id, assignment_id, score)
    )
    return cur.lastrowid


def list_students(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return all students ordered by name."""
    cur = conn.execute(
        "SELECT * FROM students ORDER BY name"
    )
    return cur.fetchall()


def student_grade_report(conn: sqlite3.Connection, student_id: int) -> list[sqlite3.Row]:
    """
    Return rows for one student with:
      assignment_title, score, max_points, percent

    Hint:
      percent = ROUND(1.0 * score / max_points * 100, 1)
    """
    cur = conn.execute("""
                       SELECT
                           assignments.title AS assignment_title,
                           grades.score,
                           assignments.max_points,
                           ROUND(1.0 * grades.score / assignments.max_points * 100, 1) AS percent
                       FROM grades
                                JOIN assignments ON grades.assignment_id = assignments.id
                       WHERE grades.student_id = ?
                       """, (student_id,))
    return cur.fetchall()


def leaderboard(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """
    Return rows:
      student_name, avg_percent

    avg_percent should average the per-assignment percent for each student.
    """
    cur = conn.execute("""
                       SELECT
                           students.name AS student_name,
                           ROUND(AVG(1.0 * grades.score / assignments.max_points * 100), 1) AS avg_percent
                       FROM grades
                                JOIN students ON grades.student_id = students.id
                                JOIN assignments ON grades.assignment_id = assignments.id
                       GROUP BY students.id
                       ORDER BY avg_percent DESC
                       """)
    return cur.fetchall()


def print_rows(title: str, rows: Iterable[sqlite3.Row]) -> None:
    rows = list(rows)
    print("\n" + "=" * 80)
    print(title)
    print("-" * 80)
    if not rows:
        print("(no rows)")
        return
    cols = rows[0].keys()
    widths = {c: max(len(c), max(len(str(r[c])) for r in rows)) for c in cols}
    print(" | ".join(c.ljust(widths[c]) for c in cols))
    print("-+-".join("-" * widths[c] for c in cols))
    for r in rows:
        print(" | ".join(str(r[c]).ljust(widths[c]) for c in cols))


def main() -> None:
    reset_db()
    conn = connect()
    try:
        create_schema(conn)
        conn.commit()


        s_rivka = add_student(conn, "Rivka", "rivka@example.com")
        s_esther = add_student(conn, "Esther", "esther@example.com")
        s_leah = add_student(conn, "Leah", "leah@example.com")

        a_q1 = add_assignment(conn, "Quiz 1", 10)
        a_hw1 = add_assignment(conn, "Homework 1", 100)
        a_mid = add_assignment(conn, "Midterm", 200)

        record_grade(conn, s_rivka, a_q1, 9)
        record_grade(conn, s_rivka, a_hw1, 95)

        record_grade(conn, s_esther, a_q1, 7)
        record_grade(conn, s_esther, a_hw1, 88)

        record_grade(conn, s_leah, a_q1, 10)
        record_grade(conn, s_leah, a_hw1, 92)
        record_grade(conn, s_leah, a_mid, 180)

        conn.commit()



        print_rows("All students", list_students(conn))

        for s in list_students(conn):
            rows = student_grade_report(conn, s["id"])
            print_rows(f"Grade report: {s['name']}", rows)

        print_rows("Leaderboard by average percent", leaderboard(conn))


        print("Homework starter created. Implement TODOs, then uncomment the demo/report blocks in main().")
    finally:
        conn.close()


if __name__ == "__main__":
    main()