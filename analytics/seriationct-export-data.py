#!/usr/bin/env python

# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

import ming
import csv
import os
import logging as log
import tempfile
import argparse
from collections import defaultdict
import seriationct.data as data
import pprint as pp


class DeepDefaultDict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

    def __add__(self, x):
        """ override addition when self is empty """
        if not self:
            return 0 + x
        raise ValueError

    def __sub__(self, x):
        """ override subtraction when self is empty """
        if not self:
            return 0 - x
        raise ValueError




## setup

def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment, to be used as prefix for database collections")
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--outputdirectory", help="path to directory for exported data files", required=True)
    parser.add_argument("--samplesize", type=int, help="Sample size to resample frequencies for each sim run and replication")

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


    #### main program ####
    log.info("EXPORT DATA TO CSV - Experiment: %s", args.experiment)
    data.set_experiment_name(args.experiment)
    data.set_database_hostname(args.dbhost)
    data.set_database_port(args.dbport)
    config = data.getMingConfiguration(data.modules)
    ming.configure(**config)







if __name__ == "__main__":
    setup()

    # fieldnames = []
    # fieldnames.extend(["simulation_run_id", "replication", "subpop"])
    #
    # ofile  = open(args.filename, "wb")
    # writer = csv.DictWriter(ofile, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
    #
    # headers = dict((n,n) for n in fieldnames)
    # writer.writerow(headers)




    # the data cache has the following nested dict structure:  simid -> replicate -> subpop -> class:count

    cmap = DeepDefaultDict()
    cursor = data.ClassFrequencySampleUnaveraged.m.find(dict(),dict(timeout=False))

    for sample in cursor:
        sim_id = sample["simulation_run_id"]
        rep = sample["replication"]
        subpop = sample["subpop"]

        class_count_map = sample["class_count"]

        for cls, count in class_count_map.items():
            cmap[sim_id][rep][subpop][cls] += count


    class_set = set()
    for sim_id in cmap.keys():
        for rep in cmap[sim_id].keys():
            for subpop in cmap[sim_id][rep].keys():

                for cls, count in cmap[sim_id][rep][subpop].items():
                    log.info("sim: %s rep: %s subpop: %s class: %s freq: %s", sim_id, rep, subpop, cls, int(count))
                    class_set.add(cls)

    log.info("total number of classes: %s", len(class_set))


    for sim_id in cmap.keys():
        for rep in cmap[sim_id].keys():
            outputfile = args.outputdirectory + "/" + sim_id + "-" + str(rep) + ".txt"

            class_set = set()

            with open(outputfile, 'wb') as outfile:
                for sp in cmap[sim_id][rep].keys():
                    for cls in cmap[sim_id][rep][sp].keys():
                        class_set.add(cls)

                class_list = list(class_set)

                # write header row
                header = sim_id
                for cls in class_list:
                    header += "\t"
                    header += cls
                header += "\n"

                outfile.write(header)

                for sp in cmap[sim_id][rep].keys():
                    row = sp
                    for cls in class_list:
                        row += "\t"
                        count = cmap[sim_id][rep][sp][cls]
                        row += str(int(count)) if count != {} else str(0)
                    row += "\n"
                    outfile.write(row)







