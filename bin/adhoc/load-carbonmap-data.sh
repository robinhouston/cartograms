#!/bin/bash

set -ex

all_datasets="Area Population GDP  Extraction Emissions Consumption Historical Reserves  PeopleAtRisk SeaLevel Poverty"
datasets="${1-${all_datasets}}"

col_Area="Land area (sq. km)"
col_Population='Population, total, 2010'
col_GDP='GDP, PPP (current international $), 2010'

col_Extraction="CO2 from fossil fuels extracted, 2010"
col_Emissions="CO2 from fossil fuel use (million tonnes, 2009)"
col_Consumption="Consumption footprint, million tonnes CO2, 2010"
col_Historical="Cumulative CO2 emissions from energy, 1850–2007 (million tonnes)"
col_Reserves="Potential CO2 emissions from proven fossil fuel reserves"

col_PeopleAtRisk="Number of people exposed to droughts, floods, extreme temps"
col_SeaLevel="Population below 5m"
col_Poverty='Population living below $1.25 a day'

for f in $datasets
do
    bin/delete-data.py "carbonmap:$f"
    eval col=\${col_$f}
    bin/load-data.py "carbonmap:$f" kiln-data/Maps/With\ alpha-2/$f.csv countries "Alpha-2" "$col"
    bin/density-grid.py "carbonmap:$f" world-robinson > kiln-data/Maps/Cartogram\ data/"$f".density && \
    cart 1500 750 kiln-data/Maps/Cartogram\ data/"$f".density kiln-data/Maps/Cartogram\ data/"$f".cart
    bin/as-svg.py --dataset "carbonmap:$f" --cart kiln-data/Maps/Cartogram\ data/"$f".cart --map world-robinson --json --simplification 20000 > kiln-data/Maps/Cartogram\ data/$f.json
done

(
    echo "// This file is auto-generated. Please do not edit."
    echo "// Generated at $(date)"
    
    echo 'var carbonmap_data = {};'
    
    echo -n 'carbonmap_data._raw = '
    bin/as-svg.py --map world-robinson --json --simplification 20000 | perl -pe 's/$/;/'
    
    echo -n 'carbonmap_data._names = '
    bin/region-names-json world | perl -pe 's/$/;/'
    
    for f in $all_datasets
    do
        if [ -e kiln-data/Maps/Cartogram\ data/"$f".json ]
        then
            echo -n "carbonmap_data.$f = "
            perl -pe 's/$/;/' kiln-data/Maps/Cartogram\ data/"$f".json
            
            echo -n "carbonmap_data.$f._text = \""
            markdown_py -o html5 -s escape -e utf-8 kiln-data/Maps/"$f".text.md | perl -l40pe ''
            echo '";'
        fi
    done
) > kiln-output/data.js

bin/adhoc/dump-project-data.py carbonmap > kiln-data/dumped.csv
