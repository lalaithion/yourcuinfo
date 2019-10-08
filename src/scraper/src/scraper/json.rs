use serde::{Deserialize, Serialize};

#[allow(non_snake_case)]
#[derive(Serialize, Deserialize)]
pub struct ClassResponse {
    pub key: String,
    pub code: String,
    pub title: String,
    pub crn: String,
    pub no: String,
    pub total: String,
    pub schd: String,
    pub stat: String,
    pub isCancelled: String,
    pub mpkey: String,
    pub meets: String,
    pub instr: String,
    pub start_date: String,
    pub end_date: String,
    pub srcdb: String,
}

#[derive(Serialize, Deserialize)]
pub struct ListResponse {
    pub srcdb: String,
    pub count: u32,
    pub results: Vec<ClassResponse>,
}

#[derive(Serialize, Deserialize)]
pub struct DetailsResponse {
    pub key: String,
    pub inst: String,
    pub stat: String,
    pub mpkey: String,
    pub hours: String,
    pub hours_min: String,
    pub gmods: String,
    pub code: String,
    pub section: String,
    pub crn: String,
    pub title: String,
    pub last_updated: String,
    pub hours_text: String,
    pub seats: String,
    pub grd: String,
    pub xlist: String,
    pub campus: String,
    pub instmode_html: String,
    pub dates_html: String,
    pub restrict_info: String,
    pub clssnotes: String,
    pub description: String,
    pub meeting_html: String,
    pub exams_html: String,
    pub instructordetail_html: String,
    pub attributes: String,
    pub law: String,
    pub eval_links: String,
    pub books_html: String,
    pub linkedhtml: String,
    pub all_sections: String,
    pub srcdb: String,
}