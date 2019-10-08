use super::schema::*;
use diesel::pg::data_types::{PgTime};

#[derive(Queryable)]
pub struct Constant {
  // pub id: i32,
  pub value: String,
}

#[derive(Queryable)]
pub struct Class {
    pub id: i32,
    pub code: String,
    pub full_name: String,
    pub description: Option<String>,
}

#[derive(Queryable)]
pub struct Instructor {
    pub id: i32,
    pub full_name: String,
}

#[derive(Insertable)]
#[derive(AsChangeset)]
#[table_name="section_types"]
pub struct NewSectionType<'a> { 
  // pub id: i32,
  pub type_: &'a str,
}

#[derive(Insertable, AsChangeset)]
#[table_name="classes"]
pub struct NewClass<'a> {
  // pub id: i32,
  pub code: &'a str,
  pub full_name: &'a str,
  pub description: &'a str,
}

#[derive(Insertable, AsChangeset)]
#[table_name="semesters"]
pub struct NewSemester<'a> {
  // pub id: i32,
  pub year: i32,
  pub season: &'a str,
}

#[derive(Insertable, AsChangeset)]
#[table_name="instructors"]
pub struct NewInstructor {
  // pub id: i32,
  pub full_name: String,
}


#[derive(Insertable, AsChangeset)]
#[table_name="sections"]
pub struct NewSection<'a> {
  pub crn: i32,
  pub section_no: i32,
  pub parent_class: i32, // REFERENCES classes NOT NULL,
  pub section_type: i32, // REFERENCES section_types NOT NULL,
  pub institution: i32, // REFERENCES institutions,
  pub mode: i32, // REFERENCES instruction_modes,

  pub semester: i32, // REFERENCES semesters NOT NULL,
  // pub start_time: PgTime,
  // pub end_time: PgTime,
  
  // pub monday: bool,
  // pub tuesday: bool,
  // pub wednesday: bool,
  // pub thursday: bool,
  // pub friday: bool,
  // pub saturday: bool,
  // pub sunday: bool,

  // pub instructor: i32, // REFERENCES instructors,
  // pub credits: i32,
  // pub total_seats: i32,
  // pub available_seats: i32,
  // pub waitlist: i32,

  // pub is_cancelled: bool,
  // pub special_date_range: bool,
  // pub no_auto_enroll: bool,
  pub section_name: &'a str,
}