CREATE TABLE classes (
  id SERIAL PRIMARY KEY,
  code VARCHAR NOT NULL,
  full_name VARCHAR NOT NULL,
  description VARCHAR,
  UNIQUE (code)
);

CREATE TABLE semesters (
  id SERIAL PRIMARY KEY,
  year INTEGER NOT NULL,
  season VARCHAR NOT NULL,
  UNIQUE (year, season)
);

CREATE TABLE instructors (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR NOT NULL,
  UNIQUE (full_name)
);

CREATE TABLE sections (
  crn INTEGER PRIMARY KEY,
  section_no INTEGER NOT NULL,
  parent_class VARCHAR REFERENCES classes(code) NOT NULL,
  section_type INTEGER REFERENCES section_types NOT NULL,
  institution INTEGER REFERENCES institutions,
  mode INTEGER REFERENCES instruction_modes,

  semester INTEGER REFERENCES semesters NOT NULL,
  start_time TIME,
  end_time TIME,
  
  -- If anyone can think of a better way of doing this, please change it.
  monday BOOLEAN,
  tuesday BOOLEAN,
  wednesday BOOLEAN,
  thursday BOOLEAN,
  friday BOOLEAN,
  saturday BOOLEAN,
  sunday BOOLEAN,

  instructor INTEGER REFERENCES instructors,
  credits INTEGER,
  total_seats INTEGER,
  available_seats INTEGER,
  waitlist INTEGER,

  is_cancelled BOOLEAN,
  special_date_range BOOLEAN,
  no_auto_enroll BOOLEAN,
  section_name TEXT
);