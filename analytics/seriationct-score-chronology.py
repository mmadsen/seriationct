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


def setup():
    global config
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--gmlfile", help="Filename of the minmax-by-weight GML file to process and score",
                        required=True)

    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")

    config = parser.parse_args()

    script = __file__

    if config.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


    log.info("scoring GML file: %s", config.gmlfile)


def main():

    g = nx.read_gml(config.gmlfile)
    log.debug("graph nodes: %s", g.number_of_nodes())



    pass





if __name__ == "__main__":
    setup()
    main()



