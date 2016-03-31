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
from seriation.database import SeriationRun, SeriationFileLocations, \
    FrequencySeriationResult, ContinuitySeriationResult, SeriationRunParameters

import pprint as pp
import pickle
import numpy as np


# TODO:  using all the intermediate data objects, export a Pandas data frame of the experiment for analysis.  It's alright if the network model has model-specific parameters


def get_csv_header():
    fields = ['model_id', 'model_uuid', 'network_type', 'generator', 'numclusters',
              'numlineages','clusterspread', 'direction', 'foo',
              'centroidmin', 'centroidmax', 'nodespercluster', 'slices', 'rawdirectorypath',
              'xyfilepath', 'compressedfilepath']

    return fields



# broken out to allow line profiling
#@profile
def doExport():
    database = args.experiment
    database += "_samples_raw"
    db_args = {}
    db_args['dbhost'] = args.dbhost
    db_args['dbport'] = args.dbport
    db_args['database'] = database
    db_args['dbuser'] = None
    db_args['dbpassword'] = None
    pp_db = data.PostProcessingDatabase(db_args)
    sm_db = data.SimulationMetadataDatabase(db_args)
    nm_db = data.NetworkModelDatabase(db_args)


    data_repository_file = args.experiment
    data_repository_file += "-"
    data_repository_file += "full-data.csv"





    # approach is to start at the end, and walk back toward the beginning
    # Start with SeriationCT SeriationAnnotationData object, get IDSS seriation params

    # BUT - to know the column headers, we have to either accumulate all the data in memory
    # first or we have to peek at what columns exist in the network model database so we can
    # then process a row at a time.
    nmodel = data.NetworkModelDatabase.objects()[0]
    params = nmodel.model_parameters



    annotated_obj = data.SeriationAnnotationData.objects


    # Get post processing step parameters, by walking explicitly backward using the
    # seriation input file to get the filtered info, then filtered to get assemblage sampling,
    # and so on.

    # After postprocessing steps, use the simulation run id to get the sim params

    # then get the network model info and NM parameters


    # since
    with open(data_repository_file, 'wb') as csvfile:
        fields = get_csv_header()
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()


## setup

def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment, to be used as prefix for database collections")
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--outputdirectory", help="location to write exported data, defaults to current", default=".")

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


    #### main program ####
    log.info("EXPORT Finiashed experiment - Experiment: %s ", args.experiment)



if __name__ == "__main__":
    setup()
    doExport()








