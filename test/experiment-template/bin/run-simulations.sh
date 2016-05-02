#!/bin/sh
for d in `ls jobs/job*.sh`; do ( sh $d ); done
