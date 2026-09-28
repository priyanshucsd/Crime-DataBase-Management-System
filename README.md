# Crime Database Management System (CDMS)

A simple DBMS mini project built with **Python, PostgreSQL, psycopg2 and Streamlit**.
It manages criminals, victims, police officers, crimes and cases, with a dashboard
and reports.

## Features

- Dashboard with 7 live statistics
- Full CRUD (add, view, search, update, delete) for all 5 tables
- Crime registration with dropdowns for criminal, victim and officer
- Case registration with dropdowns for crime and officer, and status updates
- Reports with tables and charts (crimes by type, cases by status,
  officer workload, repeat criminals, and more)
- Parameterized SQL queries (SQL injection safe)
- Transactions with rollback on error
- Friendly error messages for database problems

## Database Design

| Table | Primary Key | Foreign Keys |
|---|---|---|
| criminals | criminal_id | none |
| victims | victim_id | none |
| police_officers | officer_id | none |
| crimes | crime_id | criminal_id, victim_id, officer_id |
| cases | case_id | crime_id, officer_id |

Relationships:
- One criminal, victim or officer can be linked to many crimes.
- One crime can have many cases.
- One officer can handle many cases.
- Deleting a crime also deletes its cases (`ON DELETE CASCADE`).
- Deleting a criminal, victim or officer linked to a crime is blocked
  (`ON DELETE RESTRICT`).

## Project Structure

```text
crime_database/
├── app.py            Streamlit user interface
├── database.py       All PostgreSQL logic (connection, CRUD, reports)
├── schema.sql        Creates the 5 tables
├── sample_data.sql   Sample records
├── queries.sql       26 demo queries covering the required SQL features
├── requirements.txt  Python packages
└── README.md
```

## Requirements

- Python 3.9 or higher
- PostgreSQL 13 or higher (with pgAdmin, optional)

## Setup

### 1. Create the database

```powershell
psql -U postgres -c "CREATE DATABASE crime_db;"
```

(Or create `crime_db` from pgAdmin: right-click Databases, Create, Database.)

### 2. Create tables and load sample data

```powershell
psql -U postgres -d crime_db -f schema.sql
psql -U postgres -d crime_db -f sample_data.sql
```

Run `schema.sql` first. Running it again erases all data.

### 3. Install Python packages

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure the connection

Copy `.env.example` to `.env` and fill in your PostgreSQL details:

```powershell
copy .env.example .env
```

Then edit `.env`:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crime_db
DB_USER=postgres
DB_PASSWORD=your_real_password
```

### 5. Check the connection

```powershell
python database.py
```

Expected: `Connected to PostgreSQL successfully.` followed by the record counts.

### 6. Run the application

```powershell
streamlit run app.py
```

The app opens at http://localhost:8501. Press Ctrl + C in the terminal to stop it.

## Sample Data

| Table | Rows |
|---|---|
| criminals | 6 |
| victims | 6 |
| police_officers | 4 |
| crimes | 10 |
| cases | 8 |

## SQL Concepts Demonstrated

INSERT, SELECT, UPDATE, DELETE, WHERE, ORDER BY, GROUP BY, HAVING,
INNER JOIN, LEFT JOIN, COUNT, AVG and subqueries (see `queries.sql`).

## Testing

1. Reset data: run `schema.sql` then `sample_data.sql`.
2. Dashboard should show 6, 6, 4, 10, 8, Open 5, Closed 3.
3. Try Add, Search, Update and Delete on every page.
4. Try deleting a linked record: the app shows a friendly error.
5. Open every Reports tab.
6. SQL injection test: search for `' OR 1=1 --`. No records match,
   because input is passed as a parameter and never executed as SQL.

## Troubleshooting

| Problem | Fix |
|---|---|
| Could not connect to PostgreSQL | Start the PostgreSQL service; check port and password in `database.py` |
| `psql` is not recognized | Add PostgreSQL's `bin` folder to PATH |
| `relation "criminals" does not exist` | Run `schema.sql` on `crime_db` |
| `ModuleNotFoundError` | Activate the virtual environment and run `pip install -r requirements.txt` |
| Reports are empty | Run `sample_data.sql` |

## Author

Priyanshu Sharma , 0808CS241280, B.Tech CSE, IPS Academy, Indore