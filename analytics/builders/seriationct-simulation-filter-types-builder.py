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
import sys



def parse_filename_into_root(filename):
    base = os.path.basename(filename)
    root, ext = os.path.splitext(base)
    return root



# TODO:  Need a different command line for each type of assemblage sampling...

def generate_filter_command(inputfile):
    cmd = "seriationct-filter-types.py "
    cmd += " --debug "
    cmd += args.debug
    cmd += " --experiment "
    cmd += args.experiment
    cmd += " --inputfile "
    cmd += inputfile
    cmd += " --outputdirectory "
    cmd += args.outputdirectory
    cmd += " --dropthreshold "
    cmd += str(args.dropthreshold)
    cmd += " --filtertype "
    cmd += args.filtertype
    cmd += " --minnonzero "
    cmd += str(args.minnonzero)

    return cmd






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
    parser.add_argument("--parallelism",type=int, help="Number of job files to create for exporting via Grid Engine", default=1)


    parser.add_argument("--dropthreshold", type=float,
                    help="Threshold for the Hartigan dip test for considering a type unimodal", default=0.1)
    parser.add_argument("--filtertype", choices=['nonzerodip', 'dip', 'onlynonzero'], help="Filtering can remove just types \
                        that fail Hartigans dip test, dip plus types that have less than two nonzero entries, or just types with less than two nonzero entries", \
                        required=True, default='dip')
    parser.add_argument("--minnonzero", type=int, default=3,
                    help="Minimum number of nonzero values in a type to be retained for seriation")

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

    log.info("Opening %s output files for filter jobs", args.parallelism)
    num_files = int(args.parallelism)
    file_list = []
    base_name = "filterjob-"
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


        cmd = generate_filter_command(full_fname)

        fc = file_cycle.next()
        log.debug("cmd: %s", cmd)
        fc.write(cmd)
        fc.write('\n')

    for fh in file_list:
            fh.close()



if __name__ == "__main__":
    setup()
    main()










