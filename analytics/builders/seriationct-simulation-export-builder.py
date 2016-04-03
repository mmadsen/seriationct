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



def generate_export_commandline(experiment, outputdirectory, sim_id):
    """
    Creates a seriation command line for the given input file and output directory

    :return: string
    """

    base_cmd = ''

    base_cmd = "seriationct-export-single-simulation.py --experiment "

    base_cmd += experiment
    base_cmd += " --simid "
    base_cmd += sim_id.rstrip()
    base_cmd += " --outputdirectory "
    base_cmd += outputdirectory

    log.debug("cmd: %s", base_cmd)
    return base_cmd





def setup():
    global args, expconfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--outputdirectory", help="path to directory where exported data will be written",
                        required=True)
    parser.add_argument("--jobdirectory", help="directory where job files will be written for execution", default="jobs")
    parser.add_argument("--simidfile",type=str, help="File with simulation IDs to export",required=True)
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
    base_name = "exportjob-"
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

    # get a list of the input files from the database
    with open(args.simidfile, 'r') as simid_file:
        for s in simid_file:

            cmd = generate_export_commandline(args.experiment, args.outputdirectory, s)

            fc = file_cycle.next()
            log.debug("cmd: %s", cmd)
            fc.write(cmd)
            fc.write('\n')

    for fh in file_list:
        fh.close()



if __name__ == "__main__":
    setup()
    main()










