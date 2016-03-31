#!/bin/sh

## the coresperprocess argument is meant to be changed given GridEngine versus serial execution
## if GridEngine, you want this value to be 1, so that each simulation occupies a single core, and 
## GridEngine schedules simulations across all the cores without interference.
## if you're NOT using GridEngine, either remove this argument, or let it default to the number
## of cores/hyperthreads, or perhaps cores/hyperthreads-1.  

seriationct-runbuilder.py --experiment REPLACEME \
--expconfig seriationct-priors.json \
--parallelism 5 \
--numsims 20 \
--networkmodels networkmodels \
--debug 0 \
--coresperprocess 1 \
--jobdirectory jobs

