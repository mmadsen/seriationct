#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Creates a simple network model of N slices, each slice containing M populations, wired in a complete network.
Each population is derived from a randomly chosen population in slice N-1.  

"""

import csv
import argparse
import logging as log
import networkx as nx
import numpy as np
import itertools
import random
import copy
import math
import os
import fnmatch


def setup():
    global args, config, simconfig, location_cache

    # used to ensure that assemblage locations are unique across clusters if desired
    location_cache = set()

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--outputdirectory", help="path to directory for exported data files", required=True)
    parser.add_argument("--experiment", help="experiment name, used as prefix to GML files", required=True)
    parser.add_argument("--slices", type=int, help="number of slices to create", default=6)
    parser.add_argument("--numpopulations",type=int, help="number of populations per slice", default=10)
    parser.add_argument("--centroidx", type=int, help="centroid X for random population locations", default=300)
    parser.add_argument("--centroidy", type=int, help="centroid Y for random population locations", default=300)
    parser.add_argument("--spatialsd", type=int, help="SD of spread from centroid for random population locations", default = 100)
    parser.add_argument("--edgeweight", type=float, help="weight associated to edges", default=10)

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def debug_print_gml(g):
    for t in nx.generate_gml(g):
        print t




def filter_mirror_tuples(tuplist):
    filtered = []
    for tup in tuplist:
        found = False
        for testtup in filtered:
            mirrortup = (testtup[1],testtup[0])
            if tup == testtup or tup == mirrortup:
                found = True
        if found == False:
            filtered.append(tup)

    return filtered





def assign_node_distances(g):
    """
    Once spatial coordinates have been assigned, we can assign the distance attribute to edges.  We use the
    Euclidean distance given X,Y coordinates.
    """
    for a,b,d in g.edges(data=True):
        ax = int(g.node[a]['xcoord'])
        bx = int(g.node[b]['xcoord'])
        ay = int(g.node[a]['ycoord'])
        by = int(g.node[b]['ycoord'])
        dist = math.sqrt(pow(by - ay, 2) + pow(bx - ax, 2))
        d['distance'] = dist






def assign_uniform_intracluster_weights(g, weight):
    """
    Assigns a uniform weight to the edges in a cluster.

    """
    for a,b,d in g.edges(data=True):
        d['weight'] = weight
        d['unnormalized_weight'] = weight
        d['normalized_weight'] = weight


def generate_random_slice(slice_id,num_populations,edgeweight,centroidx,centroidy,spatialsd):
    """
    Generate a NetworkX graph object with num_populations nodes, located in random places around the coordinate
    represented by the centroid tuple, and cluster spread as variance.  Nodes are wired together in a complete
    graph.  All of the nodes belong to lineage #1 by default.

    :param num_populations:
    :param edgeweight:
    :param centroid_range_tuple:
    :param cluster_spread:
    :return:
    """
    g = nx.complete_graph(num_populations)
    start_node_id = (slice_id - 1) * num_populations
    log.debug("nodes labeled: %s", range(start_node_id, start_node_id + num_populations))
    nx.convert_node_labels_to_integers(g, start_node_id)

    for id in g.nodes():
        xcoord = 0.0
        ycoord = 0.0

        while (True):
            xcoord = abs(int(math.ceil(random.normalvariate(centroidx, spatialsd))))
            ycoord = abs(int(math.ceil(random.normalvariate(centroidy, spatialsd))))
            location = (xcoord, ycoord)
            if location not in location_cache:
                location_cache.add(location)
                break

        # log.debug("node %s at %s,%s",id,xcoord,ycoord)
        g.node[id]['xcoord'] = str(xcoord)
        g.node[id]['ycoord'] = str(ycoord)
        lab = "assemblage-"
        lab += str(xcoord)
        lab += "-"
        lab += str(ycoord)
        g.node[id]['label'] = lab
        g.node[id]['level'] = "None"
        g.node[id]['cluster_id'] = 1
        g.node[id]['lineage'] = 1
        g.node[id]['appears_in_slice'] = slice_id
        if slice_id == 1:
            g.node[id]['parent_node'] = 'initial'

    assign_uniform_intracluster_weights(g, edgeweight)
    assign_node_distances(g)

    return g



def assign_random_parent_from_previous(s_g, prev_g):
    """
    Given a slice, and the previous slice, go through nodes in the current slice,
    and choose a random parent from nodes in the same cluster.
    """
    # cache the previous slice assemblages by label so we don't ask every time
    for n,d in s_g.nodes_iter(data=True):
        random_parent = random.choice(prev_g.nodes())

        s_g.node[n]['parent_node'] = prev_g.node[random_parent]['label']
        log.debug("random parent: %s with label %s", random_parent, prev_g.node[random_parent]['label'])






def generate_slices(num_slices, num_populations, edgeweight, centroidx, centroidy, spatialsd):
    """
    Using generate_random_complete_clusters_with_interconnect, create num_slices graphs, designating one the initial slice
    """
    slice_map = dict()

    for slice_id in range(1, num_slices+1):
        log.debug("creating slice %s", slice_id)
        s_g = generate_random_slice(slice_id,num_populations,edgeweight,centroidx, centroidy, spatialsd)
        slice_map[slice_id] = s_g

    log.debug("slice_map: %s", slice_map)

    # wire parents for slices after the initial slice
    for slice_id in range(2, num_slices+1):
        prev_id = slice_id - 1
        assign_random_parent_from_previous(slice_map[slice_id], slice_map[prev_id])

    return slice_map



def generate_xyrows_for_slice(s_g):
    rows = []
    for n,d in s_g.nodes_iter(data=True):
        row = s_g.node[n]['label']
        row += '\t'
        row += s_g.node[n]['xcoord']
        row += '\t'
        row += s_g.node[n]['ycoord']
        row += '\n'
        rows.append(row)
    return rows



if __name__ == "__main__":
    setup()

    slicemap = generate_slices(args.slices,
                                args.numpopulations,
                                args.edgeweight,
                                args.centroidx,
                                args.centroidy,
                                args.spatialsd)

    log.debug("slice map: %s", slicemap)

    # write slices as GML files
    basename = args.outputdirectory
    basename += "/"
    basename += args.experiment
    basename += "-"

    xyheader = "assemblage\teasting\tnorthing\n"
    xyrows = []

    for i in range(1, args.slices + 1):
        slice = slicemap[i]

        xyrows.extend(generate_xyrows_for_slice(slice))

        filename = basename
        filename += str(i).zfill(3)
        filename += ".gml"
        nx.write_gml(slice, filename)

    xybasename = args.outputdirectory
    xybasename += "/"
    xybasename += args.experiment
    xybasename += 'XY.txt'

    with open(xybasename, 'wb') as xyfile:
        xyfile.write(xyheader)
        for row in xyrows:
            xyfile.write(row)


