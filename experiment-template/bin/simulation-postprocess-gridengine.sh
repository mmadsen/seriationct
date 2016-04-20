#!/bin/sh

mkdir -p sampled-traits
mkdir -p assemblage-sampled
mkdir -p filtered-data

######## Sample exported datafiles to create synthetic assemblages of 500 artifacts each #########

echo "==================== resample exported data files ====================="


seriationct-resample-builder.py --inputdirectory exported-data \
    --experiment REPLACEME \
    --outputdirectory sampled-traits \
    --jobdirectory jobs \
    --samplesize 500 \
    --debug 0 \
    --dropthreshold 0.01 \
    --parallelism 1


for d in `ls jobs/resamplejob*.sh`
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

echo "...resampling assemblages complete..."


######## Sample assemblages to pull one assemblage per time interval, with no overlap ########

echo "==================== subsample assemblages ====================="


seriationct-simulation-sample-assemblages-builder.py --inputdirectory sampled-traits \
    --experiment REPLACEME \
    --outputdirectory assemblage-sampled \
    --sampletype slicestratified \
    --numsamples 1 \
    --samplefraction 0.05 \
    --debug 0 \
    --jobdirectory jobs \
    --parallelism 1


for d in `ls jobs/assemsamplejob*.sh`
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

echo "...sampling sassemblages complete..."

######## Filter slice-stratified assemblages to eliminate types with less than 3 non-zero entries #######

echo "==================== filter subsampled assemblages ====================="



seriationct-simulation-filter-types-builder.py --inputdirectory assemblage-sampled \
    --experiment REPLACEME \
    --outputdirectory filtered-data \
    --dropthreshold 0.10 \
    --filtertype onlynonzero \
    --minnonzero 3 \
    --debug 0 \
    --jobdirectory jobs \
    --parallelism 1

for d in `ls jobs/filterjob*.sh`
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

echo "...filtering assemblages complete..."


######### Prepare seriation input with all the info needed for spatial seriation and later annotation

echo "==================== finalize seriation input data  ====================="

seriationct-finalize-seriation-input.py \
    --experiment REPLACEME \
    --inputdirectory filtered-data \
    --debug 0



echo "=========== POSTPROCESSING COMPLETE =============="