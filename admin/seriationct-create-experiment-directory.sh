#!/bin/sh

if [ $# -eq 0 ]; then
    echo "seriationct-create-experiment.sh <experiment name> "
    exit 1
fi


# first command line argument is the directory within which to build the experiment
py_loc=`which python`
basedir=`dirname $py_loc | sed "s/bin//"`
unzip $basedir/seriationct-template/seriationct-experiment-template.zip
mv experiment-template $1

cd $1/bin
perl -pi.bak -e "s/REPLACEME/$1/g" *.sh
rm *.bak
cd ..
perl -pi.bak -e "s/REPLACEME/$1/g" README.md
rm *.bak


mkdir -p jobs
mkdir -p data
mkdir -p data/temporal
mkdir -p data/xyfiles

# touch a file in each, so that the empty directories persist in Git 
# prior to having content.  this makes it easier to synchronize an experiment
# through Github to multiple machines

touch jobs/README
touch data/temporal/README
touch data/xyfiles/README

cd ..

echo "Experiment $1 directory structure complete"
echo " "
echo "To configure your experiment, edit the files under the bin/ subdirectory "
echo "to specify a network model, seriation parameters, and simulation runbuilder "
echo "parameters.  To specify the simulation and network parameters themselves, edit the JSON "
echo "file in the main directory."
echo " "
echo "To run the experiment, in the main experiment directory ($1): "
echo "  sh runall.sh "



