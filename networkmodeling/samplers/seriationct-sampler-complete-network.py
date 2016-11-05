#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Constructs random network models given specified point parameters and uniform prior distributions.  Since we may
generate a large number of network models in order to properly sample the prior space, we use a scheme where network
models are named "<experiment>-netmodel-<sequential integer>, and then the specific postfix:

<nothing>:  directory with the raw network model
.zip:  compressed network model with just the GML files
-XY.txt:  file with the geographic coordinates of all communities in the network model

Furthermore, since each network model has a (possibly) unique combination of parameters, this program also constructs
a database mapping those parameters to the sequential integer ID, contained in:

<experiment>-netmodel-parameters.csv

This file also contains the compressed network model filename as a column, since this is what simulation
and postprocessing code will know, and thus it is the proper foreign key for merging data, and needs to be provided
for postprocessing (which now gets more complex).  

"""


import logging as log
import argparse
import itertools
import numpy.random as npr
import json
import uuid
import os
import csv
import shutil
from seriationct.data import NetworkModelDatabase

def setup():
    global args, nmconfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--seed", type=int, help="random generator seed for replication, defaults to None", default=None)
    parser.add_argument("--netmodelconfig", help="Network model configuration file path", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--nummodels", type=int, help="Number of network models to create through random prior sampling (should be a multiple of the number of network models)")
    parser.add_argument("--rawnetworkmodelspath", help="Path to directory to place raw temporal network model subdirectories", required=True)
    parser.add_argument("--compressednetworkmodelspath", help="Path to directory to place compressed network model files", required=True)
    parser.add_argument("--xyfilespath", help="Path to directory to place assemblage coordinate XY files", required=True)
    #parser.add_argument("--modelrepositorycsv", help="Path to CSV file to record parameters for each model for later analysis", required=True)

    args = parser.parse_args()
    nmconfig = parse_netmodel_config(args.netmodelconfig)

    if args.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    elif args.debug is None:
        args.debug = '0'
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    log.info("Generating %s network models with sampled priors for experiment: %s using generator: %s", args.nummodels, args.experiment, nmconfig['network_generator'])



def generate_randomized_networkmodel(seed):
    """
    Creates a simulation command line for the sim-networkmodel-seriation.py model, using random
    prior distributions for the innovation rate and migration fraction.

    :return: string, dict of parameters for CSV file
    """
    record = {}
    npr.RandomState(seed=seed)

    model_uuid = str(uuid.uuid4())
    record['model_uuid'] = model_uuid

    model_id = args.experiment
    model_id += "_"
    model_id += nmconfig['network_type']
    model_id += "_"
    model_id += model_uuid

    record['model_id'] = model_id
    record['network_type'] = nmconfig['network_type']

    rawdirectorypath = args.rawnetworkmodelspath
    rawdirectorypath += "/"
    rawdirectorypath += model_id
    record['rawdirectorypath'] = rawdirectorypath

    compressedfilepath = args.compressednetworkmodelspath
    compressedfilepath += "/"
    compressedfilepath += model_id
    compressedfilepath += ".zip"
    record['compressedfilepath'] = compressedfilepath

    xyfilepath = args.xyfilespath
    xyfilepath += "/"
    xyfilepath += model_id
    xyfilepath += '-XY.txt'
    record['xyfilepath'] = xyfilepath


    nm_generator = nmconfig['network_generator']
    record['generator'] = nm_generator
    cmd = nm_generator

    cmd += " --modelid "
    cmd += model_id

    cmd += " --outputdirectory "
    cmd += rawdirectorypath

    cmd += " --experiment "
    cmd += args.experiment

    cmd += " --slices "
    cmd += str(nmconfig['slices'])
    record['slices'] = nmconfig['slices']

    cmd += " --debug "
    cmd += args.debug

    cmd += " --numpopulations "
    cmd += str(nmconfig['num_populations_per_slice'])
    record['populations_per_slice'] = nmconfig['num_populations_per_slice']

    cmd += " --edgeweight "
    cmd += str(nmconfig['edgeweight'])
    record['edgeweight'] = nmconfig['edgeweight']

    cmd += " --centroidx "
    cmd += str(nmconfig['centroidx'])
    record['centroidx'] = nmconfig['centroidx']

    cmd += " --centroidy "
    cmd += str(nmconfig['centroidy'])
    record['centroidy'] = nmconfig['centroidy']

    cmd += " --spatialsd "
    cmd += str(nmconfig['spatialsd'])
    record['spatialsd'] = nmconfig['spatialsd']


    cmd += '\n'

    log.debug("%s", cmd)
    return (cmd, record)


def get_csv_header():
    fields = ['model_id', 'model_uuid', 'network_type', 'generator', 'centroidx', 'centroidy', 'spatialsd',
              'edgeweight', 'populations_per_slice', 'slices', 'rawdirectorypath',
              'xyfilepath', 'compressedfilepath']

    return fields



def parse_netmodel_config(config_path):
    try:
        json_data = open(config_path)
        config = json.load(json_data)
    except ValueError:
        print "Problem parsing json configuration file - probably malformed syntax"
        exit(1)
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        exit(1)

    return config



def create_compressed_networkmodel(model_id):
    """

    TODO:  ZipWriter seems to want to put individual files in the zipfile, we need to zip a whole dir  shell out?

    """
    cmd = "zip -q -r "
    cmd += args.compressednetworkmodelspath
    cmd += "/"
    cmd += model_id
    cmd += ".zip "
    cmd += args.rawnetworkmodelspath
    cmd += "/"
    cmd += model_id

    os.system(cmd)


def copy_xyfile(model_id):
    """
    Copies the XY coordinates file from a raw network model to the xy files directory, for a given model ID
    """
    xyfile_src = args.rawnetworkmodelspath
    xyfile_src += "/"
    xyfile_src += model_id
    xyfile_src += "/"
    xyfile_src += model_id
    xyfile_src += "-XY.txt"

    xyfile_dest = args.xyfilespath
    xyfile_dest += "/"
    xyfile_dest += model_id
    xyfile_dest += "-XY.txt"

    shutil.copy(xyfile_src, xyfile_dest)



def main():
    database = args.experiment
    database += "_samples_raw"
    db_args = {}
    db_args['dbhost'] = args.dbhost
    db_args['dbport'] = args.dbport
    db_args['database'] = database
    db_args['dbuser'] = None
    db_args['dbpassword'] = None
    network_db = NetworkModelDatabase(db_args)

    modelrepository_file = args.experiment
    modelrepository_file += "-networkmodels.csv"

    with open(modelrepository_file, 'wb') as csvfile:
        fields = get_csv_header()
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()


        for i in range(0, args.nummodels):
            cmd, record = generate_randomized_networkmodel(args.seed)
            model_id = record['model_id']

            rawdir = args.rawnetworkmodelspath
            rawdir += "/"
            rawdir += model_id

            os.mkdir(rawdir)

            os.system(cmd)
            writer.writerow(record)

            network_db.store_model_metadata(record)

            copy_xyfile(model_id)
            create_compressed_networkmodel(model_id)








if __name__ == "__main__":
    setup()
    main()


