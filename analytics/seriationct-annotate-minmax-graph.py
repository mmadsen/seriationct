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
import zipfile
import networkx as nx
import os
import pprint as pp


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--networkmodel", help="path to ZIP format network model containing GML slices", required=True)
    parser.add_argument("--inputfile", help="path to GML version of minmax seriation output file", required=True)

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

"""

 Example of a node in a slice of a networkmodel:

  node [
    id 0
    label "assemblage-9-6"
    appears_in_slice 1
    ycoord 6
    level "child"
    child_of "root"
    xcoord 9
    parent_node "assemblage-19-20"
  ]

"""


def get_node_for_key(name, key, graph):
    """
    Returns the node ID for a node with a given "name" as the value
    for attribute "key", or None if there is no match
    """
    for n in graph.nodes():
        log.debug("graph node: %s", graph.node[n])
        if graph.node[n][key] == name:
            return n
    return None


def copy_attributes_to_minmax(g_slice = None, g_mm = None):
    """
    Given the nodes in the slice, copy appropriate attributes
    to the minmax graph. The nodes are identified by their
    label/name attributes, since the ID numbers have no guarantee
    of matching.

    """
    log.debug("mm nodes: %s", g_mm.nodes())

    for slice_node in g_slice.nodes():
        log.debug("slice node: %s", g_slice.node[slice_node])

        mm_node_id = get_node_for_key(slice_node, "name", g_mm)

        if mm_node_id is None:
            # if we use samples of the original network model for seriation, not all of the slice
            # nodes will appear in the minmax graph.  this is NOT a bug, but we need to just
            # move on.
            continue

        g_mm.node[mm_node_id]['appears_in_slice'] = g_slice.node[slice_node]['appears_in_slice']
        g_mm.node[mm_node_id]['level'] = g_slice.node[slice_node]['level']
        g_mm.node[mm_node_id]['child_of'] = g_slice.node[slice_node]['child_of']
        g_mm.node[mm_node_id]['parent_node'] = g_slice.node[slice_node]['parent_node']

        log.debug("annotated: %s", g_mm.node[mm_node_id])


if __name__ == "__main__":
    setup()

    # parse the inputfile and calculate the output file name
    input_basename = os.path.basename(args.inputfile)
    root, ext = os.path.splitext(input_basename)
    input_path = os.path.dirname(args.inputfile)
    output_filename = input_path + root + "-annotated.gml"
    log.info("Processing input %s to output %s", input_basename, output_filename)

    # read the minmax input file
    mm = nx.read_gml(args.inputfile)

    # parse the slices in the networkmodel
    zf = zipfile.ZipFile(args.networkmodel, 'r')
    for file in [f for f in zf.namelist() if f.endswith(".gml")]:
        if file.startswith("__"):
            pass
        else:
            gml = zf.read(file)
            slice = nx.parse_gml(gml)

            copy_attributes_to_minmax(g_slice = slice, g_mm = mm)


    # now save the annotated graph to a file in GML format
    nx.write_gml(mm, output_filename)






