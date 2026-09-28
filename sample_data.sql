-- Sample data. Safe to re-run: it clears the tables first and resets IDs to 1.
TRUNCATE cases, crimes, police_officers, victims, criminals RESTART IDENTITY CASCADE;

INSERT INTO criminals (name, date_of_birth, gender, address, phone) VALUES
('Rahul Sharma',  '1990-05-14', 'Male',   'Rajendra Nagar, Indore', '9876500001'),
('Sanjay Patil', '1985-11-02', 'Male',   'Arera Colony, Bhopal',   '9876500002'),
('Amit Yadav',   '1995-03-21', 'Male',   'Freeganj, Ujjain',       '9876500003'),
('Deepak Rana',  '1988-07-30', 'Male',   'Sudama Nagar, Indore',   '9876500004'),
('Kavita Joshi', '1992-09-09', 'Female', 'AB Road, Dewas',         '9876500005'),
('Imran Khan',   '1983-01-17', 'Male',   'Old City, Bhopal',       '9876500006');

INSERT INTO victims (name, age, gender, address, phone) VALUES
('Anita Sharma',   34, 'Female', 'Palasia, Indore',       '9123400001'),
('Rohit Gupta',    45, 'Male',   'Vijay Nagar, Indore',   '9123400002'),
('Meena Kulkarni', 29, 'Female', 'Scheme No 54, Indore',  '9123400003'),
('Suresh Jain',    52, 'Male',   'Sarafa, Indore',        '9123400004'),
('Pooja Mishra',   23, 'Female', 'Bhawarkua, Indore',     '9123400005'),
('Vikas Tiwari',   38, 'Male',   'Rau, Indore',           '9123400006');

INSERT INTO police_officers (name, rank, phone, police_station) VALUES
('Ramesh Chauhan',  'Inspector',     '9000000001', 'Vijay Nagar Police Station'),
('Neha Singh',      'Sub-Inspector', '9000000002', 'Palasia Police Station'),
('Arvind Malviya',  'Inspector',     '9000000003', 'Tukoganj Police Station'),
('Mohan Lal',       'Head Constable','9000000004', 'Vijay Nagar Police Station');

INSERT INTO crimes (crime_type, crime_date, location, description, criminal_id, victim_id, officer_id) VALUES
('Theft',    '2026-01-12', 'Palasia Market, Indore',  'Mobile phone stolen from shop counter',   1, 1, 2),
('Robbery',  '2026-02-03', 'MG Road, Indore',         'Chain snatched at knifepoint',            2, 2, 1),
('Assault',  '2026-02-18', 'Vijay Nagar, Indore',     'Physical fight outside a restaurant',     3, 3, 1),
('Fraud',    '2026-03-07', 'Online',                  'Fake investment scheme',                  4, 4, 3),
('Theft',    '2026-03-25', 'Rajwada, Indore',         'Wallet pickpocketed in crowd',            1, 5, 2),
('Burglary', '2026-04-10', 'Scheme No 78, Indore',    'House broken into while owners away',     5, 6, 4),
('Fraud',    '2026-05-02', 'Online',                  'Fake job offer, money taken',             4, 1, 3),
('Assault',  '2026-05-19', 'Bhawarkua, Indore',       'Attack during a road dispute',            3, 2, 1),
('Robbery',  '2026-06-08', 'Ring Road, Indore',       'Bag snatched from a two-wheeler rider',   2, 3, 4),
('Theft',    '2026-07-14', 'Sarafa Bazaar, Indore',   'Jewellery stolen from display',           1, 4, 2);

INSERT INTO cases (case_number, crime_id, officer_id, filing_date, status, description) VALUES
('FIR-2026-001', 1,  2, '2026-01-13', 'Closed',              'Phone recovered, accused arrested'),
('FIR-2026-002', 2,  1, '2026-02-04', 'Solved',              'Accused identified through CCTV'),
('FIR-2026-003', 3,  1, '2026-02-19', 'Closed',              'Settled, charges filed'),
('FIR-2026-004', 4,  3, '2026-03-08', 'Under Investigation', 'Bank records being traced'),
('FIR-2026-005', 5,  2, '2026-03-26', 'Open',                'Witness statements pending'),
('FIR-2026-006', 6,  4, '2026-04-11', 'Open',                'Fingerprints sent to lab'),
('FIR-2026-007', 7,  3, '2026-05-03', 'Under Investigation', 'Linked to earlier fraud case'),
('FIR-2026-008', 9,  4, '2026-06-09', 'Open',                'Searching for eyewitnesses');