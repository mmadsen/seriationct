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
import numpy as np


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment, to be used as prefix for database collections")
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--inputdirectory", help="path to directory with CSV files to sample", required=True)
    parser.add_argument("--outputdirectory", help="path to directory for exported data files", required=True)
    parser.add_argument("--samplesize", type=int, help="Sample size to resample frequencies for each sim run and replication")
    parser.add_argument("--dropthreshold", type=float, help="Drop all frequencies below this threshold before resampling", default=0.001)

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
    Reads the unsampled export file, and produces a list of assemblages, classes, and a numpy array
    of the class counts for further sampling.
    :return: tuple with a list of assemblage names, class_names, and a Numpy array of trait counts
    """
    fullpath = args.inputdirectory + "/" + filename
    with open(fullpath, 'r') as incsv:
        csvread = csv.reader(incsv, delimiter="\t")

        header_row = csvread.next()
        class_names = header_row[1:]  # everything except the first item

        row_list = []
        assemblage_list = []
        for row in csvread:
            assemblage_list.append(row[0])
            row_list.append(row[1:])

        count_arr = np.array(row_list, dtype=np.float32)

    return (assemblage_list, class_names, count_arr)







def calc_frequency_array(count_arr):
    #log.debug("count_arr: %s", count_arr)
    row_sums = np.sum(count_arr, axis=1)
    freq_arr = (count_arr.T / row_sums).T

    # remove frequencies < 1e-04, or 0.0001
    freq_arr[freq_arr < args.dropthreshold] = 0.0

    return freq_arr





if __name__ == "__main__":
    setup()

    for file in os.listdir(args.inputdirectory):
        if fnmatch.fnmatch(file, '*.txt'):
            root = parse_filename_into_root(file)

            outputfile = args.outputdirectory + "/" + root + "-sampled-" + str(args.samplesize) + ".txt"

            log.info("Starting processing of %s", outputfile)

            (assemblages, classes, count_arr) = read_unsampled_file(file)

            freq_arr = calc_frequency_array(count_arr)

            # First we sample the frequency array.  We then get rid of any resulting columns that have
            # all zeros -- these are classes which are unrepresented in any assemblage
            # then we write out the resulted reduced sample

            sampled = np.zeros(freq_arr.shape)
            for row_idx in range(0,freq_arr.shape[0]):

                probs = freq_arr[row_idx]
                log.debug("sum of all freq: %s", sum(probs))
                sampled[row_idx] = np.random.multinomial(args.samplesize, probs, size=1)
                log.debug("sampled: %s", sampled[row_idx])

                total_sample = sum(sampled[row_idx])
                log.debug("sample size: %s  sample total: %s", args.samplesize, total_sample)

            # find the nonzero columns in the result
            col_sum = np.sum(sampled, axis=0)
            nonzero_cols = np.nonzero(col_sum)[0].tolist()

            log.info("Writing sampled output for file: %s  remaining classes in sample: %s", outputfile, len(nonzero_cols))

            with open(outputfile, 'wb') as outfile:

                # write header row
                header = "Assemblage_Name"

                for idx in range(0, len(classes)):
                    if idx in nonzero_cols:
                        header += '\t'
                        header += classes[idx]
                header += '\n'

                outfile.write(header)

                for row_idx in range(0, sampled.shape[0]):
                    row = assemblages[row_idx]
                    for idx in range(0, len(classes)):
                        if idx in nonzero_cols:
                            row += "\t"
                            row += str(int(sampled[row_idx, idx]))
                    row += "\n"
                    outfile.write(row)



            log.info("Completed processing of file %s", outputfile)

