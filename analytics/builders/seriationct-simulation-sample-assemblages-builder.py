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

def generate_base_command(inputfile):
    cmd = "seriationct-sample-assemblages.py "
    cmd += " --debug 0"
    cmd += " --experiment "
    cmd += args.experiment
    cmd += " --inputfile "
    cmd += inputfile
    cmd += " --outputdirectory "
    cmd += args.outputdirectory
    cmd += " --samplefraction "
    cmd += str(args.samplefraction)
    cmd += " --numsamples "
    cmd += str(args.numsamples)
    cmd += " --sampletype "
    cmd += args.sampletype

    return cmd


def generate_random_sample_command(inputfile):
    cmd = generate_base_command(inputfile)
    # simple random samples are covered by the base
    return cmd

def generate_spatial_sample_command(inputfile):
    cmd = generate_base_command(inputfile)
    cmd += " --spatialquadrats "
    cmd += args.spatialquadrats
    cmd += " --spatialdata "
    cmd += args.spatialdata
    cmd += " --maxsizespatial "
    cmd += args.maxsizespatial
    return cmd

def generate_temporal_sample_command(inputfile):
    cmd = generate_base_command(inputfile)
    cmd += " --temporaldata "
    cmd += args.temporaldata
    cmd += " --temporalperiods "
    cmd += args.temporalperiods
    return cmd

def generate_spatiotemporal_sample_command(inputfile):
    cmd = generate_base_command(inputfile)
    cmd += " --spatialquadrats "
    cmd += args.spatialquadrats
    cmd += " --spatialdata "
    cmd += args.spatialdata
    cmd += " --maxsizespatial "
    cmd += args.maxsizespatial
    cmd += " --temporaldata "
    cmd += args.temporaldata
    cmd += " --temporalperiods "
    cmd += args.temporalperiods
    return cmd


def generate_complete_sample_command(inputfile):
    cmd = generate_base_command(inputfile)
    # complete samples are covered by the base
    return cmd

def generate_exclusion_sample_command(inputfile):
    cmd = generate_base_command(inputfile)
    cmd += " --excludefile "
    cmd += args.excludefile
    return cmd

def generate_slicestratified_sample_command(inputfile):
    cmd = generate_base_command(inputfile)
    # slicestratified samples are covered by the base because
    # the code queries for the proper network model given
    # the input file
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


    parser.add_argument("--samplefraction", type=float,
                        help="Sample size to resample frequencies for each sim run and replication", required=True)
    parser.add_argument("--sampletype",
                        choices=['random', 'spatial', 'temporal', 'spatiotemporal', 'complete', 'excludelist','slicestratified'],
                        help="type of sampling.  random has no stratification, temporal is rough early/late stratification, spatial is"
                             "quadrants, spatiotemporal is stratification by both, complete preserves all rows, excludelist returns all rows except those given in a file",
                        required=True)
    parser.add_argument("--excludefile", help="File of assemblage names to exclude from the input list")
    parser.add_argument("--numsamples", type=int,
                        help="number of samples to take from each original data set (default is 1)", default=1)
    parser.add_argument("--temporaldata",
                        help="path to directory with temporal data files to match files in inputdirectory "
                             "(required for temporal or spatiotemporal sampling")
    parser.add_argument("--temporalperiods", type=int, help="Number of temporal periods in which to stratify the sample",
                        default=3)
    parser.add_argument("--spatialquadrats", type=int,
                        help="Number of blocks in the X and Y directions in which to stratify the sample", default=3)
    parser.add_argument("--spatialdata", help="path to XY file of spatial coordinates for assemblages")
    parser.add_argument("--maxsizespatial", type=int, help="Maximum size of spatial coordinates in X and Y directions",
                        default=1100)

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

    log.info("Opening %s output files for assemblage sampling jobs", args.parallelism)
    num_files = int(args.parallelism)
    file_list = []
    base_name = "assemsamplejob-"
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


            if args.sampletype == 'random':
                cmd = generate_random_sample_command(full_fname)
            elif args.sampletype == 'spatial':
                cmd = generate_spatial_sample_command(full_fname)
            elif args.sampletype == 'temporal':
                cmd = generate_temporal_sample_command(full_fname)
            elif args.sampletype == 'spatiotemporal':
                cmd = generate_spatiotemporal_sample_command(full_fname)
            elif args.sampletype == 'complete':
                cmd = generate_complete_sample_command(full_fname)
            elif args.sampletype == 'excludelist':
                cmd = generate_exclusion_sample_command(full_fname)
            elif args.sampletype == 'slicestratified':
                cmd = generate_slicestratified_sample_command(full_fname)
            else:
                print "sampletype not recognized, fatal error"
                sys.exit(1)

            fc = file_cycle.next()
            log.debug("cmd: %s", cmd)
            fc.write(cmd)
            fc.write('\n')

    for fh in file_list:
        fh.close()



if __name__ == "__main__":
    setup()
    main()










