#!/bin/bash

SCRAPEFILE=../data/json/mycuinfo.json

# Scrape new data
#cp $SCRAPEFILE $SCRAPEFILE.old
#python3 scrape.py login.json

# Update me on changes, if any
DIFFERENCES=$(python3 utils/find_differences.py "$SCRAPEFILE.old" "$SCRAPEFILE")
if [[ $? -eq 0 ]]; then
    SUBJECT="$(date) yourCUinfo auto-update"
    EMAIL="alcu5535@colorado.edu"
    echo -ne "$DIFFERENCES" | mail -s "$SUBJECT" "$EMAIL"
fi

# Update GitHub pages site
git add ../data/class_data.json
#git commit -m "Auto-update: $(date)"
#git push origin master
