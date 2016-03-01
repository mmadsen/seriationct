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

def setup():
    global args, nmconfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--netmodelconfig", help="Network model configuration file path", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--nummodels", type=int, help="Number of network models to  random prior sampling (should be a multiple of the number of network models)")
    parser.add_argument("--rawnetworkmodelspath", help="Path to directory to place raw temporal network model subdirectories", required=True)
    parser.add_argument("--compressednetworkmodelspath", help="Path to directory to place compressed network model files", required=True)
    parser.add_argument("--xyfilespath", help="Path to directory to place assemblage coordinate XY files", required=True)
    parser.add_argument("--modelrepositorycsv", help="Path to CSV file to record parameters for each model for later analysis", required=True)

    args = parser.parse_args()
    nmconfig = parse_netmodel_config(args.netmodelconfig)

    if args.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    elif args.debug is None:
        args.debug = '0'
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    log.info("Generating %s network models with sampled priors for experiment: %s", args.nummodels, args.experiment)



def generate_randomized_networkmodel(seed, net_model):
    """
    Creates a simulation command line for the sim-networkmodel-seriation.py model, using random
    prior distributions for the innovation rate and migration fraction

    :return: string
    """

    field_order = ['modelid', 'mean_edges_perpopulation', 'sd_edges_perpopulation', 'exponential_decay_coefficient', 'edgeweight', 'num_populations_per_slice', 'slices', 'spatial_aspect_ratio']
    params = dict()


    mean_edges_perpopulation = npr.uniform(low=float(nmconfig['mean_edges_perpopulation_low']),
                                           high=float(nmconfig['mean_edges_perpopulation_high']))

    sd_edges_perpopulation = npr.uniform(low=float(nmconfig['sd_edges_perpopulation_low']),
                                         high=float(nmconfig['sd_edges_perpopulation_high']))

    exponential_coefficient = npr.uniform(low=float(nmconfig['exponential_coefficient_low']),
                                          high=float(nmconfig['exponential_coefficient_high']))


{

    "edgeweight": 10,
    "slices": 10,
    "numpopulations": 32
}



    cmd = "seriationct-build-spatial-neighbor.py "

    if args.dbhost is not None:
        cmd += " --dbhost "
        cmd += args.dbhost


    if args.dbport is not None:
        cmd += " --dbport "
        cmd += args.dbport

    cmd += " --experiment "
    cmd += args.experiment

    cmd += " --slices "
    cmd += str(nmconfig['slices'])

    cmd += " --debug "
    cmd += args.debug

    cmd += " --numpopulations "
    cmd += str(nmconfig['numpopulations'])

    cmd += " --edgeweight "
    cmd += str(nmconfig['edgeweight'])



    # for production runs, let the system decide how many cores to use
    cmd += " --devel 0"

    if args.networkprefix is not None:
        cmd += " --networkmodel "
        cmd += args.networkprefix + "/"
        cmd += net_model
    else:
        cmd += " --networkmodel "
        cmd += net_model

    if args.coresperprocess is not None:
        cmd += " --cores "
        cmd += str(args.coresperprocess)

    cmd += '\n'

    log.debug("%s", cmd)
    return cmd


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







def main():


    for i in range(0, args.nummodels):







    file_list = []
    base_name = "job-"
    base_name += args.experiment
    base_name += "-"

    for i in range(0, num_files):
        filename = ''
        if args.jobdirectory is not None:
            filename = args.jobdirectory + "/"
        filename += base_name
        filename += str(uuid.uuid4())
        filename += ".sh"

        log.debug("job file: %s", filename)
        f = open(filename, 'w')

        f.write("#!/bin/sh\n\n")
        file_list.append(f)

    file_cycle = itertools.cycle(file_list)


    # read all the network model archives, and create a itertools.cycle for them
    # so that we distribute network models across the randomly chosen priors
    network_model_files = []

    for file in os.listdir(args.networkmodels):
        if file.endswith(".zip"):
            full_filepath = args.networkmodels + "/" + file
            network_model_files.append(full_filepath)
            log.info("Network model found: %s", full_filepath)

    network_model_cycle = itertools.cycle(network_model_files)


    for i in xrange(0, args.numsims):

        # give us a random seed that will fit in a 64 bit long integer
        seed = npr.randint(1,2**31)

        net_model = network_model_cycle.next()
        cmd = generate_randomized_simulation(seed, net_model)

        fc = file_cycle.next()
        log.debug("cmd: %s", cmd)
        fc.write(cmd)


    for fh in file_list:
        fh.close()





if __name__ == "__main__":
    setup()
    main()


