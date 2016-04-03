#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import sys
import csv
import argparse
import logging as log
import os
import fnmatch
import numpy as np
from decimal import *
from seriationct.demography import TemporalNetwork
import operator
import tatome.dip as dip
import seriationct.data as data


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment, to be used as prefix for database collections")
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--inputdirectory", help="path to directory with CSV files to sample", required=True)
    parser.add_argument("--outputdirectory", help="path to directory for exported data files", required=True)
    parser.add_argument("--dropthreshold", type=float, help="Threshold for the Hartigan dip test for considering a type unimodal", default=0.1)
    parser.add_argument("--filtertype", choices=['nonzerodip','dip', 'onlynonzero'], help="Filtering can remove just types \
        that fail Hartigans dip test, dip plus types that have less than two nonzero entries, or just types with less than two nonzero entries", \
                        required=True, default='dip')
    parser.add_argument("--minnonzero", type=int, default=3, help="Minimum number of nonzero values in a type to be retained for seriation")

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def parse_filename_into_root(filename):
    base = os.path.basename(filename)
    root, ext = os.path.splitext(base)
    return root


def read_unsampled_file(filename, sorted_assemblages):
    """
    Reads the unsampled export file, and produces a list of assemblages, classes, and a numpy array
    of the class counts for further sampling.

    This is horribly inefficient, but we rarely have really large data sets for seriation...

    :return: tuple with a list of assemblage names, class_names, and a Numpy array of trait counts
    """
    fullpath = args.inputdirectory + "/" + filename
    with open(fullpath, 'r') as incsv:
        csvread = csv.reader(incsv, delimiter="\t")

        header_row = csvread.next()
        class_names = header_row[1:]  # everything except the first item
        unsorted_row_list = []
        for row in csvread:
            unsorted_row_list.append(row)

        # now sort the whole thing before we peel off column 1, make it match the sorted assemblage names
        sorted_row_list = []
        for assem in sorted_assemblages:
            for row in unsorted_row_list:
                if row[0] == assem:
                    sorted_row_list.append(row)


        data_list = []
        assemblage_list = []
        for r in sorted_row_list:
            assemblage_list.append(r[0])
            data_list.append(r[1:])

        count_arr = np.array(data_list, dtype=np.float32)

    return (assemblage_list, class_names, count_arr)


def has_gt_n_nonzero_entry(col, n):
    """
    Returns true if a list of numbers has more than N non-zero entries, false otherwise.
    or is composed of all zeros
    (which is happening due to sampling of types with very small proportions.

    :param col:
    :return: bool
    """
    non_zero = 0
    for i in col:
        if i > 0:
            non_zero += 1

    if non_zero >= n:
        return True
    else:
        return False




def has_only_zeroes(col):
    """
    Returns true if a list of numbers only contains zeros.  In a situation where we cannot have
    negative numbers, we can shortcut this with the sum of the list, but in general that would be
    dangerous.
    :param col:
    :return: bool
    """
    if sum(col) == 0:
        return True
    else:
        return False


def filter_cols_for_unimodality(count_arr, threshold):
    """
    Given an array of counts, iterates over the array and tests each column for unimodality
    using the Hartigans' dip test, as implemented by https://github.com/tatome/dip_test.  Values
    over threshold are taken as evidence for multimodality.  Returns a list of columns which are
    retained (as unimodal) and columns which should be filtered out (as multimodal).

    :param count_arr:
    :return: tuple of lists:  rejected_columns, retained_columns
    """
    rejected_columns = []
    retained_columns = []
    for i in range(0, count_arr.shape[1]):
        col = count_arr[:,i].tolist()

        # have to filter the columns with only zeroes out before passing to the dip test
        if has_only_zeroes(col):
            rejected_columns.append(i)
            log.debug("rejecting col %s for having only zero entries", i)
            continue


        if args.filtertype in ['nonzerodip','onlynonzero']:
            if has_gt_n_nonzero_entry(col, args.minnonzero) == False:
                rejected_columns.append(i)
                log.debug("rejecting col %s for having too few non-zero entries", i)
                continue

        if args.filtertype in ['nonzerodip', 'dip']:
            # element zero of the dip test tuple is the p-value (or "dip test value" as it's described in the docs)
            dip_pvalue = dip.dip(idxs=col)[0]
            log.debug("dip pvalue for col %s: %s", i, dip_pvalue)
            if dip_pvalue < float(threshold):
                log.debug("rejecting col %s for having dip test value below threshold", i)
                rejected_columns.append(i)
                continue

        # if we pass all the checks, it's good
        retained_columns.append(i)

    return (rejected_columns, retained_columns)


def row_num_for_assemblage(assemblage, assemblages):
    """
    Get the index of the named assemblage in the assemblages list

    :param assemblage:
    :param sorted_assemblages:
    :return: index number, or none if the assemblage doesn't exist in the list (an error condition, shouldn't happen)
    """
    for i in range(0, len(assemblages)):
        if assemblage == assemblages[i]:
            return i
    return None

def get_networkmodel_for_input(file):
    sampled_obj = data.AssemblageSampledSimulationData.objects.get(output_file=file)
    sim_id = sampled_obj.simulation_run_id
    sim_run = data.SimulationRunMetadata.objects.get(simulation_run_id=sim_id)
    networkmodel = sim_run.networkmodel
    return networkmodel



if __name__ == "__main__":
    setup()
    database = args.experiment
    database += "_samples_raw"
    db_args = {}
    db_args['dbhost'] = args.dbhost
    db_args['dbport'] = args.dbport
    db_args['database'] = database
    db_args['dbuser'] = None
    db_args['dbpassword'] = None
    pp_db = data.PostProcessingDatabase(db_args)
    sm_db = data.SimulationMetadataDatabase(db_args)










    for file in os.listdir(args.inputdirectory):
        if fnmatch.fnmatch(file, '*.txt'):
            full_fname = args.inputdirectory
            full_fname += "/"
            full_fname += file
            root = parse_filename_into_root(file)

            networkmodel = get_networkmodel_for_input(full_fname)
            # we use the actual TemporalNetwork
            netmodel = TemporalNetwork(networkmodel_path=networkmodel, sim_length=1000)

            time_map = netmodel.get_subpopulation_slice_ids()
            # log.debug("assemblage time_map: %s", time_map)

            # get the list of assemblages in order sorted by the origin time
            sorted_assemblage_names = sorted(time_map.keys(), key=operator.itemgetter(1))

            log.debug("sorted_assemblages: %s", sorted_assemblage_names)

            outputfile = args.outputdirectory + "/" + root + "-" + str(args.dropthreshold) + "-unimodal-filtered.txt"

            log.debug("Starting processing of %s", outputfile)

            (assemblages, classes, count_arr) = read_unsampled_file(file, sorted_assemblage_names)
            #log.debug("assemblages: %s", assemblages)

            # sort the rows of the count_arr by the temporal order we've got above.  This isn't easy to do
            # automatically, so we basically do it manually
            # class order hasn't changed so the classes variable is still valid.

            sorted_row_list = []
            for assem in sorted_assemblage_names:
                if assem in assemblages:
                    row_in_orig = row_num_for_assemblage(assem, assemblages)
                    sorted_row_list.append(count_arr[row_in_orig,:])

            #log.debug("sorted row list: %s", sorted_row_list)

            sorted_data = np.array(sorted_row_list,dtype=np.float32)



            # sorted_assemblages and sorted_data now represent the data set in sorted temporal order
            # filter this using the Hartigans' dip test
            (rejected_cols, retained_cols) = filter_cols_for_unimodality(sorted_data,args.dropthreshold)


            log.info("Writing filtered output for file: %s rejected classes: %s  remaining classes: %s", outputfile,len(rejected_cols), len(retained_cols))

            with open(outputfile, 'wb') as outfile:

                # write header row
                header = "Assemblage_Name"

                for idx in range(0, len(classes)):
                    if idx in retained_cols:
                        header += '\t'
                        header += classes[idx]
                header += '\n'

                outfile.write(header)

                for row_idx in range(0, sorted_data.shape[0]):
                    row = assemblages[row_idx]
                    for idx in range(0, len(classes)):
                        if idx in retained_cols:
                            row += "\t"
                            row += str(int(sorted_data[row_idx, idx]))
                    row += "\n"
                    outfile.write(row)


        sim_id = pp_db.store_filtered_datafile(full_fname,networkmodel,args.dropthreshold,args.filtertype,args.minnonzero,outputfile)

        log.debug("Completed processing of file %s", outputfile)

