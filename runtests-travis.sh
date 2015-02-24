#!/bin/sh
set -ex
export PYTHONPATH=$PYTHONPATH::/tmp/usr/local/lib/python2.7/dist-packages:`pwd`
cd test
nosetests
