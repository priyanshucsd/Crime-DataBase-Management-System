
-- Q1. SELECT: all criminals
SELECT * FROM criminals;

-- Q2. WHERE: crimes of one type
SELECT crime_id, crime_type, crime_date, location
FROM crimes
WHERE crime_type = 'Theft';

-- Q3. WHERE with AND + range: crimes between two dates
SELECT crime_id, crime_type, crime_date, location
FROM crimes
WHERE crime_date BETWEEN '2026-02-01' AND '2026-04-30'
  AND crime_type <> 'Fraud';

-- Q4. WHERE with pattern search: Indore criminals
SELECT criminal_id, name, address
FROM criminals
WHERE address ILIKE '%indore%';

-- Q5. ORDER BY: newest crimes first
SELECT crime_id, crime_type, crime_date, location
FROM crimes
ORDER BY crime_date DESC;

-- Q6. INSERT 
BEGIN;
INSERT INTO criminals (name, date_of_birth, gender, address, phone)
VALUES ('Demo Person', '2000-01-01', 'Male', 'Demo Address', '9999999999');
SELECT * FROM criminals WHERE name = 'Demo Person';
ROLLBACK;

-- Q7. UPDATE: close a case
BEGIN;
UPDATE cases SET status = 'Closed' WHERE case_number = 'FIR-2026-005';
SELECT case_number, status FROM cases WHERE case_number = 'FIR-2026-005';
ROLLBACK;

-- Q8. DELETE: remove a case
BEGIN;
DELETE FROM cases WHERE case_number = 'FIR-2026-008';
SELECT COUNT(*) AS cases_after_delete FROM cases;   
ROLLBACK;
SELECT COUNT(*) AS cases_after_rollback FROM cases; 

-- Q9. COUNT: totals
SELECT COUNT(*) AS total_crimes FROM crimes;

-- Q10. GROUP BY + COUNT: crimes by type
SELECT crime_type, COUNT(*) AS total_crimes
FROM crimes
GROUP BY crime_type
ORDER BY total_crimes DESC, crime_type;

-- Q11. GROUP BY + COUNT: cases by status
SELECT status, COUNT(*) AS total_cases
FROM cases
GROUP BY status
ORDER BY total_cases DESC, status;

-- Q12. AVG: average age of victims
SELECT ROUND(AVG(age), 1) AS average_victim_age FROM victims;

-- Q13. AVG + GROUP BY + INNER JOIN: average victim age per crime type
SELECT c.crime_type, ROUND(AVG(v.age), 1) AS average_victim_age
FROM crimes c
INNER JOIN victims v ON c.victim_id = v.victim_id
GROUP BY c.crime_type
ORDER BY average_victim_age DESC;


-- Q14. HAVING: criminals involved in more than one crime
SELECT cr.criminal_id, cr.name, COUNT(c.crime_id) AS total_crimes
FROM criminals cr
INNER JOIN crimes c ON cr.criminal_id = c.criminal_id
GROUP BY cr.criminal_id, cr.name
HAVING COUNT(c.crime_id) > 1
ORDER BY total_crimes DESC, cr.name;


-- Q15. HAVING on officers: officers who handled 3 or more crimes
SELECT o.name, COUNT(c.crime_id) AS crimes_handled
FROM police_officers o
INNER JOIN crimes c ON o.officer_id = c.officer_id
GROUP BY o.officer_id, o.name
HAVING COUNT(c.crime_id) >= 3;



SELECT c.crime_id, c.crime_type, c.crime_date, c.location,
       cr.name AS criminal, v.name AS victim, o.name AS officer
FROM crimes c
INNER JOIN criminals cr      ON c.criminal_id = cr.criminal_id
INNER JOIN victims v         ON c.victim_id   = v.victim_id
INNER JOIN police_officers o ON c.officer_id  = o.officer_id
ORDER BY c.crime_id;

-- Q17. INNER JOIN: case details with crime and officer
SELECT cs.case_number, cs.status, cs.filing_date,
       c.crime_type, c.location, o.name AS officer
FROM cases cs
INNER JOIN crimes c          ON cs.crime_id   = c.crime_id
INNER JOIN police_officers o ON cs.officer_id = o.officer_id
ORDER BY cs.filing_date;

-- Q18. LEFT JOIN: criminals with NO crime (shows NULL/0 for them)
SELECT cr.criminal_id, cr.name, COUNT(c.crime_id) AS total_crimes
FROM criminals cr
LEFT JOIN crimes c ON cr.criminal_id = c.criminal_id
GROUP BY cr.criminal_id, cr.name
ORDER BY total_crimes, cr.name;


-- Q19. LEFT JOIN: officer workload (crimes handled, including zero)
SELECT o.name, o.rank, COUNT(c.crime_id) AS crimes_handled
FROM police_officers o
LEFT JOIN crimes c ON o.officer_id = c.officer_id
GROUP BY o.officer_id, o.name, o.rank
ORDER BY crimes_handled DESC, o.name;

-- Q20. LEFT JOIN: cases handled by each officer
SELECT o.name, o.police_station, COUNT(cs.case_id) AS cases_handled
FROM police_officers o
LEFT JOIN cases cs ON o.officer_id = cs.officer_id
GROUP BY o.officer_id, o.name, o.police_station
ORDER BY cases_handled DESC, o.name;

-- Q21. LEFT JOIN + IS NULL: crimes that have no case
SELECT c.crime_id, c.crime_type, c.location
FROM crimes c
LEFT JOIN cases cs ON c.crime_id = cs.crime_id
WHERE cs.case_id IS NULL;

-- Q22. Subquery with NOT IN: the same result as Q21, written differently
SELECT crime_id, crime_type, crime_date, location
FROM crimes
WHERE crime_id NOT IN (SELECT crime_id FROM cases);

-- Q23. Subquery with IN: crimes whose case is still unsolved
SELECT crime_id, crime_type, location
FROM crimes
WHERE crime_id IN (SELECT crime_id
                   FROM cases
                   WHERE status IN ('Open', 'Under Investigation'));

-- Q24. Scalar subquery with AVG: victims older than the average victim
SELECT name, age
FROM victims
WHERE age > (SELECT AVG(age) FROM victims)
ORDER BY age DESC;

-- Q25. Subquery + HAVING: criminals with more crimes than the average criminal
SELECT cr.name, COUNT(c.crime_id) AS total_crimes
FROM criminals cr
INNER JOIN crimes c ON cr.criminal_id = c.criminal_id
GROUP BY cr.criminal_id, cr.name
HAVING COUNT(c.crime_id) > (SELECT AVG(crime_count)
                            FROM (SELECT COUNT(*) AS crime_count
                                  FROM crimes
                                  WHERE criminal_id IS NOT NULL
                                  GROUP BY criminal_id) AS per_criminal);


-- Q26. All dashboard counts in one query
SELECT
  (SELECT COUNT(*) FROM criminals)       AS total_criminals,
  (SELECT COUNT(*) FROM victims)         AS total_victims,
  (SELECT COUNT(*) FROM police_officers) AS total_officers,
  (SELECT COUNT(*) FROM crimes)          AS total_crimes,
  (SELECT COUNT(*) FROM cases)           AS total_cases,
  (SELECT COUNT(*) FROM cases WHERE status IN ('Open', 'Under Investigation')) AS open_cases,
  (SELECT COUNT(*) FROM cases WHERE status IN ('Solved', 'Closed'))            AS closed_cases;