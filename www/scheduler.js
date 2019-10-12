var calendar = new Calendar('#calendar');

function previewOption(option) {
    calendar.clear();
    for(section of option.sections) {
        calendar.addSection(section);
    }
}

function previewBest(course_codes) {
    var options = fitSchedule(course_codes);
    var best = findBest(options);
    previewOption(best);
}

function findBest(options) {
    return options.reduce((max, option) => option.raking > max.ranking ? option : max);
}

// Constraints: array of functions that take a section, return a number in the range [0,1].
// 0 means will not take. Any other number will involve rankings.
function fitSchedule(course_codes, constraints) {
    constraints = constraints || [];
    var choices = course_codes.reduce((acc, course_code) => {
        var sections = getSectionsOfCourse(course_code);
        var sections_by_type = Object.keys(SECTION_TYPES).map((t) => sections.filter((section) => section.type == t));
        return acc.concat([...sections_by_type.filter((sections) => sections.length > 0)])
    }, []);

    function findOptionSet(chosen_sections, current_ranking, remaining) {
        var sections = remaining[0];
        var rest = remaining.slice(1);
        // console.log(sections, rest)

        var ranked_sections = sections.reduce((valid_options, section) => {
            // Check for collisions with previously chosen sections
            for(choice of chosen_sections) {
                if(section.conflictsWith(choice)) return valid_options;
            }

            // Apply constraints, potentially lowering current ranking
            var updated_ranking = constraints.reduce((rank, constraint) => rank *= constraint(section), current_ranking);
            if(updated_ranking == 0) return valid_options;

            // If there are still choices, recurse on those.
            var updated_chosen_sections = chosen_sections.concat([section]);
            if(rest.length > 0) {
                return valid_options.concat(findOptionSet(updated_chosen_sections, updated_ranking, rest));
            }
            // If there are no choices, just return.
            return valid_options.concat([{
                sections: updated_chosen_sections,
                ranking: updated_ranking,
            }]);
        }, []);
        // We can drop any sections with a ranking of zero.
        return ranked_sections.filter((section) => section.ranking > 0)
    }
    return findOptionSet([], 1, choices);
}