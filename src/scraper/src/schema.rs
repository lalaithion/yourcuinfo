table! {
    classes (id) {
        id -> Int4,
        code -> Varchar,
        full_name -> Varchar,
        description -> Nullable<Varchar>,
    }
}

table! {
    institutions (id) {
        id -> Int4,
        name -> Varchar,
    }
}

table! {
    instruction_modes (id) {
        id -> Int4,
        mode -> Varchar,
    }
}

table! {
    instructors (id) {
        id -> Int4,
        full_name -> Varchar,
    }
}

table! {
    section_types (id) {
        id -> Int4,
        #[sql_name = "type"]
        type_ -> Varchar,
    }
}

table! {
    sections (crn) {
        crn -> Int4,
        section_no -> Int4,
        parent_class -> Varchar,
        section_type -> Int4,
        institution -> Nullable<Int4>,
        mode -> Nullable<Int4>,
        semester -> Int4,
        start_time -> Nullable<Time>,
        end_time -> Nullable<Time>,
        monday -> Nullable<Bool>,
        tuesday -> Nullable<Bool>,
        wednesday -> Nullable<Bool>,
        thursday -> Nullable<Bool>,
        friday -> Nullable<Bool>,
        saturday -> Nullable<Bool>,
        sunday -> Nullable<Bool>,
        instructor -> Nullable<Int4>,
        credits -> Nullable<Int4>,
        total_seats -> Nullable<Int4>,
        available_seats -> Nullable<Int4>,
        waitlist -> Nullable<Int4>,
        is_cancelled -> Nullable<Bool>,
        special_date_range -> Nullable<Bool>,
        no_auto_enroll -> Nullable<Bool>,
        section_name -> Nullable<Text>,
    }
}

table! {
    semesters (id) {
        id -> Int4,
        year -> Int4,
        season -> Varchar,
    }
}

joinable!(sections -> institutions (institution));
joinable!(sections -> instruction_modes (mode));
joinable!(sections -> instructors (instructor));
joinable!(sections -> section_types (section_type));
joinable!(sections -> semesters (semester));

allow_tables_to_appear_in_same_query!(
    classes,
    institutions,
    instruction_modes,
    instructors,
    section_types,
    sections,
    semesters,
);
