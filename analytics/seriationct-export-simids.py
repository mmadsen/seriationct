#!/usr/bin/env python

# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

import ming
import csv
import os
import logging as log
import tempfile
import argparse
from collections import defaultdict
import seriationct.data as data
import pprint as pp
import pickle
import numpy as np



# broken out to allow line profiling
#@profile
def doExport():
    # the data cache has the following nested dict structure:  simid -> replicate -> subpop -> class:count

    with open(args.outputfile, 'wb') as outfile:
        cursor = data.SimulationMetadata.m.find(dict(),dict({'simulation_run_id':1}))

        for sample in cursor:
            sim_id = sample["simulation_run_id"]
            outfile.write(sim_id)
            outfile.write('\n')




## setup

def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment, to be used as prefix for database collections")
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--outputfile", help="path to file for simulation IDs", required=True)

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


    #### main program ####
    log.info("EXPORT DATA TO CSV - Experiment: %s", args.experiment)
    data.set_experiment_name(args.experiment)
    data.set_database_hostname(args.dbhost)
    data.set_database_port(args.dbport)
    config = data.getMingConfiguration(data.modules)
    ming.configure(**config)


if __name__ == "__main__":
    setup()
    doExport()







