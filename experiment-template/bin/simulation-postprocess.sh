#!/bin/sh

set -o errexit

mkdir -p data/sampled-traits
mkdir -p data/assemblage-sampled
mkdir -p data/filtered-data

######## Sample exported datafiles to create synthetic assemblages of 500 artifacts each #########

echo "==================== resample exported data files ====================="


seriationct-simulation-resample-builder.py --inputdirectory data/exported-data \
    --experiment REPLACEME \
    --outputdirectory data/sampled-traits \
    --jobdirectory jobs \
    --samplesize 500 \
    --debug 0 \
    --dropthreshold 0.01 \
    --parallelism 1


for d in `ls jobs/resamplejob*.sh`; do ( sh $d ); done



######## Sample assemblages to pull one assemblage per time interval, with no overlap ########

echo "==================== subsample assemblages ====================="


seriationct-simulation-sample-assemblages-builder.py --inputdirectory data/sampled-traits \
    --experiment REPLACEME \
    --outputdirectory data/assemblage-sampled \
    --sampletype slicestratified \
    --numsamples 1 \
    --samplefraction 0.05 \
    --debug 0 \
    --jobdirectory jobs \
    --parallelism 1


for d in `ls jobs/assemsamplejob*.sh`; do ( sh $d ); done

######## Filter slice-stratified assemblages to eliminate types with less than 3 non-zero entries #######

echo "==================== filter subsampled assemblages ====================="


seriationct-simulation-filter-types-builder.py --inputdirectory data/assemblage-sampled \
    --experiment REPLACEME \
    --outputdirectory data/filtered-data \
    --dropthreshold 0.10 \
    --filtertype onlynonzero \
    --minnonzero 3 \
    --debug 0 \
    --jobdirectory jobs \
    --parallelism 1

for d in `ls jobs/filterjob*.sh`; do ( sh $d ); done


######### Prepare seriation input with all the info needed for spatial seriation and later annotation

echo "==================== finalize seriation input data  ====================="

seriationct-finalize-seriation-input.py \
    --experiment REPLACEME \
    --inputdirectory data/filtered-data \
    --debug 0




echo "=========== POSTPROCESSING COMPLETE =============="
