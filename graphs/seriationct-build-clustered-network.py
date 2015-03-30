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
import networkx as nx
import numpy as np
import itertools
import random
import math
import os
import fnmatch


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--outputdirectory", help="path to directory for exported data files", required=True)
    parser.add_argument("--experiment", help="experiment name, used as prefix to GML files", required=True)
    parser.add_argument("--numclusters", type=int, help="number of clusters to create in the network model", default=3)
    parser.add_argument("--slices", type=int, help="number of slices to create", default=5)
    parser.add_argument("--nodespercluster", type=int, help="nodes per cluster", default=6)
    parser.add_argument("--interconnectfraction", type=float, help="density of intercluster edges compared to nodespercluster", default=0.3)
    parser.add_argument("--centroidmin", type=int, help="minimum X and Y for random cluster centroids", default=50)
    parser.add_argument("--centroidmax", type=int, help="maximum X and Y for random cluster centroids", default=400)
    parser.add_argument("--clusterspread", type=float, help="std deviation around cluster centroid for locating cluster nodes", default=10.0)

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

def random_interconnect_clusters(full_g, clusters_to_connect, cluster_id_ranges, num_interconnects):
    """
    Given a union graph of the clusters, and a tuple of two clusters to connect (given simply as integers),
    and a number of interconnects to make, randomly sample pairs of node IDs from the two clusters, and
    create an edge in the full union graph.
    """
    c1_ids = cluster_id_ranges[clusters_to_connect[0]]
    c2_ids = cluster_id_ranges[clusters_to_connect[1]]
    c1_nodes_chosen = random.sample(c1_ids, num_interconnects)
    c2_nodes_chosen = random.sample(c2_ids, num_interconnects)
    edge_list = zip(c1_nodes_chosen, c2_nodes_chosen)
    log.debug("Edges to construct: %s", edge_list)
    for new_edge in edge_list:
        full_g.add_edge(*new_edge)  # *new_edge unpacks the tuple

def assign_spatial_locations_to_cluster(full_g, cluster_ids, x_centroid, y_centroid, sd_dist, cluster_id):
    """
    Assigns xcoord and ycoord, and spatial node label, to nodes in a cluster based upon a random normal
    spread around a centroid.  Thus, we can achieve complete spatial overlap in clusters (and thus a spatial null model),
    by assigning the same centroid.
    """
    for id in cluster_ids:
        xcoord = abs(int(math.ceil(random.normalvariate(x_centroid, sd_dist))))
        ycoord = abs(int(math.ceil(random.normalvariate(y_centroid, sd_dist))))
        #log.debug("node %s at %s,%s",id,xcoord,ycoord)
        full_g.node[id]['xcoord'] = str(xcoord)
        full_g.node[id]['ycoord'] = str(ycoord)
        lab = "assemblage-"
        lab += str(xcoord)
        lab += "-"
        lab += str(ycoord)
        full_g.node[id]['label'] = lab
        full_g.node[id]['level'] = "None"
        full_g.node[id]['cluster_id'] = str(cluster_id)


def assign_uniform_intracluster_weights(g, weight):
    """
    Assigns a uniform weight to the edges in a cluster.

    """
    for a,b,d in g.edges(data=True):
        d['weight'] = weight
        d['unnormalized_weight'] = weight
        d['normalized_weight'] = weight


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
        dist = math.sqrt(abs(by - ay) + abs(bx - ax))
        d['distance'] = dist

def generate_random_complete_clusters_with_interconnect(num_clusters, num_nodes_cluster,
                                                        density_interconnect, centroid_range_tuple, cluster_spread):
    """
    Generates a random graph with M clusters, each of which is the complete graph of N nodes, with a fraction of nodes
    randomly interconnected between clusters.  This base graph will serve as slice 1 in a temporal network, and be
    evolved from this point. Given a tuple of integers for the range of possible centroid X and Y coordinates, the
    clusters are distributed around randomly chosen centroids, with a spread factor given.
    """
    clusters = []
    cluster_id_ranges = []
    starting_id = 0
    for i in range(0,num_clusters):
        g = nx.complete_graph(num_nodes_cluster)
        g = nx.convert_node_labels_to_integers(g, first_label=starting_id)

        assign_uniform_intracluster_weights(g, 0.5)

        clusters.append(g)
        cluster_ids = range(starting_id, starting_id + num_nodes_cluster)
        cluster_id_ranges.append(cluster_ids)
        starting_id += num_nodes_cluster
    full_g = nx.union_all(clusters)
    log.debug("range of cluster ids per cluster: %s", cluster_id_ranges)


    # now, we interconnect random nodes in the formerly independent clusters, given
    # the known range of
    num_interconnects = int(math.ceil(density_interconnect * num_nodes_cluster))
    log.debug("interconnecting %s random nodes between each cluster", num_interconnects)
    cluster_ids = range(0, num_clusters)
    paired_clusters = list(itertools.product(cluster_ids,cluster_ids))
    non_self_pairs = [tup for tup in paired_clusters if tup[0] != tup[1] ]
    unique_pairs = filter_mirror_tuples(non_self_pairs)
    log.debug("num cluster pairs without self-pairing: %s", len(unique_pairs))
    log.debug("cluster pairs: %s", unique_pairs)

    for pair in unique_pairs:
        random_interconnect_clusters(full_g,pair,cluster_id_ranges,num_interconnects)

    xcentroids = np.random.random_integers(centroid_range_tuple[0], centroid_range_tuple[1], num_clusters)
    ycentroids = np.random.random_integers(centroid_range_tuple[0], centroid_range_tuple[1], num_clusters)
    centroids = zip(xcentroids, ycentroids)

    for cluster in range(0, num_clusters):
        ids = cluster_id_ranges[cluster]
        centroid = centroids[cluster]
        log.debug("cluster %s has centroid at: %s", cluster, centroid)
        assign_spatial_locations_to_cluster(full_g, ids, centroid[0], centroid[1], cluster_spread, cluster)

    # now, given spatial coordinates, assign the distance value to each edge
    assign_node_distances(full_g)

    return full_g


def assign_to_slice(g, slice):
    """
    Annotate each node with an "appears_in_slice" attribute.  If the slice is the first,
    also assign a "parent_node" attribute of "initial" since we will not be assigning
    specific parents in this slice.
    """
    for n,d in g.nodes_iter(data=True):
        g.node[n]['appears_in_slice'] = str(slice)
        if slice == 1:
            g.node[n]['parent_node'] = 'initial'


def get_node_labels_for_cluster(g, cluster_id):
    """
    Given a graph whose nodes are labeled by "cluster_id", return the "label" attribute
    of those nodes matching the passed cluster ID.
    """
    labels = []
    for n,d in g.nodes_iter(data=True):
        if g.node[n]['cluster_id'] == str(cluster_id):
            labels.append(g.node[n]['label'])

    return labels

def assign_random_parent_from_previous(s_g, prev_g, num_clusters):
    """
    Given a slice, and the previous slice, go through nodes in the current slice,
    and choose a random parent from nodes in the same cluster.
    """
    # cache the previous slice assemblages by label so we don't ask every time
    cluster_label_map = dict()
    for i in range(0,num_clusters):
        cluster_label_map[i] = get_node_labels_for_cluster(prev_g, i)

    for n,d in s_g.nodes_iter(data=True):
        cluster = int(s_g.node[n]['cluster_id'])
        random_parent = random.choice(cluster_label_map[cluster])
        s_g.node[n]['parent_node'] = random_parent

def generate_sequential_slices(num_slices, num_clusters, num_nodes_cluster, density_interconnect, centroid_range_tuple, cluster_spread):
    """
    Using generate_random_complete_clusters_with_interconnect, create num_slices graphs, designating one the initial slice
    """
    slice_map = dict()
    for slice_id in range(1, num_slices+1):
        log.debug("creating slice %s", slice_id)
        s_g = generate_random_complete_clusters_with_interconnect(num_clusters, num_nodes_cluster,
                                                                  density_interconnect, centroid_range_tuple, cluster_spread)
        assign_to_slice(s_g,slice_id)
        slice_map[slice_id] = s_g

    log.debug("slice_map: %s", slice_map)

    # wire parents for slices after the initial slice
    for slice_id in range(2, num_slices+1):
        prev_id = slice_id - 1
        assign_random_parent_from_previous(slice_map[slice_id], slice_map[prev_id], num_clusters)

    return slice_map







if __name__ == "__main__":
    setup()

    centroid_tuple = (args.centroidmin, args.centroidmax)
    slicemap = generate_sequential_slices(args.slices,args.numclusters,args.nodespercluster,args.interconnectfraction,
                                          centroid_tuple,args.clusterspread)

    log.debug("slice map: %s", slicemap)

    # write slices as GML files
    basename = args.outputdirectory
    basename += "/"
    basename += args.experiment
    basename += "-"
    for i in range(1, args.slices + 1):
        slice = slicemap[i]
        filename = basename
        filename += str(i).zfill(3)
        filename += ".gml"
        nx.write_gml(slice, filename)

