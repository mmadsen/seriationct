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



def generate_seriation_commandline(inputfile, outputdirectory, xyfile, database, source_identifier):
    """
    Creates a seriation command line for the given input file and output directory

    :return: string
    """

    base_cmd = ''

    base_cmd += "idss-seriation-mongodb.py --debug 0 --graphs 0 --spatialbootstrapN 100 --spatialsignificance=1 "
    base_cmd += " --database "
    base_cmd += database


    if args.continuity is not None:
        base_cmd += " --continuity "
        base_cmd += str(args.continuity)

    if args.frequency is not None:
        base_cmd += " --frequency "
        base_cmd += str(args.frequency)

    if args.dobootstrapsignificance == 1:
        base_cmd += " --bootstrapCI=1 --bootstrapSignificance=0.95 "
    elif args.dobootstrapsignificance == 0:
        log.debug("Turning off bootstrap significance testing")
        base_cmd += " --bootstrapCI=0 "
    else:
        log.error("Bad value for turning on/off bootstrap significance testing")
        os._exit(1)

    if args.execpath is not None:
        cmd = args.execpath
        cmd += '/'
    else:
        cmd = ''

    cmd += base_cmd + " --inputfile " + inputfile
    cmd += " --outputdirectory " + outputdirectory
    cmd += " --xyfile " + xyfile
    cmd += " --source_identifier " + source_identifier

    log.debug("cmd: %s", cmd)
    return cmd





def setup():
    global args, expconfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--parallelism", help="Number of separate job lists to create", default="1")
    parser.add_argument("--jobdirectory", help="Path to a directory where job scripts should be written (optional)")
    parser.add_argument("--inputdirectory", help="path to directory with IDSS input files to process", required=True)
    parser.add_argument("--outputdirectory", help="path to directory where IDSS output directories will be created",
                        required=True)
    parser.add_argument("--execpath", help="Path to the IDSS executable script (optional)")
    parser.add_argument("--dobootstrapsignificance", type=int, default=1, help="Perform bootstrap significance tests with a 95% CI")
    parser.add_argument("--continuity",type=int, help="Perform continuity seriation",default=0)
    parser.add_argument("--frequency",type=int, help="Perform frequency seriation",default=1)

    args = parser.parse_args()

    if args.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    elif args.debug is None:
        args.debug = '0'
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    log.info("Generating seriation commands for experiment: %s", args.experiment)



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
    base_name = "seriationjob-"
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
    seriations = data.SeriationInputData.objects

    for s in seriations:
        input_file = s.seriation_input_file

        log.info("Processing input file: %s", input_file)

        root = parse_filename_into_root(input_file)

        outdir = os.getcwd() + '/' + args.outputdirectory + "/" + root

        try:
            os.mkdir(outdir)
        except:
            pass


        cmd = generate_seriation_commandline(input_file, outdir, s.xy_file_path, database, s.source_identifier)

        fc = file_cycle.next()
        log.debug("cmd: %s", cmd)
        fc.write(cmd)
        fc.write('\n')

    for fh in file_list:
        fh.close()



if __name__ == "__main__":
    setup()
    main()










