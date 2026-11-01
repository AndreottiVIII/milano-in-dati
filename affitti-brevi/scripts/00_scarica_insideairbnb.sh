cd "C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/affitti-brevi/raw/insideairbnb" || exit 1
UA="milano-in-dati research (non-commercial)"
for d in 2026-09-19 2026-06-25 2026-03-27 2025-12-26; do
  mkdir -p $d
  for f in data/listings.csv.gz visualisations/neighbourhoods.geojson visualisations/neighbourhoods.csv data/calendar.csv.gz data/reviews.csv.gz; do
    b=$(basename $f)
    [ -s $d/$b ] || { curl -sL -A "$UA" -o $d/$b.part https://data.insideairbnb.com/italy/lombardy/milan/$d/$f && mv $d/$b.part $d/$b; sleep 3; }
    echo "$(date +%T) $d $b $(stat -c %s $d/$b)"
  done
done
echo DONE
