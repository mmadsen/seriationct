#!/bin/sh

mkdir -p sampled-traits
mkdir -p slice-stratified-sampled-data
mkdir -p slice-stratified-filtered-data

######## Sample exported datafiles to create synthetic assemblages of 500 artifacts each #########

echo "==================== sample exported data files ====================="

seriationct-sample-exported-datafiles.py --inputdirectory exported-data \
    --experiment REPLACEME \
	--outputdirectory sampled-traits \
	--samplesize 500 \
	--debug 0 \
	--dropthreshold 0.01


######## Sample assemblages to pull one assemblage per time interval, with no overlap ########

echo "==================== sample temporal slices ====================="

seriationct-sample-assemblages-for-seriation.py --inputdirectory sampled-traits \
    --experiment REPLACEME \
	--outputdirectory slice-stratified-sampled-data \
 	--sampletype slicestratified \
 	--numsamples 1 \
 	--samplefraction 0.05 \
 	--debug 0 \

######## Filter slice-stratified assemblages to eliminate types with less than 3 non-zero entries #######

echo "==================== filter sampled assemblages ====================="

seriationct-filter-types.py \
    --experiment REPLACEME \
	--inputdirectory slice-stratified-sampled-data \
	--outputdirectory slice-stratified-filtered-data \
	--dropthreshold 0.10 \
	--filtertype onlynonzero \
	--minnonzero 3
	--debug 0 \

######### Prepare seriation input with all the info needed for spatial seriation and later annotation

echo "==================== finalize seriation input data for assemblages ====================="

seriationct-finalize-seriation-input.py \
    --experiment REPLACEME \
    --inputdirectory slice-stratified-filtered-data \
    --debug 0