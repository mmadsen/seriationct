#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""


import logging as log
import argparse
import itertools
import ctmixtures.utils as utils
import numpy.random as npr
import json
import uuid
import os


def generate_randomized_simulation(seed, net_model):
    """
    Creates a simulation command line for the sim-networkmodel-seriation.py model, using random
    prior distributions for the innovation rate and migration fraction

    :return: string
    """

    theta = npr.uniform(low = float(expconfig['theta_low']), high = float(expconfig['theta_high']))
    migr_frac = npr.uniform(low = float(expconfig['migrationfraction_low']), high = float(expconfig['migrationfraction_high']))

    if args.simprefix is not None:
        cmd = ""
        cmd += args.simprefix
        cmd += "/sim-seriationct-networkmodel.py "
    else:
        cmd = "sim-seriationct-networkmodel.py "

    if args.dbhost is not None:
        cmd += " --dbhost "
        cmd += args.dbhost


    if args.dbport is not None:
        cmd += " --dbport "
        cmd += args.dbport

    cmd += " --experiment "
    cmd += args.experiment

    cmd += " --popsize "
    cmd += str(expconfig["popsize"])

    cmd += " --maxinittraits "
    cmd += str(expconfig["maxinittraits"])

    cmd += " --numloci "
    cmd += str(expconfig["numloci"])

    cmd += " --innovrate "
    cmd += str(theta)

    cmd += " --simlength "
    cmd += str(expconfig["simlength"])

    cmd += " --debug "
    cmd += args.debug

    cmd += " --seed "
    cmd += str(seed)

    cmd += " --reps "
    cmd += str(expconfig["replicates"])

    cmd += " --samplefraction "
    cmd += str(expconfig["samplefraction"])

    cmd += " --migrationfraction "
    cmd += str(migr_frac)

    # for production runs, let the system decide how many cores to use
    cmd += " --devel 0"

    if args.networkprefix is not None:
        cmd += " --networkmodel "
        cmd += args.networkprefix + "/"
        cmd += net_model
    else:
        cmd += " --networkmodel "
        cmd += net_model

    cmd += '\n'

    log.debug("%s", cmd)
    return cmd


def parse_experiment_config(config_path):
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



def setup():
    global args, expconfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--expconfig", help="Experiment configuration file path", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--parallelism", help="Number of separate job lists to create", default="4")
    parser.add_argument("--numsims", type=int, help="Number of simulations to generate across network models by random prior sampling (should be a multiple of the number of network models)")
    parser.add_argument("--networkmodels", help="Path to directory with compressed temporal network models", required=True)
    parser.add_argument("--simprefix", help="Full path prefix to the simulation executable (optional)")
    parser.add_argument("--networkprefix", help="Full path prefix to the network model directory given in --networkmodels (optiona)")
    parser.add_argument("--jobdirectory", help="Path to a directory where job scripts should be written (optional)")

    args = parser.parse_args()
    expconfig = parse_experiment_config(args.expconfig)

    if args.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    elif args.debug is None:
        args.debug = '0'
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    log.info("Generating simulation commands for experiment: %s", args.experiment)



def main():
    log.info("Opening %s output files for simulation configuration", args.parallelism)
    num_files = int(args.parallelism)
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


