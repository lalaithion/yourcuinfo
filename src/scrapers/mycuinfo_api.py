import requests, pdb, json, time

def get_classes(srcdb):
    search_url = 'https://classes.colorado.edu/api/?page=fose&route=search'

    search_request = {
        "other": {
            "srcdb": '2191'#srcdb
        },
        "criteria": [
            { "field": "hours", "value": ">=0" },
            { "field": "hours_min", "value": ">=0" }
        ]
    }

    response = requests.post(search_url, json=search_request)

    if response.status_code is 200:
        return response.json()
    else:
        raise Exception("Got status code: %d" % (resonse.status_code))

def get_details(srcdb, code, crn):
    details_url = 'https://classes.colorado.edu/api/?page=fose&route=details'

    crn_str = "crn:" + crn
    details_request = {
        "group": "code:" + code,
        "key": crn_str,
        "srcdb": srcdb,
        "matched": crn_str,
    }

    response = requests.post(details_url, json=details_request)

    if response.status_code is 200:
        return response.json()
    else:
        raise Exception("Got status code: %d" % (resonse.status_code))

def main():
    year = 2019
    semester = "spring"

    year_last_2_digits = str(year)[-2:]
    semester_number = { "spring": "1", "summer": "4", "fall": "7" }[semester]

    srcdb = "2" + year_last_2_digits + semester_number

    start = time.time()
    print("Starting parse at")
    # classes = get_classes(srcdb)
    #
    # with open("classes.json", "w") as f:
    #     f.write(json.dumps(classes))

    with open("classes.json") as f:
        classes = json.loads(f.read())

    details = {}
    try:
        for result in classes["results"]:
            code = result["code"]
            crn = result["crn"]
            print("On class: %s-%s (%s/%d)" % (code, result["no"], result["key"], classes["count"]))
            details[crn] = get_details(srcdb, code, crn)

    except Exception as e:
        print("Error:", e)
        # pdb.set_trace()

    with open("details.json", "w") as f:
        f.write(json.dumps(details))

    end = time.time()

    print("Total parse time: ", end - start)


# data = { 'Content-Type': 'application/json' }
# params = {'sessionKey': '9ebbd0b25760557393a43064a92bae539d962103', 'format': 'xml', 'platformId': 1}


# {
#     "srcdb": "2191",
#     "count": 4502,
#     "results": [
#         {
#             "key": "1",
#             "code": "ACCT 3220",
#             "title": "Corporate Financial Reporting 1",
#             "crn": "26499",
#             "no": "001",
#             "total": "3",
#             "schd": "LEC",
#             "stat": "W",
#             "isCancelled": "",
#             "mpkey": "2026",
#             "meets": "MW 2-3:15p",
#             "instr": "F. Tice",
#             "start_date": "2019-01-14",
#             "end_date": "2019-05-02",
#             "srcdb": "2191"
#         },
#         {
#             "key": "2",
#             "code": "ACCT 3220",
#             "title": "Corporate Financial Reporting 1",
#             "crn": "26500",
#             "no": "002",
#             "total": "3",
#             "schd": "LEC",
#             "stat": "W",
#             "isCancelled": "",
#             "mpkey": "2029",
#             "meets": "MW 12:30-1:45p",
#             "instr": "F. Tice",
#             "start_date": "2019-01-14",
#             "end_date": "2019-05-02",
#             "srcdb": "2191"
#         },

# {
#     "key": "2516",
#     "inst": "CUBLD",
#     "stat": "A",
#     "mpkey": "2318",
#     "hours": "0",
#     "hours_min": "0",
#     "gmods": "LTR,NOC,PF4",
#     "code": "CHEM 6801",
#     "section": "800",
#     "crn": "20294",
#     "title": "Departmental Research Seminar",
#     "last_updated": "Mon Nov 26 2018 21:56:19 GMT-0600 (CST)",
#     "hours_text": "0 Credit Hour Seminar",
#     "seats": "<strong>Maximum Enrollment</strong>: 30 / <strong>Seats Avail</strong>: 30<br/><strong>Waitlist Total</strong>: 0, Auto-Enroll",
#     "grd": "Student Option",
#     "xlist": "",
#     "campus": "Boulder Main Campus",
#     "instmode_html": "In Person",
#     "dates_html": "2018-08-27 through 2018-12-13",
#     "restrict_info": "Restricted to graduate students only.",
#     "clssnotes": "",
#     "description": "Lectures by visiting scientists and occasionally by staff members and graduate students on topics of current research. Meets once a week. Required for all graduate students in chemistry.",
#     "meeting_html": "<div class=\"meet\">MTWThF 4pm-5:50pm in <a href=\"http://www.colorado.edu/campusmap/map.html?bldg=CHEM\" target=\"_blank\">Cristol Chem &amp; Biochem Bldg 142</a></div>",
#     "exams_html": "",
#     "instructordetail_html": "",
#     "attributes": "",
#     "law": "",
#     "eval_links": "<a href=\"https://fcq.colorado.edu/scripts/broker.exe?_PROGRAM=fcqlib.fcqdata.sas&subj=CHEM&crse=6801\" target=\"_blank\">Course Evaluations</a><br/>",
#     "books_html": "<a class=\"btn\" target=\"_blank\" href=\"https://www.cubookstore.com/booklist.aspx?catalogid=20294&uterm=Fall2018\">PURCHASE BOOKS</a>",
#     "linkedhtml": "",
#     "all_sections": "<div class=\"course-sections\" role=\"grid\" aria-readonly=\"true\"><div role=\"row\"><div role=\"columnheader\" scope=\"col\">Class Nbr</div><div role=\"columnheader\" scope=\"col\">Section #</div><div role=\"columnheader\" scope=\"col\">Type</div><div role=\"columnheader\" scope=\"col\">Campus</div><div role=\"columnheader\" scope=\"col\">Meets</div><div role=\"columnheader\" scope=\"col\">Instructor</div><div role=\"columnheader\" scope=\"col\">Status</div><div role=\"columnheader\" scope=\"col\">Dates</div></div><a role=\"row\" href=\"#\" class=\"course-section\" data-action=\"result-detail\" data-group=\"code:CHEM 6801\" data-srcdb=\"2187\" data-key=\"crn:20294\"><div role=\"rowheader\" class=\"course-section-crn\"><span class=\"header-text\">Class Nbr: </span> 20294</div><div role=\"gridcell\" class=\"course-section-section\"><span class=\"header-text\">Section #: </span> 800</div><div role=\"gridcell\" class=\"course-section-schd\"><span class=\"header-text\">Type: </span> SEM</div><div role=\"gridcell\" class=\"course-section-camp\"><span class=\"header-text\">Campus: </span> Main</div><div role=\"gridcell\" class=\"course-section-mp\"><span class=\"header-text\">Meets: </span> MTWThF 4-5:50p</div><div role=\"gridcell\" class=\"course-section-instr\"><span class=\"header-text\">Instructor: </span> </div><div role=\"gridcell\" class=\"course-section-stat\"><span class=\"header-text\">Status: </span> Open</div><div role=\"gridcell\" class=\"course-section-dates\"><span class=\"header-text\">Dates: </span> 08-27 to 12-13</div></a></div>",
#     "srcdb": "2187"
# }

if __name__ == "__main__":
    main()
