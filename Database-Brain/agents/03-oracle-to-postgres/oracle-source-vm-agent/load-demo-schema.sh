#!/bin/bash
echo "==CONTAINER=="
sudo docker ps --filter name=oracle-xe --format '{{.Status}}'

echo "==SQL-VERSION=="
sudo docker exec oracle-xe bash -c "echo 'select banner from v\$version where rownum=1;' | sqlplus -s system/Demo_Ora2Pg_2026!@//localhost:1521/XEPDB1"

echo "==CREATE-DEMO-SCHEMA=="
sudo docker exec -i oracle-xe sqlplus -s system/Demo_Ora2Pg_2026!@//localhost:1521/XEPDB1 <<'SQL'
SET ECHO OFF FEEDBACK ON
CREATE USER hr_demo IDENTIFIED BY hr_demo;
GRANT CONNECT, RESOURCE, UNLIMITED TABLESPACE TO hr_demo;
SQL

sudo docker exec -i oracle-xe sqlplus -s hr_demo/hr_demo@//localhost:1521/XEPDB1 <<'SQL'
SET ECHO OFF FEEDBACK ON
CREATE TABLE departments (
  department_id NUMBER(4) PRIMARY KEY,
  department_name VARCHAR2(30) NOT NULL,
  location_id NUMBER(4)
);
CREATE TABLE employees (
  employee_id NUMBER(6) PRIMARY KEY,
  first_name VARCHAR2(20),
  last_name VARCHAR2(25) NOT NULL,
  email VARCHAR2(25) UNIQUE NOT NULL,
  phone_number VARCHAR2(20),
  hire_date DATE NOT NULL,
  job_id VARCHAR2(10) NOT NULL,
  salary NUMBER(8,2),
  commission_pct NUMBER(2,2),
  manager_id NUMBER(6),
  department_id NUMBER(4) REFERENCES departments(department_id)
);
CREATE INDEX emp_dept_ix ON employees(department_id);
CREATE INDEX emp_name_ix ON employees(last_name, first_name);
CREATE SEQUENCE emp_seq START WITH 1000;

INSERT INTO departments VALUES (10, 'Administration', 1700);
INSERT INTO departments VALUES (20, 'Marketing', 1800);
INSERT INTO departments VALUES (30, 'Purchasing', 1700);
INSERT INTO departments VALUES (40, 'Human Resources', 2400);
INSERT INTO departments VALUES (50, 'Shipping', 1500);
INSERT INTO departments VALUES (60, 'IT', 1400);
INSERT INTO departments VALUES (70, 'Public Relations', 2700);
INSERT INTO departments VALUES (80, 'Sales', 2500);
INSERT INTO departments VALUES (90, 'Executive', 1700);
INSERT INTO departments VALUES (100, 'Finance', 1700);

INSERT INTO employees VALUES (100, 'Steven', 'King', 'SKING', '515.123.4567', DATE '2003-06-17', 'AD_PRES', 24000, NULL, NULL, 90);
INSERT INTO employees VALUES (101, 'Neena', 'Kochhar', 'NKOCHHAR', '515.123.4568', DATE '2005-09-21', 'AD_VP', 17000, NULL, 100, 90);
INSERT INTO employees VALUES (102, 'Lex', 'De Haan', 'LDEHAAN', '515.123.4569', DATE '2001-01-13', 'AD_VP', 17000, NULL, 100, 90);
INSERT INTO employees VALUES (103, 'Alexander', 'Hunold', 'AHUNOLD', '590.423.4567', DATE '2006-01-03', 'IT_PROG', 9000, NULL, 102, 60);
INSERT INTO employees VALUES (104, 'Bruce', 'Ernst', 'BERNST', '590.423.4568', DATE '2007-05-21', 'IT_PROG', 6000, NULL, 103, 60);
INSERT INTO employees VALUES (107, 'Diana', 'Lorentz', 'DLORENTZ', '590.423.5567', DATE '2007-02-07', 'IT_PROG', 4200, NULL, 103, 60);
INSERT INTO employees VALUES (108, 'Nancy', 'Greenberg', 'NGREENBERG', '515.124.4569', DATE '2002-08-17', 'FI_MGR', 12008, NULL, 101, 100);
INSERT INTO employees VALUES (109, 'Daniel', 'Faviet', 'DFAVIET', '515.124.4169', DATE '2002-08-16', 'FI_ACCOUNT', 9000, NULL, 108, 100);
INSERT INTO employees VALUES (110, 'John', 'Chen', 'JCHEN', '515.124.4269', DATE '2005-09-28', 'FI_ACCOUNT', 8200, NULL, 108, 100);
INSERT INTO employees VALUES (200, 'Jennifer', 'Whalen', 'JWHALEN', '515.123.4444', DATE '2003-09-17', 'AD_ASST', 4400, NULL, 101, 10);
INSERT INTO employees VALUES (201, 'Michael', 'Hartstein', 'MHARTSTEIN', '515.123.5555', DATE '2004-02-17', 'MK_MAN', 13000, NULL, 100, 20);
INSERT INTO employees VALUES (202, 'Pat', 'Fay', 'PFAY', '603.123.6666', DATE '2005-08-17', 'MK_REP', 6000, NULL, 201, 20);

CREATE OR REPLACE PROCEDURE give_raise(p_emp_id IN NUMBER, p_pct IN NUMBER) AS
BEGIN
  UPDATE employees SET salary = salary * (1 + p_pct/100) WHERE employee_id = p_emp_id;
  COMMIT;
END;
/

CREATE OR REPLACE FUNCTION get_dept_total(p_dept_id IN NUMBER) RETURN NUMBER AS
  v_total NUMBER;
BEGIN
  SELECT NVL(SUM(salary),0) INTO v_total FROM employees WHERE department_id = p_dept_id;
  RETURN v_total;
END;
/

CREATE OR REPLACE VIEW emp_details AS
SELECT e.employee_id, e.first_name||' '||e.last_name AS full_name, e.email,
       d.department_name, e.salary
FROM employees e LEFT JOIN departments d ON e.department_id = d.department_id;

COMMIT;
SQL

echo "==COUNTS=="
sudo docker exec -i oracle-xe sqlplus -s hr_demo/hr_demo@//localhost:1521/XEPDB1 <<'SQL'
SET ECHO OFF FEEDBACK OFF HEADING ON PAGESIZE 50
SELECT 'departments' AS t, COUNT(*) AS n FROM departments
UNION ALL SELECT 'employees', COUNT(*) FROM employees
UNION ALL SELECT 'objects', COUNT(*) FROM user_objects;
SQL

echo "==DONE=="
