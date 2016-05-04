#!/bin/sh
set -o errexit

for d in `ls jobs/simulationjob*.sh`; do ( sh $d ); done
