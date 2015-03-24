#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import csv
import argparse
import logging as log
import os
import fnmatch
import math
import random
import numpy as np


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--inputdirectory", help="path to directory with IDSS format input files to sample", required=True)
    parser.add_argument("--outputdirectory", help="path to directory for sampled data files", required=True)
    parser.add_argument("--samplefraction", type=float, help="Sample size to resample frequencies for each sim run and replication")


    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def parse_filename_into_root(filename):
    base = os.path.basename(filename)
    root, ext = os.path.splitext(base)
    return root


def read_unsampled_file(filename):
    """
    Reads the unsampled export file, and produces a header row, and a list of rows for further sampling

    """
    fullpath = args.inputdirectory + "/" + filename
    with open(fullpath, 'r') as incsv:
        csvread = csv.reader(incsv, delimiter="\t")

        header_row = csvread.next()
        header_str = '\t'.join(header_row)
        header_str += '\n'

        row_list = []
        for row in csvread:
            row_list.append(row)

    return (header_str, row_list)







if __name__ == "__main__":
    setup()

    for file in os.listdir(args.inputdirectory):
        if fnmatch.fnmatch(file, '*.txt'):
            root = parse_filename_into_root(file)

            outputfile = args.outputdirectory + "/" + root + "-sampled-" + str(args.samplefraction) + ".txt"

            log.info("Starting processing of %s", outputfile)

            (header, row_list) = read_unsampled_file(file)

            log.debug("header: %s", header)


            num_rows = len(row_list)

            num_samples = int(math.ceil(args.samplefraction * num_rows))
            log.info("Taking %s samples from file %s", num_samples, file)

            sampled_rows = random.sample(range(0, num_rows), num_samples)
            log.debug("Sampling rows: %s", sampled_rows)


            log.info("Writing sampled output for file: %s ", outputfile)

            with open(outputfile, 'wb') as outfile:
                outfile.write(header)

                for row_idx in sampled_rows:
                    row = row_list[row_idx]
                    row_str = '\t'.join(row)
                    row_str += '\n'
                    outfile.write(row_str)

            log.info("Completed processing of file %s", outputfile)

