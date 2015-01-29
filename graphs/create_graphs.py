#!/usr/bin/env python
# Copyright (c) 2015.  Carl P. Lipo
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
A script to create the .gml files needed to establish the network structure for the ct simulations.
Takes some input information and produces a series of .gml files.

 Prototype:

 create_graphs.py --type gml --filename root_file_name  --number 25 --model grid

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
from sklearn.neighbors import NearestNeighbors

## setup

def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", help="specify output file type (gml, vna, etc.). Default = gml. ", default="gml")
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--filename", help="filename for output", default="graph", required=True)
    parser.add_argument("--x", help="number of assemblages tall to generate", default=10)
    parser.add_argument("--y", help="number of assemblages wide to generate", default=10)
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
    for x in range(1,int(args.x)):
        for y in range(1,int(args.y)):
            name="assemblage-"+str(x)+"/"+str(y)
            net.add_node(name,label=name,xcoord=xcoord, ycoord=ycoord)
            if x>0 and x%args.x<>0:
                xcoord += args.x
            if y>0 and y%args.y==0:
                ycoord += args.y
                xcoord = 0
    return net

def create_slices(graph):
    nodes = graph.nodes()
    number_per_slice=int((args.x*args.y)/args.slices)
    slices=[]
    print nodes
    for ns in range(0,args.slices):
        slice = nodes[-1*number_per_slice:]
        newnet = nx.Graph(name=args.model+"-"+str(ns), is_directed=False)
        num=0
        for node in range(0,number_per_slice):
            for n,d in graph.nodes_iter(data=True):
                if d['label']==nodes[node]:
                    newnet.add_node(d['label'],label=d['label'],xcoord=d['xcoord'], ycoord=d['ycoord'])
                    graph.remove_node(d['label'])
        slices.append(newnet)
    return slices

def save_slices(slices):
    n=0
    for sl in slices:
        n += 1
        nx.write_gml(graph, args.filename+"-"+str(n)+".gml")

def saveGraph(graph):
    nx.write_gml(graph, args.filename+".gml")

def sample_gen(n, forbid):
    state = dict()
    track = dict()
    for (i, o) in enumerate(forbid):
        x = track.get(o, o)
        t = state.get(n-i-1, n-i-1)
        state[x] = t
        track[t] = x
        state.pop(n-i-1, None)
        track.pop(o, None)
    del track
    for remaining in xrange(n-len(forbid), 0, -1):
        i = random.randrange(remaining)
        yield state.get(i, i)
        state[i] = state.get(remaining - 1, remaining - 1)
        state.pop(remaining - 1, None)

if __name__ == "__main__":
    graph = setup()
    slices = create_slices(graph)
    save_slices(slices)







