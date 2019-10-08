CREATE TABLE section_types (
  id SERIAL PRIMARY KEY,
  type VARCHAR NOT NULL,
  UNIQUE (type)
);

INSERT INTO section_types (type) VALUES
  ('Lecture'),  ('Recitation'), ('Laboratory'),   ('Seminar'),      ('Practicum'),
  ('Study'),    ('Studies'),    ('Dissertation'), ('Independent'),  ('Internship'),
  ('Other'),    ('Section'),    ('Field'),        ('Research'),     ('Clinical'),
  ('Workshop'), ('Studio');

CREATE TABLE institutions (
  id SERIAL PRIMARY KEY,
  name VARCHAR NOT NULL,
  UNIQUE (name)
);

INSERT INTO institutions (name) VALUES
  ('Boulder'), ('Denver'), ('Colorado Springs');

CREATE TABLE instruction_modes (
  id SERIAL PRIMARY KEY,
  mode VARCHAR NOT NULL,
  UNIQUE (mode)
);

INSERT INTO instruction_modes (mode) VALUES
  ('In-person'), ('Online');