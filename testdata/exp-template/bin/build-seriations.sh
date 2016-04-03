#!/bin/sh

mkdir -p seriation-output

seriationct-seriation-runbuilder.py --inputdirectory slice-stratified-filtered-data \
	--outputdirectory seriation-output \
	--dobootstrapsignificance 1 \
	--frequency 0 \
	--continuity 1 \
	--experiment test3 \
	--jobdirectory jobs \
	--parallelism 1 \
	--debug 0


