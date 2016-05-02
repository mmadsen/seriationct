#!/bin/sh

set -o errexit

mkdir -p exported-data
mkdir -p temporal

cat << EOF > /tmp/mongo-index
use REPLACEME_samples_raw;
db.seriationct_sample_unaveraged.ensureIndex( { simulation_run_id: 1 })
EOF

mongo < /tmp/mongo-index
rm /tmp/mongo-index

echo "=================== exporting simulation data =============="

seriationct-export-simids.py --experiment REPLACEME --outputfile simids.txt
for d in `cat simids.txt`;
do ( 
	#echo "export $d"
	seriationct-export-single-simulation.py --experiment REPLACEME \
		--outputdirectory exported-data \
		--simid $d 
); done


echo "=============== exporting temporal information on assemblages ==============="

seriationct-assemblage-duration-export.py --experiment REPLACEME \
    --outputdirectory temporal