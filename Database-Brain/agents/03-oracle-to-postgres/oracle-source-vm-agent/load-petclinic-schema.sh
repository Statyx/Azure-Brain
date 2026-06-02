#!/bin/bash
# Load Spring PetClinic Oracle schema with PL/SQL extras for migration assessment demo
set -e

echo "==DROP_OLD=="
docker exec -i oracle-xe sqlplus -s sys/Demo_Ora2Pg_2026!@//localhost:1521/XEPDB1 as sysdba <<'SQL'
WHENEVER SQLERROR CONTINUE;
DROP USER hr_demo CASCADE;
DROP USER petclinic CASCADE;
EXIT;
SQL

echo "==CREATE_USER=="
docker exec -i oracle-xe sqlplus -s sys/Demo_Ora2Pg_2026!@//localhost:1521/XEPDB1 as sysdba <<'SQL'
CREATE USER petclinic IDENTIFIED BY petclinic
  DEFAULT TABLESPACE USERS
  QUOTA UNLIMITED ON USERS;
GRANT CONNECT, RESOURCE, CREATE VIEW, CREATE PROCEDURE, CREATE TRIGGER, CREATE SEQUENCE TO petclinic;
EXIT;
SQL

echo "==CREATE_SCHEMA=="
docker exec -i oracle-xe sqlplus -s petclinic/petclinic@//localhost:1521/XEPDB1 <<'SQL'
WHENEVER SQLERROR EXIT SQL.SQLCODE;

-- ============ TABLES ============
CREATE TABLE types (
  id   NUMBER(10) PRIMARY KEY,
  name VARCHAR2(80) NOT NULL
);

CREATE TABLE owners (
  id         NUMBER(10) PRIMARY KEY,
  first_name VARCHAR2(30) NOT NULL,
  last_name  VARCHAR2(30) NOT NULL,
  address    VARCHAR2(255),
  city       VARCHAR2(80),
  telephone  VARCHAR2(20),
  created_at DATE DEFAULT SYSDATE NOT NULL
);

CREATE TABLE pets (
  id         NUMBER(10) PRIMARY KEY,
  name       VARCHAR2(30) NOT NULL,
  birth_date DATE,
  type_id    NUMBER(10) NOT NULL,
  owner_id   NUMBER(10) NOT NULL,
  CONSTRAINT fk_pets_type  FOREIGN KEY (type_id)  REFERENCES types(id),
  CONSTRAINT fk_pets_owner FOREIGN KEY (owner_id) REFERENCES owners(id)
);

CREATE TABLE visits (
  id          NUMBER(10) PRIMARY KEY,
  pet_id      NUMBER(10) NOT NULL,
  visit_date  DATE NOT NULL,
  description VARCHAR2(4000),
  cost        NUMBER(10,2) DEFAULT 0,
  CONSTRAINT fk_visits_pet FOREIGN KEY (pet_id) REFERENCES pets(id),
  CONSTRAINT chk_visit_cost CHECK (cost >= 0)
);

CREATE TABLE vets (
  id         NUMBER(10) PRIMARY KEY,
  first_name VARCHAR2(30) NOT NULL,
  last_name  VARCHAR2(30) NOT NULL
);

CREATE TABLE specialties (
  id   NUMBER(10) PRIMARY KEY,
  name VARCHAR2(80) NOT NULL
);

CREATE TABLE vet_specialties (
  vet_id       NUMBER(10) NOT NULL,
  specialty_id NUMBER(10) NOT NULL,
  CONSTRAINT pk_vet_spec PRIMARY KEY (vet_id, specialty_id),
  CONSTRAINT fk_vs_vet  FOREIGN KEY (vet_id)       REFERENCES vets(id),
  CONSTRAINT fk_vs_spec FOREIGN KEY (specialty_id) REFERENCES specialties(id)
);

-- ============ SEQUENCES ============
CREATE SEQUENCE seq_owners   START WITH 100;
CREATE SEQUENCE seq_pets     START WITH 100;
CREATE SEQUENCE seq_visits   START WITH 100;
CREATE SEQUENCE seq_vets     START WITH 100;

-- ============ INDEXES ============
CREATE INDEX idx_pets_owner   ON pets(owner_id);
CREATE INDEX idx_pets_type    ON pets(type_id);
CREATE INDEX idx_visits_pet   ON visits(pet_id);
CREATE INDEX idx_owners_lname ON owners(last_name);

EXIT;
SQL

echo "==CREATE_PLSQL=="
docker exec -i oracle-xe sqlplus -s petclinic/petclinic@//localhost:1521/XEPDB1 <<'SQL'
WHENEVER SQLERROR EXIT SQL.SQLCODE;

-- ============ TRIGGER (BEFORE INSERT auto-id, Oracle-style) ============
CREATE OR REPLACE TRIGGER trg_owners_bi
BEFORE INSERT ON owners
FOR EACH ROW
BEGIN
  IF :NEW.id IS NULL THEN
    :NEW.id := seq_owners.NEXTVAL;
  END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_visits_bi
BEFORE INSERT ON visits
FOR EACH ROW
BEGIN
  IF :NEW.id IS NULL THEN
    :NEW.id := seq_visits.NEXTVAL;
  END IF;
  IF :NEW.visit_date IS NULL THEN
    :NEW.visit_date := SYSDATE;
  END IF;
END;
/

-- ============ VIEW ============
CREATE OR REPLACE VIEW v_pet_owner AS
SELECT p.id AS pet_id, p.name AS pet_name, t.name AS type_name,
       o.first_name || ' ' || o.last_name AS owner_name, o.city
FROM pets p
JOIN types t  ON p.type_id  = t.id
JOIN owners o ON p.owner_id = o.id;

-- ============ FUNCTION ============
CREATE OR REPLACE FUNCTION count_pets_by_owner(p_owner_id IN NUMBER)
RETURN NUMBER
IS
  v_count NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_count FROM pets WHERE owner_id = p_owner_id;
  RETURN v_count;
END;
/

-- ============ PROCEDURE ============
CREATE OR REPLACE PROCEDURE add_visit(
  p_pet_id      IN NUMBER,
  p_description IN VARCHAR2,
  p_cost        IN NUMBER DEFAULT 0
)
IS
BEGIN
  INSERT INTO visits(pet_id, visit_date, description, cost)
  VALUES (p_pet_id, SYSDATE, p_description, p_cost);
  COMMIT;
END;
/

-- ============ PACKAGE (PL/SQL flavor) ============
CREATE OR REPLACE PACKAGE pkg_clinic_stats AS
  FUNCTION total_revenue RETURN NUMBER;
  FUNCTION visits_for_pet(p_pet_id IN NUMBER) RETURN NUMBER;
  PROCEDURE refresh_summary;
END pkg_clinic_stats;
/

CREATE OR REPLACE PACKAGE BODY pkg_clinic_stats AS
  FUNCTION total_revenue RETURN NUMBER IS
    v_total NUMBER;
  BEGIN
    SELECT NVL(SUM(cost),0) INTO v_total FROM visits;
    RETURN v_total;
  END;

  FUNCTION visits_for_pet(p_pet_id IN NUMBER) RETURN NUMBER IS
    v_count NUMBER;
  BEGIN
    SELECT COUNT(*) INTO v_count FROM visits WHERE pet_id = p_pet_id;
    RETURN v_count;
  END;

  PROCEDURE refresh_summary IS
  BEGIN
    DBMS_OUTPUT.PUT_LINE('Refreshed at ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS'));
  END;
END pkg_clinic_stats;
/

EXIT;
SQL

echo "==SEED_DATA=="
docker exec -i oracle-xe sqlplus -s petclinic/petclinic@//localhost:1521/XEPDB1 <<'SQL'
WHENEVER SQLERROR EXIT SQL.SQLCODE;

-- types
INSERT INTO types VALUES (1,'cat');
INSERT INTO types VALUES (2,'dog');
INSERT INTO types VALUES (3,'lizard');
INSERT INTO types VALUES (4,'snake');
INSERT INTO types VALUES (5,'bird');
INSERT INTO types VALUES (6,'hamster');

-- owners (id auto via trigger)
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('George','Franklin','110 W. Liberty St.','Madison','6085551023');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('Betty','Davis','638 Cardinal Ave.','Sun Prairie','6085551749');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('Eduardo','Rodriquez','2693 Commerce St.','McFarland','6085558763');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('Harold','Davis','563 Friendly St.','Windsor','6085553198');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('Peter','McTavish','2387 S. Fair Way','Madison','6085552765');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('Jean','Coleman','105 N. Lake St.','Monona','6085552654');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('Jeff','Black','1450 Oak Blvd.','Monona','6085555387');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('Maria','Escobito','345 Maple St.','Madison','6085557683');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('David','Schroeder','2749 Blackhawk Trail','Madison','6085559435');
INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES ('Carlos','Estaban','2335 Independence La.','Waunakee','6085555487');

-- pets
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Leo',  DATE '2010-09-07',1,100);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Basil',DATE '2012-08-06',6,101);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Rosy', DATE '2011-04-17',2,102);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Jewel',DATE '2010-03-07',2,102);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Iggy', DATE '2010-11-30',3,103);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'George',DATE '2010-01-20',4,104);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Samantha',DATE '2012-09-04',1,105);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Max', DATE '2012-09-04',1,105);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Lucky',DATE '2011-08-06',5,106);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Mulligan',DATE '2007-02-24',2,107);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Freddy',DATE '2010-03-09',5,108);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Lucky II',DATE '2010-06-24',2,109);
INSERT INTO pets(id,name,birth_date,type_id,owner_id) VALUES (seq_pets.NEXTVAL,'Sly', DATE '2012-06-08',1,109);

-- vets
INSERT INTO vets VALUES (seq_vets.NEXTVAL,'James','Carter');
INSERT INTO vets VALUES (seq_vets.NEXTVAL,'Helen','Leary');
INSERT INTO vets VALUES (seq_vets.NEXTVAL,'Linda','Douglas');
INSERT INTO vets VALUES (seq_vets.NEXTVAL,'Rafael','Ortega');
INSERT INTO vets VALUES (seq_vets.NEXTVAL,'Henry','Stevens');
INSERT INTO vets VALUES (seq_vets.NEXTVAL,'Sharon','Jenkins');

-- specialties
INSERT INTO specialties VALUES (1,'radiology');
INSERT INTO specialties VALUES (2,'surgery');
INSERT INTO specialties VALUES (3,'dentistry');

-- vet_specialties
INSERT INTO vet_specialties VALUES (101,1);
INSERT INTO vet_specialties VALUES (102,2);
INSERT INTO vet_specialties VALUES (102,3);
INSERT INTO vet_specialties VALUES (103,2);
INSERT INTO vet_specialties VALUES (104,1);

-- visits (via procedure to exercise PL/SQL path)
BEGIN
  add_visit(100, 'rabies shot', 35.00);
  add_visit(102, 'rabies shot', 35.00);
  add_visit(102, 'broken X-ray', 200.50);
  add_visit(104, 'spayed', 350.00);
END;
/

COMMIT;
EXIT;
SQL

echo "==VERIFY=="
docker exec -i oracle-xe sqlplus -s petclinic/petclinic@//localhost:1521/XEPDB1 <<'SQL'
SET PAGESIZE 100 LINESIZE 120 FEEDBACK OFF
SELECT object_type, COUNT(*) AS cnt FROM user_objects GROUP BY object_type ORDER BY 1;
SELECT 'owners'      AS tbl, COUNT(*) FROM owners
UNION ALL SELECT 'pets',     COUNT(*) FROM pets
UNION ALL SELECT 'visits',   COUNT(*) FROM visits
UNION ALL SELECT 'vets',     COUNT(*) FROM vets
UNION ALL SELECT 'types',    COUNT(*) FROM types;
SELECT pkg_clinic_stats.total_revenue AS revenue FROM dual;
SELECT count_pets_by_owner(102) AS pets_for_owner_102 FROM dual;
EXIT;
SQL

echo "==DONE=="
