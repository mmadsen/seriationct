#!/usr/bin/env python

import argparse
import logging as log
import os
import fnmatch
import itertools
import ctmixtures.utils as utils
import numpy.random as npr
import json
import uuid
import seriationct.data as data



def parse_filename_into_root(filename):
    base = os.path.basename(filename)
    root, ext = os.path.splitext(base)
    return root



def generate_sample_command(experiment, inputfile, outputdirectory, samplesize,
                                drop_threshold):
    """
    Creates a seriation command line for the given input file and output directory

    :return: string
    """

    base_cmd = ''

    base_cmd = "seriationct-sample-exported-datafile.py --experiment "

    base_cmd += experiment
    base_cmd += " --inputfile "
    base_cmd += inputfile
    base_cmd += " --outputdirectory "
    base_cmd += outputdirectory
    base_cmd += " --samplesize "
    base_cmd += str(samplesize)
    base_cmd += " --dropthreshold "
    base_cmd += str(drop_threshold)

    log.debug("cmd: %s", base_cmd)
    return base_cmd





def setup():
    global args, expconfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--inputdirectory", help="path to directory with exported data files to sample", required=True)
    parser.add_argument("--outputdirectory", help="path to directory where sampled data will be written",
                        required=True)
    parser.add_argument("--jobdirectory", help="directory where job files will be written for execution", default="jobs")
    parser.add_argument("--samplesize", type=int, help="Sample size to resample frequencies for each sim run and replication")
    parser.add_argument("--dropthreshold", type=float, help="Drop all frequencies below this threshold before resampling", default=0.001)

    parser.add_argument("--parallelism",type=int, help="Number of job files to create for exporting via Grid Engine", default=1)

    args = parser.parse_args()

    if args.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    elif args.debug is None:
        args.debug = '0'
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    log.info("Generating export commands for experiment: %s", args.experiment)



def main():
    database = args.experiment
    database += "_samples_raw"
    db_args = {}
    db_args['dbhost'] = args.dbhost
    db_args['dbport'] = args.dbport
    db_args['database'] = database
    db_args['dbuser'] = None
    db_args['dbpassword'] = None
    pp_db = data.PostProcessingDatabase(db_args)

    log.info("Opening %s output files for seriation configuration", args.parallelism)
    num_files = int(args.parallelism)
    file_list = []
    base_name = "resamplejob-"
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

    for file in os.listdir(args.inputdirectory):
        if fnmatch.fnmatch(file, '*.txt'):
            full_fname = args.inputdirectory
            full_fname += "/"
            full_fname += file

            cmd = generate_sample_command(args.experiment, full_fname, args.outputdirectory,
                                          args.samplesize, args.dropthreshold)

            fc = file_cycle.next()
            log.debug("cmd: %s", cmd)
            fc.write(cmd)
            fc.write('\n')

    for fh in file_list:
        fh.close()



if __name__ == "__main__":
    setup()
    main()










