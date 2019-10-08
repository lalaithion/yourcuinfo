extern crate argparse;
extern crate reqwest;
extern crate db;

use self::db::*;

use argparse::{ArgumentParser, StoreTrue, StoreOption};

// pub fn create_post<'a>(conn: &PgConnection, title: &'a str, body: &'a str) -> Post {
//     use schema::posts;

//     let new_post = NewPost {
//         title: title,
//         body: body,
//     };

//     diesel::insert_into(posts::table)
//         .values(&new_post)
//         .get_result(conn)
//         .expect("Error saving new post")
// }

// fn update_db() -> Result<(), Box<dyn std::error::Error>> {
//     let list_endpoint = "https://classes.colorado.edu/api/?page=fose&route=search";
//     // let detail_endpoint = "https://classes.colorado.edu/api/?page=fose&route=details";
//     let query = json!({
//         "other": {
//             "srcdb": "2191",
//         },
//         "criteria": []
//     }).to_string();

//     let client = reqwest::Client::new();
//     let mut resp = client.post(list_endpoint)
//         .body(query)
//         .send()?;
//     println!("{:#?}", resp);
//     let classes: ListResponse = match serde_json::from_str(&resp.text()?) {
//         Err(m) => panic!(format!("Unable to parse response from class list. Error: {}", m)),
//         Ok(x) => x
//     };

//     Ok(())
// }

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // let mut semester = None<String>
    let mut update = false;
    let mut count = None::<u8>;
    {
        let mut ap = ArgumentParser::new();
        ap.set_description("Create the class database.");
        ap.refer(&mut update)
            .add_option(&["--update"], StoreTrue,
            "Update the classes.");
        ap.refer(&mut count)
            .add_option(&["--count"], StoreOption,
            "Read a set number of classes.");
        ap.parse_args_or_exit();
    }

    update_db(update, count)?;

    Ok(())
}