#!/usr/bin/env python

# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

import ming
import logging as log
import argparse
import seriationct.data as data
import csv
import pprint as pp



## setup

def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment, to be used as prefix for database collections")
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--outputdirectory", help="path to directory for exported data files", required=True)

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


    cursor = data.SimulationMetadata.m.find(dict(),dict(timeout=False))
    header = "Assemblage " + '\t' + "OriginTime" + '\t' + "Duration" + '\n'
    for rec in cursor:

        log.debug("rec: %s", rec)

        sim_id = rec["simulation_run_id"]
        sim_id_clean = sim_id[9:]

        outputfile = args.outputdirectory + "/" + sim_id_clean +  "-assemblage-data.txt"

        durations = rec["subpopulation_durations"]
        origins = rec["subpopulation_origin_times"]

        with open(outputfile, 'wb') as outfile:
            outfile.write(header)

            for assem in durations.keys():
                row = assem
                row += '\t'
                row += str(origins[assem])
                row += '\t'
                row += str(durations[assem])
                row += '\n'

                outfile.write(row)






