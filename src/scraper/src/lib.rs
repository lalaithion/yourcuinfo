#[macro_use]
// extern crate lazy_static;
extern crate diesel;
extern crate dotenv;
extern crate regex;

pub mod schema;
pub mod models;
// pub mod scraper::json;
pub mod scraper;

// use serde_json::{from_str, Value, Value::Array, Value::Null, json};
use std::collections::HashMap;
use diesel::prelude::*;
use diesel::pg::upsert::excluded;
use diesel::pg::PgConnection;
use diesel::pg::data_types::{PgTime};
use dotenv::dotenv;
use std::env;
use regex::Regex;

use self::models::*;

pub fn establish_connection() -> PgConnection {
    dotenv().ok();

    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    PgConnection::establish(&database_url).expect(&format!("Error connecting to {}", database_url))
}

// pub fn display_from_db(connection: &PgConnection) {
//     use self::schema::section_types::dsl::*;

//     let results = section_types
//         // .limit(5)
//         .load::<Constant>(connection)
//         .expect("Error loading section_types");

//     println!("Displaying {} section_types", results.len());
//     for post in results {
//         println!("{}", post.value);
//     }
// }

// pub fn delete_from_db(conn: &PgConnection) {
//     use self::schema::section_types::dsl::*;

//     // let target = args().nth(1).expect("Expected a target to match against");
//     // let pattern = format!("%{}%", target);

//     diesel::delete(section_types)
//         .execute(conn)
//         .expect("Error deleting posts");
// }

pub fn parse_instructors(instructor_html: &str) -> Vec<String> {
    let instr_re: Regex = Regex::new("(?:<.*?>)*(?P<instructor>[^<>]+)(?:<.*?>)*").unwrap();
    let instructors = instr_re.captures_iter(instructor_html).map(|capture_group| String::from(&capture_group["instructor"]));
    instructors.collect()
}

pub fn parse_seats(seats_html: &str) -> (i32, i32, i32) {
    let re = "<strong>Maximum Enrollment</strong>: (?P<seats>\\d+) / \
         <strong>Seats Avail</strong>: (?P<available>\\d+)<br/>\
         <strong>Waitlist Total</strong>: (?P<waitlist>\\d+), (?P<mode>.*)";
    let seats_re: Regex = Regex::new(re).unwrap();
    let result = seats_re.captures_iter(seats_html).next().expect(&format!("Unable to parse: \n{}\nusing regex: \n{}", seats_html, re));
    (result["seats"].parse::<i32>().expect(&format!("Unable to parse seats from {}", &result["seats"])),
     result["available"].parse::<i32>().expect(&format!("Unable to parse available from {}", &result["available"])),
     result["waitlist"].parse::<i32>().expect(&format!("Unable to parse waitlist from {}", &result["waitlist"])))
}

pub fn parse_time(meets: &str) -> ([bool; 7], i64, i64) {
    let meets_re: Regex = Regex::new(
        "(?P<su>Su)?\
         (?P<mo>M)?\
         (?P<tu>T)?\
         (?P<we>W)?\
         (?P<th>Th)?\
         (?P<fr>F)?\
         (?P<sa>Sa)? \
         (?P<start_hr>\\d+):?(?P<start_min>\\d+)?(?P<start_am>a)?-\
         (?P<end_hr>\\d+):?(?P<end_min>\\d+)?(?P<end_am>a|p)?"
         ).unwrap();
    let result = meets_re.captures_iter(meets).next().unwrap();
    let days: [bool; 7] = [
        result.name("su").is_some(),
        result.name("mo").is_some(),
        result.name("tu").is_some(),
        result.name("we").is_some(),
        result.name("th").is_some(),
        result.name("fr").is_some(),
        result.name("sa").is_some()
    ];
    let start = (result.name("start_hr").and_then(|m| m.as_str().parse::<i64>().ok()).unwrap() * 60 +
                result.name("start_min").and_then(|m| m.as_str().parse::<i64>().ok()).unwrap_or(0) +
                if result.name("start_am").is_none() && 
                   result.name("end_am").map(|m| m.as_str() == "p").unwrap() &&
                   result.name("start_hr").map(|m| m.as_str() == "12").unwrap() { 12 * 60 } else { 0 })
                * 60 * 1000;
    let end = (result.name("end_hr").and_then(|m| m.as_str().parse::<i64>().ok()).unwrap() * 60 +
              result.name("end_min").and_then(|m| m.as_str().parse::<i64>().ok()).unwrap_or(0) +
              if result.name("end_am").map(|m| m.as_str() == "p").unwrap() &&
                 result.name("end_hr").map(|m| m.as_str() == "12").unwrap() { 12 * 60 } else { 0 })
              * 60 * 1000;

    println!("{:?}", days);
    println!("{:?}", start);
    println!("{:?}", end);
    return (days, start, end);
}

pub fn update_db(_update: bool, count: Option<u8>) -> Result<(), reqwest::Error> {
    let connection = establish_connection();

    let season = "fall";
    let year = 2019;
    let classes = scraper::scrape_classes(count)?;
    let details = scraper::scrape_details(&classes)?;

    // for d in &details {
    //     println!("{}", d.instructordetail_html)
    // }

    // Insert classes (not sections)
    let new_classes: Vec<NewClass> = details.iter().map(|d| NewClass {
        code: &d.code,
        full_name: &d.title,
        description: &d.description,
    }).collect();
    // for c in &new_classes {
    //     println!("INSERT {}", c.code);
    // }
    
    println!("Inserting semester.");
    // let semester_id = 1;
    let semester = NewSemester {
        year: year,
        season: &season
    };
    let semester_id: i32 = diesel::insert_into(schema::semesters::table)
        .values(&semester)
        .on_conflict((schema::semesters::year, schema::semesters::season))
        .do_update()
        .set(&semester)
        .returning(schema::semesters::id)
        .get_result(&connection)
        .expect("Error adding semester");

    println!("Inserting classes.");
        // .execute(&connection)
    // let inserted_classes: Vec<i32> = 
    diesel::insert_into(schema::classes::table)
        .values(&new_classes)
        // .on_conflict(schema::classes::code)
        // .do_nothing()
        .on_conflict_do_nothing()
        // .returning(schema::classes::id)
        // .do_update()
        // .set(schema::classes::full_name.eq(excluded(schema::classes::full_name)))
        // .set(schema::classes::code.eq(excluded(schema::classes::code)))
        // .set(&new_classes)
        // .get_results(&connection)
        .execute(&connection)
        .expect("Error saving classes");

    // Insert instructors
    
    let new_instructors: Vec<NewInstructor> = details
        .iter()
        .map(|d| parse_instructors(&d.instructordetail_html))
        .flatten()
        .map(|name|
            NewInstructor {
                full_name: name.clone(),
            }
        )
        .collect();
    
    println!("Inserting instructors.");
    diesel::insert_into(schema::instructors::table)
        .values(new_instructors)
        .on_conflict(schema::instructors::full_name)
        .do_nothing() // .do_update()
                      // .set(&new_instructors)
        .execute(&connection)
        // .get_results(&connection)
        .expect("Error saving instructors");

    let db_classes = schema::classes::dsl::classes
        .load::<Class>(&connection)
        .expect("Error loading classes to get IDs");
    let db_instructors = schema::instructors::dsl::instructors
        .load::<Instructor>(&connection)
        .expect("Error loading instructors to get IDs");
    let db_section_types = schema::section_types::dsl::section_types
        .load::<SectionType>(&connection)
        .expect("Error loading instructors to get IDs");
    let db_institutions = schema::institutions::dsl::institutions
        .load::<Institution>(&connection)
        .expect("Error loading instructors to get IDs");
    let db_instruction_modes = schema::instruction_modes::dsl::instruction_modes
        .load::<InstructionMode>(&connection)
        .expect("Error loading instructors to get IDs");
    let mut class_ids = HashMap::new();
    for c in &db_classes {
        class_ids.insert(&c.code, c.id);
    }
    let mut instructor_ids = HashMap::new();
    for c in &db_instructors {
        instructor_ids.insert(&c.full_name, c.id);
    }
    let mut section_type_ids = HashMap::new();
    for c in &db_section_types {
        section_type_ids.insert(&c.code, c.id);
    }
    let mut institution_ids = HashMap::new();
    for c in &db_institutions {
        institution_ids.insert(&c.code, c.id);
    }
    let mut instruction_mode_ids = HashMap::new();
    for c in &db_instruction_modes {
        instruction_mode_ids.insert(&c.code, c.id);
    }

    println!("Inserting sections.");
    let new_sections: Vec<NewSection> = classes.iter().zip(details.iter()).map(|(c, d)| {
        let (days, start, end) = parse_time(&c.meets);
        let (total_seats, available_seats, waitlist) = parse_seats(&d.seats);
        NewSection {
            crn: d.crn.parse::<i32>().expect(&format!("Cannot parse CRN {}", d.crn)),
            section_no: d.section.parse::<i32>().expect(&format!("Cannot parse section number {}", d.section)),
            parent_class: *class_ids.get(&d.code).expect(&format!("Unrecognized class code {}", d.code)),
            section_type: *section_type_ids.get(&c.schd).expect(&format!("Unrecognized section type {}", c.schd)),
            institution: *institution_ids.get(&d.campus).expect(&format!("Unrecognized institution {}", d.campus)),
            mode: *instruction_mode_ids.get(&d.instmode_html).expect(&format!("Unrecognized instruction mode {}", d.instmode_html)),

            semester: semester_id,
            start_time: PgTime(start),
            end_time: PgTime(end),
            
            monday: days[0],
            tuesday: days[1],
            wednesday: days[2],
            thursday: days[3],
            friday: days[4],
            saturday: days[5],
            sunday: days[6],

            instructor: *instructor_ids.get(&parse_instructors(&d.instructordetail_html)[0]).expect(&format!("Unrecognized instructor {}", d.instructordetail_html)),
            credits: d.hours.parse::<i32>().unwrap_or(0),
            total_seats: total_seats,
            available_seats: available_seats,
            waitlist: waitlist,

            is_cancelled: false,
            special_date_range: false,
            no_auto_enroll: false,
            // section_name: d.name,
        }
    }).collect();
    
    diesel::insert_into(schema::sections::table)
        .values(&new_sections)
        .on_conflict(schema::sections::crn)
        // .do_nothing()
        .do_update()
        // .set(new_sections.iter().next().unwrap())
        .set((
            schema::sections::section_no.eq(excluded(schema::sections::section_no)),
            schema::sections::parent_class.eq(excluded(schema::sections::parent_class)),
            schema::sections::section_type.eq(excluded(schema::sections::section_type)),
            schema::sections::institution.eq(excluded(schema::sections::institution)),
            schema::sections::mode.eq(excluded(schema::sections::mode)),
            schema::sections::semester.eq(excluded(schema::sections::semester)),
            schema::sections::start_time.eq(excluded(schema::sections::start_time)),
            schema::sections::end_time.eq(excluded(schema::sections::end_time)),
            schema::sections::monday.eq(excluded(schema::sections::monday)),
            schema::sections::tuesday.eq(excluded(schema::sections::tuesday)),
            schema::sections::wednesday.eq(excluded(schema::sections::wednesday)),
            schema::sections::thursday.eq(excluded(schema::sections::thursday)),
            schema::sections::friday.eq(excluded(schema::sections::friday)),
            schema::sections::saturday.eq(excluded(schema::sections::saturday)),
            schema::sections::sunday.eq(excluded(schema::sections::sunday)),
            schema::sections::instructor.eq(excluded(schema::sections::instructor)),
            schema::sections::credits.eq(excluded(schema::sections::credits)),
            schema::sections::total_seats.eq(excluded(schema::sections::total_seats)),
            schema::sections::available_seats.eq(excluded(schema::sections::available_seats)),
            schema::sections::waitlist.eq(excluded(schema::sections::waitlist)),
            schema::sections::is_cancelled.eq(excluded(schema::sections::is_cancelled)),
            schema::sections::special_date_range.eq(excluded(schema::sections::special_date_range)),
            schema::sections::no_auto_enroll.eq(excluded(schema::sections::no_auto_enroll)),
            schema::sections::section_name.eq(excluded(schema::sections::section_name))))
        .execute(&connection)
        // .get_result<>(&connection)
        .expect("Error saving sections");

    

    Ok(())
}