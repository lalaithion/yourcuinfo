# #!/bin/bash
USAGE="Usage: $0 [-t threads] [-m mode] [-p] [-e address]"
SCRAPEFILE=../data/json/mycuinfo.json
THREADS=5
MODE="headless"

while getopts :ht:m:pe: option
do
  case "$option" in
    h)
      echo "$USAGE"
      echo "  -t Specify the number of threads to run (default 5)"
      echo "  -m Specify run mode as 'headless' (default) or 'windowed'"
      echo "  -p Push results to Github"
      echo "  -e Email diff"
      exit 0
      ;;
    t)
      if ! [[ "$OPTARG" =~ ^[0-9]+$ ]]; then
        echo "Thread count must be integer!"
        exit 1
      fi
      THREADS="$OPTARG"
      ;;
    m)
      if [[ "$OPTARG" == "headless" ]]; then
        MODE="$OPTARG"
      elif [[ "$OPTARG" == "windowed" ]]; then
        MODE="$OPTARG"
      else
        echo "Mode must be 'windowed' or 'headless'"
        exit 1
      fi
      ;;
    p)
      PUSH=1
      ;;
    e)
      EMAIL="$OPTARG"
      ;;
    *)
      echo "Unknown option: $OPTARG"
      echo "$USAGE"
      exit 1
    ;;
  esac
done

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
if [[ $EMAIL ]]; then
  SUBJECT="$(date) yourCUinfo auto-update"
  EMAIL="alcu5535@colorado.edu"
  DIFFERENCES=$(python3 utils/find_differences.py "$SCRAPEFILE.old" "$SCRAPEFILE" 2>&1)
  echo -ne "$DIFFERENCES" | mail -s "$SUBJECT" "$EMAIL"
fi

# Update GitHub pages site
DATAFILE=../data/class_data.json
if [[ $PUSH ]]; then
  git checkout gh-pages
  git add "$DATAFILE" "$SCRAPEFILE"
  git commit -m "Auto-update: $(date)"
  git push origin gh-pages
fi
