#!/bin/sh

for d in `ls jobs/seriationjob*.sh`; do ( sh $d ); done