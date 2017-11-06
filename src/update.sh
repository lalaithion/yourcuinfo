#!/bin/bash

SCRAPEFILE=../data/json/mycuinfo.json

# Scrape new data
cp $SCRAPEFILE $SCRAPEFILE.old
python3 scrape.py login.json
if [[ $? -ne 0 ]]; then
    echo "Error during scrape."
    exit 1
fi

python3 formatter.py
if [[ $? -ne 0 ]]; then
    echo "Error during formatting."
    exit 1
fi

# Update me on changes, if any
SUBJECT="$(date) yourCUinfo auto-update"
EMAIL="alcu5535@colorado.edu"
DIFFERENCES=$(python3 utils/find_differences.py "$SCRAPEFILE.old" "$SCRAPEFILE" 2>&1)
echo -ne "$DIFFERENCES" | mail -s "$SUBJECT" "$EMAIL"

# Update GitHub pages site
DATAFILE=../data/class_data.json
git checkout gh-pages
git add "$DATAFILE" "$SCRAPEFILE"
git commit -m "Auto-update: $(date)"
git push origin master
