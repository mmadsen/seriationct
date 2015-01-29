#!/usr/bin/env python
# Copyright (c) 2015.  Carl P. Lipo
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
A script to create the .gml files needed to establish the network structure for the ct simulations.
Takes some input information and produces a series of .gml files.

 Prototype:

 create_graphs.py --type gml --filename root_file_name  --number 25 --model grid

    for example:
    python create_graphs.py --filename test --model grid-distance --slices 5
"""

import networkx as nx
import argparse
import csv
import os
import logging as log
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pprint as pp
import random
import math
from random import choice

## setup

def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", help="specify output file type (gml, vna, etc.). Default = gml. ", default="gml")
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--filename", help="filename for output", default="graph", required=True)
    parser.add_argument("--x", help="number of assemblages tall to generate", default=20)
    parser.add_argument("--y", help="number of assemblages wide to generate", default=20)
    parser.add_argument("--configuration", help="Path to configuration file")
    parser.add_argument("--slices", help="Number of graph slices to create", default=5)
    parser.add_argument("--model", choices=['grid-distance','grid-hierarchical', 'linear-distance','linear-hierarchical','branch'], required=True)

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


    #### main program ####
    log.info("Creating graph with name root %s." %args.filename)
    graph = create_vertices()

    return graph


def create_vertices():
    net = nx.Graph(name=args.model, is_directed=False)
    xcoord=0
    ycoord=0
    for yc in range(1,int(args.x)):
        for xc in range(1,int(args.y)):
            name="assemblage-"+str(xc)+"-"+str(yc)
            net.add_node(name,label=name,xcoord=xc, ycoord=yc)
    return net

def create_slices(graph):
    nodes = graph.nodes()
    number_per_slice=int((int(args.x)*int(args.y))/int(args.slices))
    slices=[]
    possible_nodes = set(graph.nodes())
    for ns in range(0,int(args.slices)):
        slice = nodes[-1*number_per_slice:]
        newnet = nx.Graph(name=args.model+"-"+str(ns), is_directed=False)
        num=0
        possible_nodes = set(graph.nodes())
        for node in range(0,number_per_slice):
            chosen_node = choice(list(possible_nodes))                  # pick a random node
            possible_nodes = set(graph.nodes())
            possible_nodes.difference_update(chosen_node)    # remove the first node and all its neighbours from the candidates

            for n,d in graph.nodes_iter(data=True):
                if d['label']==chosen_node:
                    xcoord=d['xcoord']
                    ycoord=d['ycoord']
            newnet.add_node(chosen_node,label=chosen_node,xcoord=xcoord, ycoord=ycoord)

        slices.append(newnet)
    return slices

def save_slices(wired_slices):
    n=0
    for sl in wired_slices:
        n += 1
        nx.write_gml(sl, args.filename+"-"+str(n)+".gml")

def saveGraph(graph):
    nx.write_gml(graph, args.filename+".gml")

def wire_networks(slices):
    wired_slices=[]
    for slice in slices:
        for n,d in slice.nodes_iter(data=True):
            from_node = d['label']
            #from_node_id = d['id']
            x1=d['xcoord']
            y1=d['ycoord']
            mindistance=10000000000
            neighbor=from_node ## set this to be the same node initially
            ## now find the node that is closest
            for n1,d1 in slice.nodes_iter(data=True):
                testx=d1['xcoord']
                testy=d1['ycoord']

                distance=calculate_distance(x1,y1,testx,testy)
                if distance>0:  # and distance<=mindistance and is_there_a_path(slice,from_node,neighbor)==False:
                    neighbor=d1['label']
                    #mindistance=distance
                    slice.add_edge(from_node,neighbor,from_node=from_node,to_node=neighbor,distance=distance,weight=1/distance)

        min_spanning_tree= nx.minimum_spanning_tree(slice,weight='distance')
        wired_slices.append(min_spanning_tree)
    return wired_slices

def calculate_distance(x1,y1,x2,y2):
    return math.sqrt((int(x1)-int(x2))**2 + (int(y1)-int(y2))**2)

def is_there_a_path(G, _from, _to):
    if nx.bidirectional_dijkstra(G,_from, _to):
        return True
    else:
        return False

if __name__ == "__main__":
    graph = setup()
    slices = create_slices(graph)
    wired_slices=wire_networks(slices)
    save_slices(wired_slices)







