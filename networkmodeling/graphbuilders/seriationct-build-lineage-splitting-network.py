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
    parser.add_argument("--modelid", help="model ID for a specific network model instance", required = True)
    parser.add_argument("--experiment", help="experiment name, used as prefix to GML files", required=True)
    parser.add_argument("--numclusters", type=int, help="number of clusters to create in the network model", default=3)
    parser.add_argument("--slices", type=int, help="number of slices to create", default=6)
    parser.add_argument("--nodespercluster", type=int, help="nodes per cluster", default=6)
    parser.add_argument("--interconnectfraction", type=float, help="density of intercluster edges compared to nodespercluster", default=0.3)
    parser.add_argument("--centroidmin", type=int, help="minimum X and Y for random cluster centroids", default=50)
    parser.add_argument("--centroidmax", type=int, help="maximum X and Y for random cluster centroids", default=400)
    parser.add_argument("--clusterspread", type=float, help="std deviation around cluster centroid for locating cluster nodes", default=10.0)
    parser.add_argument("--intercluster_edgeweight", type=float, help="weight assigned to edges which span two clusters", default=1)
    parser.add_argument("--intracluster_edgeweight", type=float, help="weight associated to edges which occur within a cluster", default=10)
    parser.add_argument("--numlineages", type=int, help="number of distinct lineages to split or coalesce (must be larger than numclusters", default=2)
    parser.add_argument("--direction", choices=['split','coalesce'], default="split", required=True, help="temporal direction of lineage activity.  split indicates a single lineage splitting into several, coalesce indicates multiple lineages coming together into one")
    parser.add_argument("--change_time", type=int, help="slice number where split or coalescence occurs", default=2)

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
    log.info("clusters_to_connect: %s", clusters_to_connect)
    log.info("cluster_id_ranges: %s", cluster_id_ranges)
    c1_ids = cluster_id_ranges[clusters_to_connect[0]]
    c2_ids = cluster_id_ranges[clusters_to_connect[1]]
    c1_nodes_chosen = random.sample(c1_ids, num_interconnects)
    c2_nodes_chosen = random.sample(c2_ids, num_interconnects)
    edge_list = zip(c1_nodes_chosen, c2_nodes_chosen)
    log.debug("Edges to construct: %s", edge_list)
    for new_edge in edge_list:

        full_g.add_edge(new_edge[0], new_edge[1],
                        weight=args.intercluster_edgeweight,
                        unnormalized_weight=args.intercluster_edgeweight,
                        normalized_weight=args.intercluster_edgeweight)  # *new_edge unpacks the tuple

def assign_spatial_locations_to_cluster(full_g, cluster_ids, x_centroid, y_centroid, sd_dist, cluster_id):
    """
    Assigns xcoord and ycoord, and spatial node label, to nodes in a cluster based upon a random normal
    spread around a centroid.  Thus, we can achieve complete spatial overlap in clusters (and thus a spatial null model),
    by assigning the same centroid.  No duplicate coordinates are assigned.
    """

    for id in cluster_ids:
        xcoord = 0.0
        ycoord = 0.0

        while(True):
            xcoord = abs(int(math.ceil(random.normalvariate(x_centroid, sd_dist))))
            ycoord = abs(int(math.ceil(random.normalvariate(y_centroid, sd_dist))))
            location = (xcoord,ycoord)
            if location not in location_cache:
                location_cache.add(location)
                break


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
        dist = math.sqrt(pow(by - ay, 2) + pow(bx - ax, 2))
        d['distance'] = dist





def create_cluster_interconnect_schedule():
    """
    Given the type of model (lineage split, coalescence), and the number of clusters and lineages,
    form a schedule for which clusters are to be connected in each slice.  The actual density
    of interconnections is still controlled by the interconnectfraction parameter.

    This method constructs a dict whose keys are slice ID's, and values that are lists of tuples
    of cluster ID's to interconnect.
    """
    num_clusters_per_lineage = int(args.numclusters)
    total_clusters = num_clusters_per_lineage * args.numlineages
    cluster_ids = range(0, total_clusters)
    interconnect_schedule = dict()
    slice_ids = range(1, args.slices+1)
    cluster_to_lineage_map = dict()

    log.debug("cluster_ids: %s", cluster_ids)
    log.debug("slice_ids: %s", slice_ids)

    # calculate how to break up the lineages
    lineage_list = dict()
    for lineage in range(1,args.numlineages+1):
        lineage_list[lineage] = []


    for lineage in range(1,args.numlineages+1):
        for i in range(0,num_clusters_per_lineage):
            cluster = cluster_ids.pop()
            log.debug("assigning cluster %s to lineage %s", cluster, lineage)
            lineage_list[lineage].append(cluster)
            cluster_to_lineage_map[cluster] = lineage
    # # handle the remainder if numclusters % numlineages != 0
    # for i in range(0,len(cluster_ids)):
    #     lineage_list[i].append(cluster_ids.pop())

    log.debug("lineage list to apply to split-phase in model: %s", lineage_list)


    # now calculate the actual tuples to interconnect
    # need a fresh list of the full cluster ID's since we used pop() above
    cluster_ids = range(0, args.numclusters)
    for slice in slice_ids:
        if args.direction == 'split':
            if slice < args.change_time:
                # split models start off with the full list of clusters interconnected
                interconnect_list = create_interconnect_tuples_from_clusterids(cluster_ids)
            else:
                interconnect_list = []
                for lineage in range(1,args.numlineages+1):
                    interconnect_list.extend(create_interconnect_tuples_from_clusterids(lineage_list[lineage]))
        elif args.direction == 'coalesce':
            if slice < args.change_time:
                interconnect_list = []
                for lineage in range(1,args.numlineages+1):
                    interconnect_list.extend(create_interconnect_tuples_from_clusterids(lineage_list[lineage]))
            else:
                interconnect_list = create_interconnect_tuples_from_clusterids(cluster_ids)

        interconnect_schedule[slice] = interconnect_list

    log.debug("interconnect schedule: %s", interconnect_schedule)

    return (interconnect_schedule,cluster_to_lineage_map)


def create_interconnect_tuples_from_clusterids(clusterid_list):
    """
    For a list of cluster id's, construct the cartesian product of the id's, filtering out
    self-pairs (1,1) and mirror images (ie., keep 1,2 but not 2,1).  This yields n(n-1)/2
    edges between n cluster id's.
    """
    paired_clusters = list(itertools.product(clusterid_list,clusterid_list))
    non_self_pairs = [tup for tup in paired_clusters if tup[0] != tup[1] ]
    unique_pairs = filter_mirror_tuples(non_self_pairs)
    log.debug("num cluster pairs without self-pairing or mirror pairs: %s", len(unique_pairs))
    log.debug("cluster pairs: %s", unique_pairs)
    return unique_pairs



def generate_random_complete_clusters_with_interconnect(num_clusters, num_nodes_cluster,
                                                        density_interconnect, centroid_range_tuple,
                                                        cluster_spread, interconnects_for_slice):
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

        assign_uniform_intracluster_weights(g, args.intracluster_edgeweight)

        clusters.append(g)
        cluster_ids = range(starting_id, starting_id + num_nodes_cluster)
        cluster_id_ranges.append(cluster_ids)
        starting_id += num_nodes_cluster
    full_g = nx.union_all(clusters)
    log.debug("range of cluster ids per cluster: %s", cluster_id_ranges)


    # now, we interconnect random nodes in the formerly independent clusters, given
    num_interconnects = int(math.ceil(density_interconnect * num_nodes_cluster))
    log.debug("interconnecting %s random nodes between each cluster", num_interconnects)
    for pair in interconnects_for_slice:
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


def label_nodes_with_lineage(slice_id, slice,cluster_to_lineage_map):
    """
    Assign a lineage label to each node based upon its existing cluster label,
    previously assigned.  Depending upon the model type, assign the
    initial unsplit root, or the coalesced condition, its own unique lineage label of zero
    """
    # map unique lineage ID to the root of the split, or the coalesced lineage
    # depending upon model type.  Copy the cluster to lineage map because
    # we're going to modify the copy.

    cmap = copy.deepcopy(cluster_to_lineage_map)
    if args.direction == 'split':
        log.debug("labeling the initial slices as root of lineage with later split")
        if slice_id < args.change_time:
            for key in cmap.keys():
                cmap[key] = 0
    elif args.direction == 'coalesce':
        log.debug("labeling the latest slices as root of lineage with initial split that coalesces")
        if slice_id >= args.change_time:
            for key in cmap.keys():
                cmap[key] = 0

    log.debug("cmap used for slice %s: %s", slice_id, cmap )

    for n,d in slice.nodes_iter(data=True):
        cid = int(slice.node[n]['cluster_id'])
        slice.node[n]['lineage_id'] = str(cmap[cid])


def generate_sequential_slices(num_slices, num_clusters, num_nodes_cluster, density_interconnect, centroid_range_tuple, cluster_spread):
    """
    Using generate_random_complete_clusters_with_interconnect, create num_slices networkmodeling, designating one the initial slice
    """
    slice_map = dict()

    (interconnect_schedule,cluster_to_lineage_map) = create_cluster_interconnect_schedule()

    log.debug("cluster to lineage: %s", cluster_to_lineage_map)

    for slice_id in range(1, num_slices+1):
        log.debug("creating slice %s", slice_id)
        s_g = generate_random_complete_clusters_with_interconnect(num_clusters, num_nodes_cluster,
                                                                  density_interconnect, centroid_range_tuple,
                                                                  cluster_spread, interconnect_schedule[slice_id])

        label_nodes_with_lineage(slice_id, s_g,cluster_to_lineage_map)

        assign_to_slice(s_g,slice_id)
        slice_map[slice_id] = s_g

    log.debug("slice_map: %s", slice_map)

    # wire parents for slices after the initial slice
    for slice_id in range(2, num_slices+1):
        prev_id = slice_id - 1
        assign_random_parent_from_previous(slice_map[slice_id], slice_map[prev_id], num_clusters)

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

    centroid_tuple = (args.centroidmin, args.centroidmax)
    slicemap = generate_sequential_slices(args.slices,
                                          args.numclusters,
                                          args.nodespercluster,
                                          args.interconnectfraction,
                                          centroid_tuple,
                                          args.clusterspread)

    log.debug("slice map: %s", slicemap)

    # write slices as GML files
    basename = args.outputdirectory
    basename += "/"
    basename += args.modelid
    basename += "-"
    xyheader = "assemblage\teasting\tnorthing\n"
    xyrows = []

    for i in range(1, args.slices + 1):
        slice = slicemap[i]

        xyrows.extend(generate_xyrows_for_slice(slice))

        filename = basename
        filename += "-"
        filename += str(i).zfill(3)
        filename += ".gml"
        nx.write_gml(slice, filename)

    xybasename = args.outputdirectory
    xybasename += "/"
    xybasename += args.modelid
    xybasename += '-XY.txt'

    with open(xybasename, 'wb') as xyfile:
        xyfile.write(xyheader)
        for row in xyrows:
            xyfile.write(row)


