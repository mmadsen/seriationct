#!/bin/sh

# exit if any of the subcommands returns an error, since they only work if the preceding command succeeded
set -e


## assumes that network models are built and in place, because this is typically an exploratory step
## once the network models are satisfactory, this script builds simulations, runs them, post processes
## and samples the simulation output, builds seriation scripts, runs seriations, and annotates the output

sh bin/build-simulations.sh &> build-simulation.log
sh bin/run-simulations.sh &> simulation.log
#sh bin/run-simulations-gridengine.sh &> simulation.log
sh bin/export-data.sh &> export.log
sh bin/simulation-postprocess.sh &> postprocess.log
sh bin/build-seriations.sh &> build-seriations.log
sh bin/run-seriations.sh &> seriation.log
sh bin/annotate-seriation-output.sh &> annotate.log
