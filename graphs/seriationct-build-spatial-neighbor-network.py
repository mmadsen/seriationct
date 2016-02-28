#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Creates a simple network model of N slices, each slice containing M populations, wired in a lattice with
mostly short-distance, nearest-neighbor connections (but with a configurable possibility of some long-distance,
small world type connections.
Each population is derived from a spatially close population in slice N-1.

Spatial configuration:

The overall size of the region is arbitrary, so we'll determine it from the number of subpopulations
expected per time slice, and ensure that there is some separation between populations so that we can
create "near" and "far" assemblages, given the requested "shape" of the region.  The shape is governed
entirely by the "aspect ratio", which allows us to create square or very thin, long regions (e.g., as
we would expect following a river).

In the setup phase, we first calculate the maximum X and Y coordinates of the region.  An easy way to
do this is to act like a population takes up a 10x10 portion of space, and enforce the constraint that
we want enough space in the region that the total number of subpopulations occupy less than a critical
density of the space (given this hypothetical "size").  So, if had an aspect ratio of 1.0 (square),
and wanted 25 subpopulations per time slice, and a critical density of 1%, we would do as follows:

25 subpopulations x 100 = 2500 units occupied by subpopulations
2500 / 0.01 = 250,000 units needed for region
Given a square region, maximum X and Y coordinates are thus sqrt(250K) = 500

So if we scatter 25 subpopulations uniformly across a 500 x 500 region, we get the desired effect.

If the aspect ratio is different from square, say 3.0, then it means one side is 3 times the length
of the other, which if area is A and the ratio of sides is R:

(R * side) * side = A
R * side^2 = A
side = sqrt(A/R)

short is just side, long is side * R


Algorithm for finding "parents" between time slices.
(assumes that there are N subpopulations already randomly assigned to spatial positions within the region)

For each layer i, where i = 1 to numslices:

    build a two-level dict with distances between any vertex in layer i and vertices in layer i-1
    for each vertex v in layer i:

        construct probability weights for each vertex in layer i-1, based upon the inverse distance to vertex v
        select a random choice from the vertices in layer i-1, with weights (np.random.choice accepts weights)
        link this random choice as parent attribute

Algorithm for wiring the slices:

We use the same approach.

1.  For each vertex, generate a random number of neighbors (probably from a clipped lognormal with specified mean and sd
2.  If the vertex already has edges, reduce the number of new edges to create by that amount
3.  For the remaining new vertices, choose random edges according to the same distance weighting algorithm as we use for parents





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
    parser.add_argument("--spatialaspectratio", type=float, help="Aspect ratio for the overall space of the region.  "
                                                                 "1.0 is square, while larger values are increasingly thinner, longer rectangles", default=1.0)
    parser.add_argument("--edgeweight", type=float, help="weight associated to edges", default=10)
    parser.add_argument("--exponentialcoefficient", type=float, help="Decay factor governing steepness of exponential distance decay kernel, larger is steeper", default=2.0)
    parser.add_argument("--meanedgesperpopulation", type=float, help="average number of connections per community, biased by distance", default=3.0)
    parser.add_argument("--sdedgesperpopulation", type=float, help="sd number of connections per community, biased by distance", default=1.0)


    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def debug_print_gml(g):
    for t in nx.generate_gml(g):
        print t


def find_maximum_regional_coordinates(aspectratio, numpopulations):
    """
    Given the aspect ratio desired for the regional model (square, long thin, as defined by the ratio of sides),
    and the number of populations, deliver an XY coordinate system (in terms of maxima) that yields a 1% ratio
    of occupied space if each population takes up a 10x10 unit in the coordinate system.

    :param aspectratio:
    :param numpopulations:
    :return: tuple of maximum_x, maximum_y
    """
    occupied_space = 100. * numpopulations
    total_area = occupied_space / 0.01

    side = math.sqrt(total_area / aspectratio)
    x = side
    y = aspectratio * side

    return (x,y)





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
        ax = float(g.node[a]['xcoord'])
        bx = float(g.node[b]['xcoord'])
        ay = float(g.node[a]['ycoord'])
        by = float(g.node[b]['ycoord'])
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



def generate_random_slice(slice_id,num_populations,edgeweight,max_x_coord,max_y_coord):
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
    g = nx.empty_graph(num_populations)
    start_node_id = (slice_id - 1) * num_populations
    log.debug("nodes labeled: %s", range(start_node_id, start_node_id + num_populations))
    nx.convert_node_labels_to_integers(g, start_node_id)

    for id in g.nodes():
        xcoord = 0.0
        ycoord = 0.0

        while (True):
            xcoord = np.random.random_integers(0, max_x_coord, size=1).astype(np.int64)[0]
            ycoord = np.random.random_integers(0, max_y_coord, size=1).astype(np.int64)[0]

            location = (int(xcoord), int(ycoord))
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
        g.node[id]['lineage_id'] = 1
        g.node[id]['appears_in_slice'] = slice_id
        if slice_id == 1:
            g.node[id]['parent_node'] = 'initial'

    # now we wire up the edges in the slice
    assign_distance_weighted_edges_to_slice(g, max_x_coord,max_y_coord)

    assign_uniform_intracluster_weights(g, edgeweight)
    assign_node_distances(g)

    return g


def build_distance_map_to_parents(s_g, prev_g):
    """
    Constructs two level map of distances from each node in the current slice, to every node in the previous slice

    :param s_g:
    :param prev_g:
    :return: dict of dicts
    """

    # Go through the nodes in the current layer, and loop over the nodes in the
    # previous layer, calculating the distance
    dist_map = dict()
    for n,d in s_g.nodes_iter(data=True):
        n_label = s_g.node[n]['label']
        dist_map[n_label] = dict()
        n_x = float(s_g.node[n]['xcoord'])
        n_y = float(s_g.node[n]['ycoord'])

        for l,d in prev_g.nodes_iter(data=True):
            l_label = prev_g.node[l]['label']
            l_x = float(prev_g.node[l]['xcoord'])
            l_y = float(prev_g.node[l]['ycoord'])
            dist = math.sqrt(pow(l_y - n_y, 2) + pow(l_x - n_x, 2))
            dist_map[n_label][l_label] = dist

    return dist_map

def build_distance_map_to_self(g):
    """
    Constructs twolevel map of distances from each node in the current slice, to other nodes in the same slice

    :param g:
    :return:
    """
    dist_map = dict()
    for n,d in g.nodes_iter(data=True):
        n_label = g.node[n]['label']
        dist_map[n_label] = dict()
        n_x = int(g.node[n]['xcoord'])
        n_y = int(g.node[n]['ycoord'])

        for l,d in g.nodes_iter(data=True):
            # we don't need self distances
            if l == n:
                continue
            l_label = g.node[l]['label']
            l_x = float(g.node[l]['xcoord'])
            l_y = float(g.node[l]['ycoord'])
            dist = math.sqrt(pow(l_y - n_y, 2) + pow(l_x - n_x, 2))
            dist_map[n_label][l_label] = dist

    return dist_map


def calculate_community_distance_statistics(g, ignore_actual=True):
    """
    Calculates both the min/max/average edge distance, taking each edge into account only once,
    and the possible values for these given all pairs of vertices whether linked or not.  There
    are enough returned statistics that the function returns a dict with keys:  min_actual,
    mean_potential, etc.

    For actual values, pass "ignore_actual=False".  This allows the function to be used on
    sets of vertices with geographic coordinates but before we actually wire the edges.

    :param g:
    :param: ignore_actual - boolean to not calculate statistics for actual edges, since we might not have any yet.
    :return: dict
    """
    actual_distances = []
    potential_distances = []

    nodes = g.nodes()
    for i,j in itertools.product(nodes, nodes):
        if i == j:
            continue
        i_x = float(g.node[i]['xcoord'])
        i_y = float(g.node[i]['ycoord'])
        j_x = float(g.node[j]['xcoord'])
        j_y = float(g.node[j]['ycoord'])
        dist = math.sqrt(pow(i_y - j_y, 2) + pow(i_x - j_x, 2))
        if g.has_edge(i,j):
            actual_distances.append(dist)
        potential_distances.append(dist)

    # log.debug("actual dist: %s", actual_distances)
    # log.debug("potential dist: %s", potential_distances)

    res = dict()
    if ignore_actual == False:
        res['actual_min'] = np.amin(actual_distances)
        res['actual_max'] = np.amax(actual_distances)
        res['actual_mean'] = np.mean(actual_distances)
        res['edge_density'] = float(len(actual_distances)) / float(len(potential_distances))
    res['potential_min'] = np.amin(potential_distances)
    res['potential_max'] = np.amax(potential_distances)
    res['potential_mean'] = np.mean(potential_distances)

    # log.debug("res: %s", res)
    return res





def build_map_from_vertex_label_to_id(g):
    """
    Keep a map from vertex label to node ID, since we don't want to relabel the nodes in this context

    :param g:
    :return: dict
    """
    label_map = dict()
    for n,d in g.nodes_iter(data=True):
        label_map[g.node[n]['label']] = n

    return label_map



def build_weighted_node_lists_linear_decay(node, dist_map, max_x_coord, max_y_coord):
    """
    Build a list of neighbors for the focal node, and a list of probability weights where
    the probability is linear in the inverse of distance (smaller distances equal larger weights)

    :param node:
    :param dist_map:
    :return:
    """
    node_list = []
    weight_list = []

    distances = []

    for label,d in dist_map[node].items():
        distances.append(d)
        node_list.append(label)

    n_distances = np.asarray(distances)
    # log.debug("distances: %s", n_distances)

    # divisor is the maximum possible distance in the region, which is the distance from origin
    # diagonally to the max x and max y coordinate.
    n_total = math.sqrt(max_x_coord**2 + max_y_coord**2)
    frac_distances = n_distances / n_total
    # log.debug("frac distances: %s",frac_distances)

    frac_distances = 1.0 - frac_distances
    # log.debug("inverse frac distances: %s", frac_distances)

    total_frac_distance = np.sum(frac_distances)
    frac_distances = frac_distances / total_frac_distance

    # log.debug("scaled frac distances: %s", frac_distances)

    total_weights = sum(frac_distances)

    return (node_list, frac_distances)


def build_weighted_node_lists_exponential_decay(node, dist_map, average_potential_dist, alpha):
    """
    Build a list of neighbors for the focal node, and a list of probability weights where
    the probability is linear in the inverse of distance (smaller distances equal larger weights)

    :param node:
    :param dist_map:
    :param average_potential_dist:
    :return:
    """
    node_list = []
    weight_list = []

    distances = []

    for label,d in dist_map[node].items():
        distances.append(d)
        node_list.append(label)

    n_distances = np.asarray(distances)
    # log.debug("distances: %s", n_distances)

    # raw exponential weights are exp(-distance[i]/average_potential_dist)
    raw_weights = np.exp(alpha * (n_distances * -1)/average_potential_dist)
    #log.debug("raw exponential weights: %s", raw_weights)

    total_weights = np.sum(raw_weights)

    scaled_weights = raw_weights / total_weights
    #log.debug("scaled exponential weights: %s", scaled_weights)

    return (node_list, scaled_weights)





def assign_random_parent_from_previous(s_g, prev_g, max_x_coord, max_y_coord):
    """
    Given a slice, and the previous slice, go through nodes in the current slice,
    and choose a random parent from nodes in the same cluster.
    """

    dist_map = build_distance_map_to_parents(s_g, prev_g)
    dist_stat = calculate_community_distance_statistics(s_g, ignore_actual=False)

    # cache the previous slice assemblages by label so we don't ask every time
    for n,d in s_g.nodes_iter(data=True):
        # find a random parent weighted by distance, so that close vertices have more weight
        n_label = s_g.node[n]['label']
        parent_list, weights = build_weighted_node_lists_exponential_decay(n_label, dist_map, dist_stat['potential_mean'], args.exponentialcoefficient)

        # the parent list is already node labels, so random.choice will give us a random label
        # weighted by the inverse distance, so we should see parents being "close"
        random_parent = np.random.choice(parent_list,p=weights)

        s_g.node[n]['parent_node'] = random_parent
        # log.debug("random parent: %s", random_parent)


def assign_distance_weighted_edges_to_slice(g, max_x_coord, max_y_coord):
    """
    Takes an empty graph with N nodes, and given parameters for mean/sd node degree, and generates
    random inverse-distance-weighted edges, so that neighbors are preferentially geographically close.

    :param g:
    :return:
    """
    # generate a random number of edges for each vertex, drawn from a lognormal distribution, clipped to 1 on the
    # lower limit (no isolated vertices) and the number of populations minus one on the upper.
    edges_per_vertex = np.clip(np.random.lognormal(args.meanedgesperpopulation,
                                                   args.sdedgesperpopulation, size = args.numpopulations), 1, args.numpopulations-1).astype(np.int64)
    # log.debug("edges per vertex: %s", edges_per_vertex)
    # to allow us to index the number of edges, poor man's generator
    edge_ix = 0
    dist_map = build_distance_map_to_self(g)
    # we need the latter because we usually prefer to deal in node labels, but edge wiring requires IDs.
    label_map = build_map_from_vertex_label_to_id(g)
    dist_stat = calculate_community_distance_statistics(g, ignore_actual=True)

    for v,d in g.nodes_iter(data=True):
        num_neighbors = edges_per_vertex[edge_ix]
        # reduce by the number of existing edges
        num_neighbors -= len(g.neighbors(v))
        if num_neighbors < 1:
            continue

        # log.debug("selecting %s neighbors", num_neighbors)

        n_label = g.node[v]['label']
        other_node_list, weights = build_weighted_node_lists_exponential_decay(n_label, dist_map, dist_stat['potential_mean'], args.exponentialcoefficient)
        # log.debug("other node list: %s", other_node_list)
        # log.debug("weights: %s", weights)

        random_neighbor_list = np.random.choice(other_node_list, size=num_neighbors, p=weights)
        # log.debug("selected neighbors: %s", random_neighbor_list)

        # go over random neighbors and wire them with edges
        for neighbor_label in random_neighbor_list:
            g.add_edge(v, label_map[neighbor_label])



def generate_slices(num_slices, num_populations, edgeweight, max_x_coord, max_y_coord):
    """
    Using generate_random_complete_clusters_with_interconnect, create num_slices graphs, designating one the initial slice
    """
    slice_map = dict()

    for slice_id in range(1, num_slices+1):
        log.debug("creating slice %s", slice_id)
        s_g = generate_random_slice(slice_id,num_populations,edgeweight,max_x_coord, max_y_coord)
        slice_map[slice_id] = s_g
        stats = calculate_community_distance_statistics(s_g, ignore_actual=False)
        log.debug("slice stats: %s", stats)

    # log.debug("slice_map: %s", slice_map)

    # wire parents for slices after the initial slice
    for slice_id in range(2, num_slices+1):
        prev_id = slice_id - 1
        assign_random_parent_from_previous(slice_map[slice_id], slice_map[prev_id], max_x_coord, max_y_coord)

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

    (max_x_coord, max_y_coord) = find_maximum_regional_coordinates(args.spatialaspectratio, args.numpopulations)

    slicemap = generate_slices(args.slices,
                                args.numpopulations,
                                args.edgeweight,
                                max_x_coord,
                                max_y_coord)

    # log.debug("slice map: %s", slicemap)

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
    xybasename += '-XY.txt'

    with open(xybasename, 'wb') as xyfile:
        xyfile.write(xyheader)
        for row in xyrows:
            xyfile.write(row)


