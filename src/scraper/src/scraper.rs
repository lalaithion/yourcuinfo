extern crate reqwest;
extern crate serde_json;

pub mod json;

use serde_json::{json};
use std::collections::HashMap;
use self::json::{ClassResponse, DetailsResponse, ListResponse};

const CLASSES_URL: &'static str = "https://classes.colorado.edu/api/?page=fose&route=search";
const DETAILS_URL: &'static str = "https://classes.colorado.edu/api/?page=fose&route=details";

fn get_classes(semester_code: &str) -> Result<ListResponse, reqwest::Error> {
  let client = reqwest::Client::new();
  let res: ListResponse = client.post(CLASSES_URL)
    .body(json!({
        "other": {"srcdb" : semester_code},
        "criteria": []
      }).to_string())
    .send()?
    .json()?;

  Ok(res)
}

fn get_details(semester_code: &str, class_code: &str, course_number: &str) -> Result<DetailsResponse, reqwest::Error> {
  let client = reqwest::Client::new();
  let res: DetailsResponse = client.post(DETAILS_URL)
    .body(json!({
        "group": "code:".to_owned() + class_code,
        "key": "crn:".to_owned() + course_number,
        "srcdb": semester_code,
        "matched": "crn:".to_owned() + course_number
      }).to_string())
    .send()?
    .json()?;

  Ok(res)
}

fn get_details_from_result(semester_code: &str, result: &ClassResponse) -> Result<DetailsResponse, reqwest::Error> {
  let class_code = &result.code;
  let crn = &result.crn;

  get_details(semester_code, &class_code, &crn)
}

pub fn scrape(_count: Option<u8>) -> Result<Vec<DetailsResponse>, reqwest::Error> {
  let semester_codes: HashMap<&str, &str> =
    [ ("Spring", "1"),
      ("Summer", "4"),
      ("Fall", "7")].iter().cloned().collect();

  let year: &str = "2019";
  let semester: &str = "Fall";

  let semester_code: String = String::from("2")
    + year.get(2..4).unwrap_or("19")
    + semester_codes.get(semester).unwrap_or(&"1");

  let classes = get_classes(&semester_code)?;

  let details = classes.results.iter().take(20)
        .map(|r| match get_details_from_result(&semester_code, r) {
          Ok(x) => x,
          _ => panic!("Oops")
        }).collect();

  Ok(details)
}