#!/bin/bash

set -ex

datasets="Area GDP Population"
col_Area="Land area (sq. km)"
col_GDP='GDP, PPP (current international $), 2010'
col_Population='Population, total, 2010'

for f in $datasets
do
    bin/delete-data.py "carbonmap:$f"
    eval col=\${col_$f}
    bin/load-data.py "carbonmap:$f" kiln-data/Maps/With\ alpha-2/Updated\ by\ Duncan/$f.csv countries "Alpha-2" "$col"
    bin/density-grid.py "carbonmap:$f" world-robinson > kiln-data/Maps/Cartogram\ data/"$f".density && \
    cart 1500 750 kiln-data/Maps/Cartogram\ data/"$f".density kiln-data/Maps/Cartogram\ data/"$f".cart
    bin/as-svg.py --dataset "carbonmap:$f" --cart kiln-data/Maps/Cartogram\ data/"$f".cart --map world-robinson --json --simplification 20000 > kiln-data/Maps/Cartogram\ data/$f.json
done

(
    echo "// This file is auto-generated. Please do not edit."
    echo 'var carbonmap_data = {};'
    for f in $datasets
    do
        echo -n "carbonmap_data.$f = "
        perl -pe 's/$/;/' kiln-data/Maps/Cartogram\ data/"$f".json
    done
) > kiln-output/data.js

bin/adhoc/dump-project-data.py carbonmap > kiln-data/dumped.csv
