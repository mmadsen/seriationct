#!/home/ubuntu/anaconda2/bin/python

# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

import ming
import csv
import os
import logging as log
import argparse
import seriationct.data as data
import json
import resource

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

# broken out to allow line profiling
#@profile
def doExport():
    # the data cache has the following nested dict structure:  simid -> replicate -> subpop -> class:count

    cmap = DeepDefaultDict()

    cnt = 0
    with open(args.filename) as f:
        for line in f:
            cnt += 1
            if cnt % 100000 == 0:
                print "rows: %s  memory usage (MB): %s" % (cnt, (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000))
            sample = None
            try:
                sample = json.loads(line.replace("\\", r"\\"))
            except ValueError:
                print "JSON parsing error in line %s" % (cnt + 1)
                continue
            sim_id = sample["simulation_run_id"]
            rep = sample["replication"]
            subpop = sample["subpop"]

            class_count_map = sample["class_count"]

            for cls, count in class_count_map.items():
                cmap[sim_id][rep][subpop][cls] += count

    # conditional either we sample trait counts (which will reduce the list of traits we put in the header),
    # or output the full list of counts (which will put every trait in the header)

    print "(debug) file reading complete, now processing to collapse and aggregate"

    class_set = set()
    for sim_id in cmap.keys():
        for rep in cmap[sim_id].keys():
            for subpop in cmap[sim_id][rep].keys():
                for cls, count in cmap[sim_id][rep][subpop].items():
                    class_set.add(cls)

    print "(debug) memory usage after aggregation of classes: %s", (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000)

    log.info("total number of classes: %s", len(class_set))

    print "(debug) writing output files"

    for sim_id in cmap.keys():
        for rep in cmap[sim_id].keys():


            sim_id_clean = sim_id[9:]


            outputfile = args.outputdirectory + "/" + sim_id_clean + "-" + str(rep) + ".txt"

            class_set = set()

            with open(outputfile, 'wb') as outfile:
                for sp in cmap[sim_id][rep].keys():
                    for cls in cmap[sim_id][rep][sp].keys():
                        class_set.add(cls)

                class_list = list(class_set)

                # write header row
                header = "Assemblage_Name"
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





## setup

def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment, to be used as prefix for database collections")
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--filename", help="filename containing mongoexport json dump")
    parser.add_argument("--outputdirectory", help="path to directory for exported data files", required=True)

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


    #### main program ####
    log.info("EXPORT DATA TO CSV - Experiment: %s", args.experiment)


if __name__ == "__main__":
    setup()
    doExport()








