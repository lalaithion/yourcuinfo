#[macro_use]
extern crate diesel;
extern crate dotenv;
extern crate regex;
extern crate log;

pub mod schema;
pub mod models;
pub mod scraper;

use std::{env};
use std::error::Error;
use diesel::prelude::*;
use diesel::pg::PgConnection;
use diesel::pg::data_types::{PgTime};
use dotenv::dotenv;
use regex::{Regex};

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

pub fn parse_instructors(instructor_html: &str) -> Result<Vec<String>, Box<dyn Error>> {
    let instr_re: Regex = Regex::new("(?:<.*?>)*(?P<instructor>[^<>]+)(?:<.*?>)*")?;
    let instructors: Vec<String> = instr_re.captures_iter(instructor_html)
        .try_fold(Vec::<String>::new(), |mut acc, capture_group| -> Result<Vec<String>, Box<dyn Error>> {
            acc.push(String::from(capture_group.name("instructor").ok_or("Could not parse instructor")?.as_str()));
            Ok(acc)
        })?;
    Ok(instructors)
}

pub fn parse_seats(seats_html: &str) -> Result<(i32, i32, i32), Box<dyn Error>> {
    let re = "<strong>Maximum Enrollment</strong>: (?P<seats>\\d+) / \
         <strong>Seats Avail</strong>: (?P<available>\\d+)\
         (<br/><strong>Waitlist Total</strong>: (?P<waitlist>\\d+), (?P<mode>.*))?";
    let seats_re: Regex = Regex::new(re)?;
    let result = seats_re.captures_iter(seats_html).next().ok_or(format!("Unable to parse: \n{}\nusing regex: \n{}", seats_html, re))?;

    let seats = result.name("seats").ok_or("No 'seats' field provided").and_then(
        |m| m.as_str().parse::<i32>().map_err(|_| "Could not parse 'seats' field"))?;
    let available = result.name("available").ok_or("No 'available' field provided").and_then(
        |m| m.as_str().parse::<i32>().map_err(|_| "Could not parse 'available' field"))?;

    match result.name("waitlist") {
        Some(x) => {
            let waitlist = x.as_str().parse::<i32>().map_err(|_| "Could not parse 'waitlist' field")?;
            Ok((seats, available, waitlist))
        },
        None => Ok((seats, available, 0))
    }
}

pub fn parse_time(meets: &str) -> Result<([bool; 7], Option<i64>, Option<i64>), Box<dyn Error>> {
    if meets == "No Time Assigned" || meets == "Meets online" {
        return Ok(([false; 7], None, None));
    }
    // println!("Parsing meet");

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
         )?;
    let result = meets_re.captures_iter(meets).next().ok_or(format!("Cannot match meeting time regex for string '{}'", meets))?;
    let days = [
        result.name("su").is_some(),
        result.name("mo").is_some(),
        result.name("tu").is_some(),
        result.name("we").is_some(),
        result.name("th").is_some(),
        result.name("fr").is_some(),
        result.name("sa").is_some()
    ];

    let parse_int = |name: &str| 
        result.name(name).and_then(|m| m.as_str().parse::<i64>().ok())
                         .ok_or(format!("Couldn't parse field: {}", name));

    let start_hr = parse_int("start_hr")?;
    let end_hr = parse_int("end_hr")?;
    let start_min = parse_int("start_min");
    let end_min = parse_int("end_min");
    let start_am = result.name("start_am").map(|m| m.as_str());
    let end_am = result.name("end_am").map(|m| m.as_str()).ok_or("Could not parse end_am")?;

    // println!("{} {} {:?} {:?} {:?} {}", start_hr, end_hr, start_min, end_min, start_am, end_am);
    let start = Some(
        (start_hr * 60 + start_min.unwrap_or(0) +
        if start_am.is_none() && end_am == "p" && start_hr == 12 { 12 * 60 } else { 0 })
        * 60 * 1000);

    let end = Some(
        (end_hr * 60 + end_min.unwrap_or(0) +
        if end_am == "p" && end_hr == 12 { 12 * 60 } else { 0 })
        * 60 * 1000);

    return Ok((days, start, end));
}

pub fn update_db(threads: u8, count: Option<u8>) -> Result<(), Box<dyn Error>> {
    // TODO: Pass as command line args
    let season = "fall";
    let year = 2019;
    let semester = NewSemester {
        year: year,
        season: &season
    };
    
    let connection = establish_connection();

    // Add semester to DB
    let semester_id: i32 = diesel::insert_into(schema::semesters::table)
        .values(&semester)
        .on_conflict((schema::semesters::year, schema::semesters::season))
        .do_update()
        .set(&semester)
        .returning(schema::semesters::id)
        .get_result(&connection)
        .expect("Error adding semester to database");

    let class_stream = scraper::scrape_stream(threads, count);
    for (i, scrape_result) in class_stream.iter().enumerate() {
        if i % 100 == 0 {
            println!("On class #{}", i);
        }
        
        // TODO: Make neater
        let (class, details) = match scrape_result {
            Err(msg) => {
                println!("Error: {}", msg);
                continue
            }
            Ok(x) => x,
        };

        // Lambda acts as try/catch
        let result = (|| -> Result<(), Box<dyn Error>> {
            // Add parent class to DB
            let new_class = NewClass {
                code: &details.code,
                full_name: &details.title,
                description: &details.description,
            };
            let class_id = diesel::insert_into(schema::classes::table)
                .values(&new_class)
                .returning(schema::classes::id)
                .on_conflict(schema::classes::code)
                .do_update()
                .set(&new_class)
                .execute(&connection)? as i32;
            
            // Add instructors to DB
            let instructor_ids: Vec<i32> = parse_instructors(&details.instructordetail_html)?
            .iter().try_fold(Vec::<i32>::new(), |mut acc, name| -> Result<Vec<i32>, Box<dyn Error>> {
                let new_instructor = NewInstructor {
                    full_name: name.clone(),
                };
                let instructor_id = diesel::insert_into(schema::instructors::table)
                .values(&new_instructor)
                .returning(schema::instructors::id)
                .on_conflict(schema::instructors::full_name)
                .do_update()
                .set(&new_instructor)
                .execute(&connection)?;
                acc.push(instructor_id as i32);
                Ok(acc)
            })?;
            
            let (days, start, end) = parse_time(&class.meets)?;
            let (total_seats, available_seats, waitlist) = parse_seats(&details.seats)?;
            // TODO: Optional credits?
            let credits = match details.hours.as_str() {
                "" => 0.0,
                hours => hours.parse::<f32>().map_err(|_| format!("Unable to parse hour string: {}", hours))?
            };
            let section = NewSection {
                crn: details.crn.parse::<i32>().map_err(|_| format!("Unable to parse CRN: {}", details.crn))?,
                section_no: &details.section,
                parent_class: class_id,
                section_type: 1, // TODO: Implement
                institution: 1, // TODO: Implement
                mode: 1, // TODO: Implement

                semester: semester_id,
                start_time: start.map(|time| PgTime(time)),
                end_time: end.map(|time| PgTime(time)),
                
                monday: days[0],
                tuesday: days[1],
                wednesday: days[2],
                thursday: days[3],
                friday: days[4],
                saturday: days[5],
                sunday: days[6],

                instructor: instructor_ids,
                credits: credits,
                total_seats: total_seats,
                available_seats: available_seats,
                waitlist: waitlist,

                is_cancelled: false,
                special_date_range: false,
                no_auto_enroll: false,
                // section_name: details.name,
            };

            diesel::insert_into(schema::sections::table)
                .values(&section)
                .on_conflict(schema::sections::crn)
                .do_update()
                .set(&section)
                .execute(&connection)?;
            
            Ok(())
        })();

        match result {
            Err(msg) => println!("Error on {}: {}.", &details.code, msg),
            _ => ()
        };
    }

    Ok(())
}