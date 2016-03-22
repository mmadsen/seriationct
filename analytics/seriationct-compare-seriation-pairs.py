#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Compare pairs of seriations from the same simulation runs, but performed with different algorithms (e.g., frequency
vs continuity).  The sets of seriations should be in different directories, which will be filled with GML files
output in the standard IDSS output filename format from SeriationCT input.  That is, a filename for a seriation
solution will be a GML file, and probably from a minmax by weight solution, as in:

f9704f0a-d4ad-11e5-b861-086266a2412a-0-sampled-500-slicestratified-0.12-resample-0-0.1-unimodal-filtered-minmax-by-weight-frequency.gml

Everything before the 5th occurrence of the "-" is the simulation run ID, and will be a key for pairing up the
seriations, although we could easily extend this approach to allow comparison across the rest of the information, such
as replicate value, sampled assemblage size, assemblage sample method, assemblage sample fraction, and other information.



"""
import networkx as nx
import logging as log
import argparse
import re
import os
import fnmatch


def setup():
    global config
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, default=0, help="turn on debugging output")
    parser.add_argument("--frequencydir", help="Directory with frequency seriation files",
                        required=True)
    parser.add_argument("--continuitydir", help="Directory with continuity seriation files",
                        required=True)

    config = parser.parse_args()

    script = __file__

    if config.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def simrunid_from_filename(fname):
    """
    Extracts the simulation run ID from a SeriationCT seriation output filename
    :param fname:
    :return:
    """
    occur = 6
    basename = os.path.basename(fname)
    indices = [x.start() for x in re.finditer("-", basename)]
    sim_id = basename[0:indices[occur-1]]
    log.debug("Processing graph: %s", sim_id)
    return sim_id



def main():
    frequency_solution_map = dict()
    continuity_solution_map = dict()
    simid_set = set()


    for file in os.listdir(config.frequencydir):
        if fnmatch.fnmatch(file, '*.gml'):
            full_fname = config.frequencydir + "/" + file
            simid = simrunid_from_filename(file)
            g = nx.read_gml(full_fname)
            frequency_solution_map[simid] = g
            simid_set.add(simid)

    for file in os.listdir(config.continuitydir):
        if fnmatch.fnmatch(file, '*.gml'):
            full_fname = config.continuitydir + "/" + file
            simid = simrunid_from_filename(file)
            g = nx.read_gml(full_fname)
            continuity_solution_map[simid] = g
            simid_set.add(simid)

    identical = 0
    different = 0
    unmatched_simids = 0
    diff_list = []
    unmatched_list = []

    for simid in simid_set:
        prob_flag = False

        if simid in frequency_solution_map:
            freq_g = frequency_solution_map[simid]
        else:
            unmatched_list.append(simid)
            unmatched_simids += 1
            prob_flag = True

        if simid in continuity_solution_map:
            cont_g = continuity_solution_map[simid]
        else:
            unmatched_list.append(simid)
            unmatched_simids += 1
            prob_flag = True

        if prob_flag is False:
            if nx.is_isomorphic(freq_g, cont_g):
                identical += 1
            else:
                different += 1
                diff_list.append(simid)


    print "identical: %s  different:  %s  unmatched: %s " % (identical, different, unmatched_simids)
    print "list of different sim_ids: "
    for id in diff_list:
        print id


    print "list of unmatched sim_ids: "
    for id in unmatched_list:
        print id









if __name__ == "__main__":
    setup()
    main()



