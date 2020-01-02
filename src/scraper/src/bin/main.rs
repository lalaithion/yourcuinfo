extern crate argparse;
extern crate reqwest;
extern crate db;

use self::db::*;

use argparse::{ArgumentParser, Store, StoreTrue, StoreOption};
use std::error::Error;

fn main() -> Result<(), Box<dyn Error>> {
    // let mut semester = None<String> // TODO: Add as command line arg
    let mut update = false;
    let mut count = None::<u8>;
    let mut threads = 1;
    {
        let mut ap = ArgumentParser::new();
        ap.set_description("Create the class database.");
        ap.refer(&mut update)
            .add_option(&["--update"], StoreTrue,
            "Update the classes.");
        ap.refer(&mut count)
            .add_option(&["--count"], StoreOption,
            "Read a set number of classes.");
        ap.refer(&mut threads)
            .add_option(&["--threads"], Store,
            "Number of threads to use.");
        ap.parse_args_or_exit();
    }

    if threads == 1 {
        println!("Running in single-threaded mode is very slow: consider using multiple threads.");
    }

    update_db(threads, count)
}