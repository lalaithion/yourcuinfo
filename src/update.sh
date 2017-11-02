#!/bin/bash

SCRAPEFILE=../data/json/mycuinfo.json

# Scrape new data
cp $SCRAPEFILE $SCRAPEFILE.old
python3 scrape.py login.json
python3 formatter.py

# Update me on changes, if any
SUBJECT="$(date) yourCUinfo auto-update"
EMAIL="alcu5535@colorado.edu"
DIFFERENCES=$(python3 utils/find_differences.py "$SCRAPEFILE.old" "$SCRAPEFILE" 2>&1)
echo -ne "$DIFFERENCES" | mail -s "$SUBJECT" "$EMAIL"

# Update GitHub pages site
DATAFILE=../data/class_data.json
git add "$DATAFILE" "$SCRAPEFILE"
git commit -m "Auto-update: $(date)"
git push origin master
