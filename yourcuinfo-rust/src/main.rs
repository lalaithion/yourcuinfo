extern crate reqwest;
extern crate serde_json;

use rayon::prelude::*;
use reqwest::{Client};
use serde_json::{Value, Value::Array, Value::Null, json};
use std::collections::HashMap;
use std::io::prelude::*;
use std::fs::File;

const CLASSES_URL: &'static str = "https://classes.colorado.edu/api/?page=fose&route=search";
const DETAILS_URL: &'static str = "https://classes.colorado.edu/api/?page=fose&route=details";

fn get_classes(client: &Client, semester_code: &str) -> Value {
  let res = client.post(CLASSES_URL)
    .body(json!({
        "other": {"srcdb" : semester_code},
        "criteria": []
      }).to_string())
    .send();

  match res {
    Ok(mut r) => r.json().unwrap_or(Null),
    Err(_) => Null
  }
}

fn get_details(client: &Client, semester_code: &str, class_code: &str, course_number: &str) -> Value {
  println!("Retrieving class {}", class_code);

  let res = client.post(DETAILS_URL)
    .body(json!({
        "group": "code:".to_owned() + class_code,
        "key": "crn:".to_owned() + course_number,
        "srcdb": semester_code,
        "matched": "crn:".to_owned() + course_number
      }).to_string())
    .send();

  match res {
    Ok(mut r) => r.json().unwrap_or(Null),
    Err(_) => Null
  }
}

fn get_details_from_result(client: &Client, semester_code: &str, result: &Value) -> Value {
  let class_code = match &result["code"] {
    Value::String(s) => s,
    _ => return Null
  };

  let course_number = match &result["crn"] {
    Value::String(s) => s,
    _ => return Null
  };

  get_details(client, semester_code, &class_code, &course_number)
}

fn main() -> std::io::Result<()> {
  let semester_codes: HashMap<&str, &str> =
    [ ("Spring", "1"),
      ("Summer", "4"),
      ("Fall", "7") ].iter().cloned().collect();

  let year: &str = "2019";
  let semester: &str = "Fall";
  let semester_code: String = String::from("2")
    + year.get(2..4).unwrap_or("19")
    + semester_codes.get(semester).unwrap_or(&"1");

  let client = reqwest::Client::new();
  let classes: Value = get_classes(&client, &semester_code);

  println!("Retrieved classes");

  let details: Value = match &classes["results"] {
    Array(v) => {
        let res = v.par_iter()
          .map(|r| get_details_from_result(&client, &semester_code, &r))
          .collect();
        Array(res)
      }
    _ => Array(vec![]),
  };

  println!("Retrieved details");

  let mut file = File::create("classes.json")?;
  file.write_all(classes.to_string().as_bytes())?;

  let mut file = File::create("details.json")?;
  file.write_all(details.to_string().as_bytes())?;

  Ok(())
}
