#!/bin/sh

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

seriationct-simulation-export-builder.py --experiment REPLACEME \
    --simidfile simids.txt --outputdirectory exported-data

echo "=============== exporting temporal information on assemblages ==============="

seriationct-assemblage-duration-export.py --experiment REPLACEME \
    --outputdirectory temporal



echo "=============== running export jobs through Grid Engine ================="

for d in `ls jobs/export*.sh`
do
        qsub -V -cwd $d
done

# just a default value, but this is often what we run at a time given core count
count=10

while [ $count -ne 0 ]
do
	sleep 60
	count=`qstat | wc -l`
	echo "still $count exports running in gridengine"
done
