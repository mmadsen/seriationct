#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Analyze the minmax-by-weight GML output from seriation and score the correctness of chronological order
in the resulting seriation, taking into account contemporaneous assemblages (i.e., present in the same slice).

For example, if slice 1 has assemblages A and B, slice 2 has C and D, and slice 3 E and F, a seriation ordering
with ABCDEF is a perfect order, but so is BADCFE -- the equivalence classes are [AB]-[CD]-[EF].

Scoring system:  a perfect order has zero mismatches.  A perfect order in the absence of lineage branches is also
a linear order, with no branches.

TODO:  This script DOES NOT yet deal with overlapping assemblages.

"""
import networkx as nx
import logging as log
import argparse
import re
import os

def setup():
    global config
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, default=0, help="turn on debugging output")
    parser.add_argument("--gmlfile", help="Filename of the minmax-by-weight GML file to process and score",
                        required=True)

    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--testdata", type=bool, default=False, help="Flag to indicate that gml file name does not follow UUID conventions")
    parser.add_argument("--sliceskipfactor", type=int, default=1, help="Allowed skip between slices to count as adjacent, used when eliminating assemblages for testing")

    config = parser.parse_args()

    script = __file__

    if config.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def main():

    if config.testdata == False:
        occur = 6 # get the UUID and replication number
        basename = os.path.basename(config.gmlfile)
        indices = [x.start() for x in re.finditer("-", basename)]
        graph_name = basename[0:indices[occur-1]]
        log.debug("Processing graph: %s", graph_name)
    else:
        graph_name = config.gmlfile


    g = nx.read_gml(config.gmlfile)
    #log.debug("graph nodes: %s", g.number_of_nodes())

    # first build a map of nodes and the slices they occur in
    node_to_slice_map = dict()
    node_to_assem_map = dict()
    slice_to_nodes_map = dict()
    slice_set = set()

    # walk through nodes, checking each node from slice S to make sure that its
    # neighbors are from S itself, S-1, or S+1.  Nodes from S that are connected to
    # anything else, or have no neighbors and are isolates, are a problem (although
    # isolates are not a problem in real data, necessarily)

    violations = 0
    for n,d in g.nodes_iter(data=True):
        #log.debug("processing node: %s", n)
        #node_slice = int(g.node[n]['appears_in_slice'])
        neighbors = g.neighbors(n)
        if len(neighbors) == 0:
            # isolated node
            violations += 1
            log.debug("node %s isolated.  violations: %s", n, violations)
            #continue

        # for neighbor in neighbors:
        #     neighbor_slice = int(g.node[neighbor]['appears_in_slice'])
        #     diff = abs(neighbor_slice - node_slice)
        #     log.debug("node in slice %s  neighbor in slice %s - diff %s", node_slice, neighbor_slice, diff)
        #     if diff > 1:
        #         # a good relationship would be one slice away in either direction, or zero
        #         violations += 1
        #         log.debug("node: %s  neighbor: %s temporal diff: %s total violations: %s", n, neighbor, diff, violations)

    for edge in g.edges_iter():
        end1 = edge[0]
        end2 = edge[1]
        end1_slice = int(g.node[end1]['appears_in_slice'])
        end2_slice = int(g.node[end2]['appears_in_slice'])
        diff = abs(end1_slice - end2_slice)
        log.debug("%s in slice %s, %s in slice %s - diff %s", end1, end1_slice, end2,   end2_slice, diff)
        if diff > int(config.sliceskipfactor):
            # a good relationship would be one slice away in either direction, or zero
            violations += 1
            log.debug("end1: %s  end2: %s temporal diff: %s total violations: %s", end1, end2, diff, violations)




    print "%s,%s" % (graph_name, violations)








if __name__ == "__main__":
    setup()
    main()



