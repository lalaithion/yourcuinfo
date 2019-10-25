CREATE TABLE section_types (
  id SERIAL PRIMARY KEY,
  type VARCHAR NOT NULL,
  code VARCHAR NOT NULL,
  UNIQUE (type, code)
);

INSERT INTO section_types (type, code) VALUES
  ('Lecture', 'LEC'), ('Recitation', 'REC'), ('Laboratory', 'LAB'),
  ('Seminar', 'SEM'), ('Practicum', 'PRA'), ('Study', 'STU'),
  ('Studies', 'STU'), ('Dissertation', 'DIS'), ('Independent', 'IND'),
  ('Internship', 'INT'), ('Other', 'OTH'), ('Section', 'SEC'), ('Field Study', 'FLD'),
  ('Research', 'RSC'), ('Clinical', 'CLN'), ('Workshop', 'WKS'), ('Studio', 'STU'),
  ('Discussion', 'DSC'), ('Main Lab Section', 'MLS');

CREATE TABLE institutions (
  id SERIAL PRIMARY KEY,
  name VARCHAR NOT NULL,
  code VARCHAR NOT NULL,
  UNIQUE (name)
);

INSERT INTO institutions (name, code) VALUES
  ('Boulder', 'Boulder Main Campus'), ('Denver', 'Denver'), ('Colorado Springs', 'Colorado Springs');

CREATE TABLE instruction_modes (
  id SERIAL PRIMARY KEY,
  mode VARCHAR NOT NULL,
  code VARCHAR NOT NULL,
  UNIQUE (code)
);

INSERT INTO instruction_modes (mode, code) VALUES
  ('In-person', 'In Person'), ('Online', 'Online');