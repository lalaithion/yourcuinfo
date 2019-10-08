#[macro_use]
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
use dotenv::dotenv;
use std::env;
use regex::Regex;

use self::models::*;
use self::scraper::scrape;

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

pub fn delete_from_db(conn: &PgConnection) {
    use self::schema::section_types::dsl::*;

    // let target = args().nth(1).expect("Expected a target to match against");
    // let pattern = format!("%{}%", target);

    diesel::delete(section_types)
        .execute(conn)
        .expect("Error deleting posts");
}

pub fn update_db(_update: bool, count: Option<u8>) -> Result<(), reqwest::Error> {
    let connection = establish_connection();

    let details = scrape(count)?;
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
    
    let inserted_classes: Vec<Class> = diesel::insert_into(schema::classes::table)
        .values(&new_classes)
        .on_conflict(schema::classes::code)
        .do_nothing()
        // .do_update()
        // .set(schema::classes::full_name.eq(excluded(schema::classes::full_name)))
        // .set(schema::classes::code.eq(excluded(schema::classes::code)))
        // .set(&new_classes)
        .get_results(&connection)
        .expect("Error saving classes");

    // for c in &inserted_classes {
    //     println!("QUERY  {}: {}", c.id, c.code);
    // }

    let classes = schema::classes::dsl::classes
        .load::<Class>(&connection)
        .expect("Error loading classes to get IDs.");
    let instructors = schema::instructors::dsl::instructors
        .load::<Instructor>(&connection)
        .expect("Error loading instructors to get IDs.");
    let mut classIDs = HashMap::new();
    for c in &classes {
        classIDs.insert(&c.code, c.id);
    }
    let mut instructorIDs = HashMap::new();
    for c in &instructors {
        instructorIDs.insert(&c.full_name, c.id);
    }

    // Insert instructors
    let instr_re: Regex = Regex::new("(?:<.*?>)*([^<>]+)(?:<.*?>)*").unwrap();
    let new_instructors: Vec<NewInstructor> = details.iter().map(|d|
        instr_re.captures_iter(&d.instructordetail_html).map(|cap| {
            NewInstructor {
                full_name: String::from(&cap[1]),
            }
        })
    ).flatten().collect();
    
    let inserted_instructors: Vec<Instructor> = 
        diesel::insert_into(schema::instructors::table)
        .values(new_instructors)
        .on_conflict(schema::instructors::full_name)
        .do_nothing() // .do_update()
                      // .set(&new_instructors)
        // .execute(&connection)
        .get_results(&connection)
        .expect("Error saving instructors");

    // Insert sections.
    let new_sections: Vec<NewSection> = details.iter().map(|d|
        NewSection {
            crn: d.crn.parse::<i32>().unwrap(),
            section_no: d.section.parse::<i32>().unwrap(),
            parent_class: classIDs.get(d.code), // REFERENCES classes NOT NULL,
            section_type: 1, // REFERENCES section_types NOT NULL,
            institution: 1, // REFERENCES institutions,
            mode: 1, // REFERENCES instruction_modes,

            semester: 1, // REFERENCES semesters NOT NULL,
            // start_time: 1,
            // end_time: 1,
            
            // monday: true,
            // tuesday: true,
            // wednesday: true,
            // thursday: true,
            // friday: true,
            // saturday: true,
            // sunday: true,

            // instructor: 1, // REFERENCES instructors,
            // credits: 1,
            // total_seats: 1,
            // available_seats: 1,
            // waitlist: 1,

            // is_cancelled: true,
            // special_date_range: true,
            // no_auto_enroll: true,
            // section_name: d.name,
        }
    ).collect();
    
    diesel::insert_into(schema::sections::table)
        .values(new_sections)
        .on_conflict(schema::sections::crn)
        .do_nothing() // .do_update()
                      // .set(&new_sections)
        .execute(&connection)
        // .get_result<>(&connection)
        .expect("Error saving sections");

    

    Ok(())
}