"""
database.py
All PostgreSQL logic for the Crime Database Management System.
The Streamlit UI (app.py) only calls the functions in this file.
"""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2 import errors
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "crime_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

GENDERS = ["Male", "Female", "Other"]
CASE_STATUSES = ["Open", "Under Investigation", "Solved", "Closed"]
CRIME_TYPES = ["Theft", "Robbery", "Assault", "Fraud", "Burglary",
               "Murder", "Kidnapping", "Cyber Crime", "Other"]


# ERROR HANDLING
class DatabaseError(Exception):
    """Friendly error that the UI can show directly to the user."""


def _friendly_message(e):
    """Convert a raw psycopg2 error into a readable message."""
    if isinstance(e, errors.UniqueViolation):
        return "Duplicate value: a record with the same unique value (e.g. case number) already exists."
    if isinstance(e, errors.ForeignKeyViolation):
        if "still referenced" in str(e):
            return ("Cannot delete: this record is linked to other records "
                    "(crimes or cases). Delete or reassign those first.")
        return "Invalid reference: the selected criminal / victim / officer / crime does not exist."
    if isinstance(e, errors.CheckViolation):
        return "Invalid value: please check gender, age or status."
    if isinstance(e, errors.NotNullViolation):
        return "A required field is empty."
    if isinstance(e, (errors.InvalidTextRepresentation,
                      errors.InvalidDatetimeFormat,
                      errors.NumericValueOutOfRange)):
        return "Invalid input format (check dates and numbers)."
    if isinstance(e, psycopg2.OperationalError):
        return "Database connection problem. Is PostgreSQL running?"
    return f"Database error: {e}"


def _clean(value):
    """Strip text; turn empty strings into None so they are stored as NULL."""
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value


def _require(value, field_name):
    """Make sure a required text field is not empty."""
    value = _clean(value)
    if value is None:
        raise DatabaseError(f"{field_name} is required.")
    return value


# CONNECTION + TRANSACTION HELPERS
def get_connection():
    """Open a new PostgreSQL connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        raise DatabaseError(
            "Could not connect to PostgreSQL. Check that the server is running "
            "and that host, port, database name, user and password in "
            "database.py are correct."
        ) from e


@contextmanager
def get_cursor(commit=False):
    """
    Gives a cursor inside a transaction.
    - commit=True  : commits if everything succeeds
    - any error    : rolls back, so nothing is half-saved
    The connection is always closed at the end.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        yield cur
        if commit:
            conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(_friendly_message(e)) from e
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query, params=None):
    """Run a SELECT and return a list of dictionaries."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def fetch_one(query, params=None):
    """Run a SELECT and return one dictionary (or None)."""
    with get_cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def execute_write(query, params=None):
    """
    Run INSERT / UPDATE / DELETE inside a transaction.
    Returns the new id if the query has RETURNING, otherwise the row count.
    """
    with get_cursor(commit=True) as cur:
        cur.execute(query, params)
        if cur.description:          
            return list(cur.fetchone().values())[0]
        return cur.rowcount


def test_connection():
    """Returns True if the database can be reached."""
    fetch_one("SELECT 1 AS ok")
    return True


def _like(keyword):
    """Build a pattern for ILIKE searches."""
    return f"%{keyword.strip()}%"


# CRIMINALS
def add_criminal(name, date_of_birth, gender, address, phone):
    name = _require(name, "Name")
    return execute_write(
        """INSERT INTO criminals (name, date_of_birth, gender, address, phone)
           VALUES (%s, %s, %s, %s, %s) RETURNING criminal_id""",
        (name, date_of_birth, _clean(gender), _clean(address), _clean(phone)),
    )


def get_all_criminals():
    return fetch_all("SELECT * FROM criminals ORDER BY criminal_id")


def get_criminal(criminal_id):
    return fetch_one("SELECT * FROM criminals WHERE criminal_id = %s", (criminal_id,))


def search_criminals(keyword):
    p = _like(keyword)
    return fetch_all(
        """SELECT * FROM criminals
           WHERE name ILIKE %s OR address ILIKE %s OR phone ILIKE %s
              OR CAST(criminal_id AS TEXT) = %s
           ORDER BY criminal_id""",
        (p, p, p, keyword.strip()),
    )


def update_criminal(criminal_id, name, date_of_birth, gender, address, phone):
    name = _require(name, "Name")
    return execute_write(
        """UPDATE criminals
           SET name = %s, date_of_birth = %s, gender = %s, address = %s, phone = %s
           WHERE criminal_id = %s""",
        (name, date_of_birth, _clean(gender), _clean(address), _clean(phone), criminal_id),
    )


def delete_criminal(criminal_id):
    return execute_write("DELETE FROM criminals WHERE criminal_id = %s", (criminal_id,))


# VICTIMS
def add_victim(name, age, gender, address, phone):
    name = _require(name, "Name")
    return execute_write(
        """INSERT INTO victims (name, age, gender, address, phone)
           VALUES (%s, %s, %s, %s, %s) RETURNING victim_id""",
        (name, age, _clean(gender), _clean(address), _clean(phone)),
    )


def get_all_victims():
    return fetch_all("SELECT * FROM victims ORDER BY victim_id")


def get_victim(victim_id):
    return fetch_one("SELECT * FROM victims WHERE victim_id = %s", (victim_id,))


def search_victims(keyword):
    p = _like(keyword)
    return fetch_all(
        """SELECT * FROM victims
           WHERE name ILIKE %s OR address ILIKE %s OR phone ILIKE %s
              OR CAST(victim_id AS TEXT) = %s
           ORDER BY victim_id""",
        (p, p, p, keyword.strip()),
    )


def update_victim(victim_id, name, age, gender, address, phone):
    name = _require(name, "Name")
    return execute_write(
        """UPDATE victims
           SET name = %s, age = %s, gender = %s, address = %s, phone = %s
           WHERE victim_id = %s""",
        (name, age, _clean(gender), _clean(address), _clean(phone), victim_id),
    )


def delete_victim(victim_id):
    return execute_write("DELETE FROM victims WHERE victim_id = %s", (victim_id,))


# POLICE OFFICERS
def add_officer(name, rank, phone, police_station):
    name = _require(name, "Name")
    rank = _require(rank, "Rank")
    police_station = _require(police_station, "Police station")
    return execute_write(
        """INSERT INTO police_officers (name, rank, phone, police_station)
           VALUES (%s, %s, %s, %s) RETURNING officer_id""",
        (name, rank, _clean(phone), police_station),
    )


def get_all_officers():
    return fetch_all("SELECT * FROM police_officers ORDER BY officer_id")


def get_officer(officer_id):
    return fetch_one("SELECT * FROM police_officers WHERE officer_id = %s", (officer_id,))


def search_officers(keyword):
    p = _like(keyword)
    return fetch_all(
        """SELECT * FROM police_officers
           WHERE name ILIKE %s OR rank ILIKE %s OR police_station ILIKE %s
              OR phone ILIKE %s OR CAST(officer_id AS TEXT) = %s
           ORDER BY officer_id""",
        (p, p, p, p, keyword.strip()),
    )


def update_officer(officer_id, name, rank, phone, police_station):
    name = _require(name, "Name")
    rank = _require(rank, "Rank")
    police_station = _require(police_station, "Police station")
    return execute_write(
        """UPDATE police_officers
           SET name = %s, rank = %s, phone = %s, police_station = %s
           WHERE officer_id = %s""",
        (name, rank, _clean(phone), police_station, officer_id),
    )


def delete_officer(officer_id):
    return execute_write("DELETE FROM police_officers WHERE officer_id = %s", (officer_id,))


def reassign_officer_work(old_officer_id, new_officer_id):
    """
    TRANSACTION EXAMPLE: moves all crimes AND cases from one officer to another.
    Both UPDATEs succeed together or neither is saved.
    Returns (crimes_moved, cases_moved).
    """
    if old_officer_id == new_officer_id:
        raise DatabaseError("Please choose two different officers.")
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE crimes SET officer_id = %s WHERE officer_id = %s",
                    (new_officer_id, old_officer_id))
        crimes_moved = cur.rowcount
        cur.execute("UPDATE cases SET officer_id = %s WHERE officer_id = %s",
                    (new_officer_id, old_officer_id))
        cases_moved = cur.rowcount
    return crimes_moved, cases_moved


# DROPDOWN OPTIONS  (each returns [{'id': .., 'label': ..}, ...])
def get_criminal_options():
    return fetch_all(
        """SELECT criminal_id AS id, CONCAT(criminal_id, ' - ', name) AS label
           FROM criminals ORDER BY name"""
    )


def get_victim_options():
    return fetch_all(
        """SELECT victim_id AS id, CONCAT(victim_id, ' - ', name) AS label
           FROM victims ORDER BY name"""
    )


def get_officer_options():
    return fetch_all(
        """SELECT officer_id AS id,
                  CONCAT(officer_id, ' - ', name, ' (', rank, ')') AS label
           FROM police_officers ORDER BY name"""
    )


def get_crime_options():
    return fetch_all(
        """SELECT crime_id AS id,
                  CONCAT(crime_id, ' - ', crime_type, ' on ', crime_date,
                         ' (', location, ')') AS label
           FROM crimes ORDER BY crime_id"""
    )


# CRIMES
_CRIME_SELECT = """
    SELECT c.crime_id, c.crime_type, c.crime_date, c.location, c.description,
           c.criminal_id, cr.name AS criminal_name,
           c.victim_id,   v.name  AS victim_name,
           c.officer_id,  o.name  AS officer_name
    FROM crimes c
    LEFT JOIN criminals cr       ON c.criminal_id = cr.criminal_id
    INNER JOIN victims v         ON c.victim_id   = v.victim_id
    INNER JOIN police_officers o ON c.officer_id  = o.officer_id
"""


def add_crime(crime_type, crime_date, location, description,
              criminal_id, victim_id, officer_id):
    crime_type = _require(crime_type, "Crime type")
    location = _require(location, "Location")
    return execute_write(
        """INSERT INTO crimes (crime_type, crime_date, location, description,
                               criminal_id, victim_id, officer_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING crime_id""",
        (crime_type, crime_date, location, _clean(description),
         criminal_id, victim_id, officer_id),
    )


def get_all_crimes():
    return fetch_all(_CRIME_SELECT + " ORDER BY c.crime_date DESC, c.crime_id DESC")


def get_crime(crime_id):
    return fetch_one("SELECT * FROM crimes WHERE crime_id = %s", (crime_id,))


def search_crimes(keyword):
    p = _like(keyword)
    return fetch_all(
        _CRIME_SELECT + """
        WHERE c.crime_type ILIKE %s OR c.location ILIKE %s OR c.description ILIKE %s
           OR cr.name ILIKE %s OR v.name ILIKE %s OR o.name ILIKE %s
           OR CAST(c.crime_id AS TEXT) = %s
        ORDER BY c.crime_date DESC, c.crime_id DESC""",
        (p, p, p, p, p, p, keyword.strip()),
    )


def update_crime(crime_id, crime_type, crime_date, location, description,
                 criminal_id, victim_id, officer_id):
    crime_type = _require(crime_type, "Crime type")
    location = _require(location, "Location")
    return execute_write(
        """UPDATE crimes
           SET crime_type = %s, crime_date = %s, location = %s, description = %s,
               criminal_id = %s, victim_id = %s, officer_id = %s
           WHERE crime_id = %s""",
        (crime_type, crime_date, location, _clean(description),
         criminal_id, victim_id, officer_id, crime_id),
    )


def delete_crime(crime_id):
    """Also deletes the crime's cases (ON DELETE CASCADE in schema.sql)."""
    return execute_write("DELETE FROM crimes WHERE crime_id = %s", (crime_id,))


# CASES
_CASE_SELECT = """
    SELECT cs.case_id, cs.case_number, cs.crime_id, c.crime_type,
           cs.officer_id, o.name AS officer_name,
           cs.filing_date, cs.status, cs.description
    FROM cases cs
    INNER JOIN crimes c          ON cs.crime_id   = c.crime_id
    INNER JOIN police_officers o ON cs.officer_id = o.officer_id
"""


def add_case(case_number, crime_id, officer_id, filing_date, status, description):
    case_number = _require(case_number, "Case number")
    if status not in CASE_STATUSES:
        raise DatabaseError("Invalid case status.")
    return execute_write(
        """INSERT INTO cases (case_number, crime_id, officer_id, filing_date,
                             status, description)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING case_id""",
        (case_number, crime_id, officer_id, filing_date, status, _clean(description)),
    )


def get_all_cases():
    return fetch_all(_CASE_SELECT + " ORDER BY cs.filing_date DESC, cs.case_id DESC")


def get_case(case_id):
    return fetch_one("SELECT * FROM cases WHERE case_id = %s", (case_id,))


def search_cases(keyword):
    p = _like(keyword)
    return fetch_all(
        _CASE_SELECT + """
        WHERE cs.case_number ILIKE %s OR cs.status ILIKE %s
           OR cs.description ILIKE %s OR c.crime_type ILIKE %s
           OR o.name ILIKE %s OR CAST(cs.case_id AS TEXT) = %s
        ORDER BY cs.filing_date DESC, cs.case_id DESC""",
        (p, p, p, p, p, keyword.strip()),
    )


def update_case_status(case_id, status):
    if status not in CASE_STATUSES:
        raise DatabaseError("Invalid case status.")
    return execute_write("UPDATE cases SET status = %s WHERE case_id = %s",
                         (status, case_id))


def update_case(case_id, case_number, crime_id, officer_id, filing_date,
                status, description):
    case_number = _require(case_number, "Case number")
    if status not in CASE_STATUSES:
        raise DatabaseError("Invalid case status.")
    return execute_write(
        """UPDATE cases
           SET case_number = %s, crime_id = %s, officer_id = %s,
               filing_date = %s, status = %s, description = %s
           WHERE case_id = %s""",
        (case_number, crime_id, officer_id, filing_date, status,
         _clean(description), case_id),
    )


def delete_case(case_id):
    return execute_write("DELETE FROM cases WHERE case_id = %s", (case_id,))


# DASHBOARD
def get_dashboard_stats():
    """
    Open cases   = status 'Open' or 'Under Investigation'
    Closed cases = status 'Solved' or 'Closed'
    """
    return fetch_one(
        """SELECT
             (SELECT COUNT(*) FROM criminals)        AS total_criminals,
             (SELECT COUNT(*) FROM victims)          AS total_victims,
             (SELECT COUNT(*) FROM police_officers)  AS total_officers,
             (SELECT COUNT(*) FROM crimes)           AS total_crimes,
             (SELECT COUNT(*) FROM cases)            AS total_cases,
             (SELECT COUNT(*) FROM cases
               WHERE status IN ('Open', 'Under Investigation')) AS open_cases,
             (SELECT COUNT(*) FROM cases
               WHERE status IN ('Solved', 'Closed'))            AS closed_cases"""
    )


# REPORTS
def report_crimes_by_type():
    return fetch_all(
        """SELECT crime_type, COUNT(*) AS total_crimes
           FROM crimes
           GROUP BY crime_type
           ORDER BY total_crimes DESC, crime_type"""
    )


def report_cases_by_status():
    return fetch_all(
        """SELECT status, COUNT(*) AS total_cases
           FROM cases
           GROUP BY status
           ORDER BY total_cases DESC, status"""
    )


def report_crimes_per_officer():
    return fetch_all(
        """SELECT o.officer_id, o.name AS officer_name, o.rank,
                  COUNT(c.crime_id) AS crimes_handled
           FROM police_officers o
           LEFT JOIN crimes c ON o.officer_id = c.officer_id
           GROUP BY o.officer_id, o.name, o.rank
           ORDER BY crimes_handled DESC, o.name"""
    )


def report_repeat_criminals():
    return fetch_all(
        """SELECT cr.criminal_id, cr.name AS criminal_name,
                  COUNT(c.crime_id) AS total_crimes
           FROM criminals cr
           INNER JOIN crimes c ON cr.criminal_id = c.criminal_id
           GROUP BY cr.criminal_id, cr.name
           HAVING COUNT(c.crime_id) > 1
           ORDER BY total_crimes DESC, cr.name"""
    )


def report_cases_per_officer():
    return fetch_all(
        """SELECT o.officer_id, o.name AS officer_name, o.police_station,
                  COUNT(cs.case_id) AS cases_handled
           FROM police_officers o
           LEFT JOIN cases cs ON o.officer_id = cs.officer_id
           GROUP BY o.officer_id, o.name, o.police_station
           ORDER BY cases_handled DESC, o.name"""
    )


def report_avg_victim_age_by_crime_type():
    """Extra report: demonstrates AVG."""
    return fetch_all(
        """SELECT c.crime_type, ROUND(AVG(v.age), 1) AS average_victim_age
           FROM crimes c
           INNER JOIN victims v ON c.victim_id = v.victim_id
           GROUP BY c.crime_type
           ORDER BY average_victim_age DESC"""
    )


def report_crimes_without_case():
    """Extra report: demonstrates a subquery."""
    return fetch_all(
        """SELECT crime_id, crime_type, crime_date, location
           FROM crimes
           WHERE crime_id NOT IN (SELECT crime_id FROM cases)
           ORDER BY crime_date"""
    )


# QUICK SELF-TEST:  python database.py
if __name__ == "__main__":
    try:
        test_connection()
        print("Connected to PostgreSQL successfully.\n")
        for key, value in get_dashboard_stats().items():
            print(f"{key:16}: {value}")
    except DatabaseError as err:
        print("ERROR:", err)