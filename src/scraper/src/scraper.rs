extern crate reqwest;
extern crate serde_json;

pub mod json;

use serde_json::{json};
use std::collections::{HashMap, VecDeque};
use self::json::{ClassResponse, DetailsResponse, ListResponse};
use std::thread;
use std::sync::{Arc, Mutex, mpsc};

const CLASSES_URL: &'static str = "https://classes.colorado.edu/api/?page=fose&route=search";
const DETAILS_URL: &'static str = "https://classes.colorado.edu/api/?page=fose&route=details";

fn get_classes(count: Option<u8>, semester_code: &str) -> Result<Vec<ClassResponse>, reqwest::Error> {
  match count {
    Some(x) => println!("Scraping {} classes.", x),
    _ => println!("Scraping all available classes")
  };

  let client = reqwest::Client::new();
  let mut res: ListResponse = client.post(CLASSES_URL)
    .body(json!({
        "other": {"srcdb" : semester_code},
        "criteria": []
      }).to_string())
    .send()?
    .json()?;

  if count.is_some() {
    res.results.truncate(count.unwrap() as usize);
  }

  Ok(res.results)
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

fn get_class_details(result: &ClassResponse) -> Result<DetailsResponse, reqwest::Error> {
  let class_code = &result.code;
  let crn = &result.crn;
  let semester_code = &result.srcdb;

  get_details(semester_code, class_code, crn)
}

pub fn scrape_classes(count: Option<u8>) -> Result<Vec<ClassResponse>, reqwest::Error> {
  let semester_codes: HashMap<&str, &str> =
    [ ("Spring", "1"),
      ("Summer", "4"),
      ("Fall", "7")].iter().cloned().collect();

  let year: &str = "2019";
  let semester: &str = "Fall";

  let semester_code: String = String::from("2")
    + year.get(2..4).unwrap_or("19")
    + semester_codes.get(semester).unwrap_or(&"1");

  let classes = get_classes(count, &semester_code)?;

  Ok(classes)
}

pub fn scrape_stream(threads: u8, count: Option<u8>) -> mpsc::Receiver<Result<(ClassResponse, DetailsResponse), reqwest::Error>> {
  let class_queue = VecDeque::from(scrape_classes(count).unwrap());
  let mutex_master = Arc::new(Mutex::new(class_queue));

  let (tx_master, rx) = mpsc::channel();
  for _ in 0..threads {
    let tx = mpsc::Sender::clone(&tx_master);
    let queue_mutex = Arc::clone(&mutex_master);
    thread::spawn(move || {
      loop {
        let class_data;
        {
          let mut queue = queue_mutex.lock().unwrap();
          if queue.is_empty() {
            break
          }
          class_data = queue.pop_front().unwrap();
        }
        let class_details = get_class_details(&class_data);
        let payload = class_details.map(|details| (class_data, details));
        tx.send(payload).unwrap();
      }
    });
  }
  rx
}