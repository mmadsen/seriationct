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
    python create_graphs.py --filename test --model grid-distance --slices 5 --x 20 --y 20 --tree complete
    python create_graphs.py --filename test --model grid-distance --slices 5 --x 20 --y 20 --tree minmax
"""

import networkx as nx
import argparse
import csv
import os
import logging as log
import operator
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pprint as pp
import random
import math
from random import choice
import itertools
import sys
import os


def setup():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", help="specify output file type (gml, vna, etc.). Default = gml. ", default="gml")
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--filename", help="filename for output", default="graph", required=True)
    parser.add_argument("--x", help="number of assemblages tall to generate", default=20)
    parser.add_argument("--y", help="number of assemblages wide to generate", default=20)
    parser.add_argument("--configuration", help="Path to configuration file")
    parser.add_argument("--slices", help="Number of graph slices to create", default=5)
    parser.add_argument("--model", choices=['grid-distance','grid-hierarchical', 'linear-distance','linear-hierarchical','branch'], required=True)
    parser.add_argument("--tree", help="Kind of tree to create", choices=['minmax','complete','mst'], default='complete')
    parser.add_argument("--graphs", help="create plots of networks", default=True)
    parser.add_argument("--graphshow", help="show plots in runtime.", default=True)
    parser.add_argument("--overlap",help="specify % of nodes to overlap from slice to slice. values are 0-1. For example. 0.5 for 50%", default=0.20)
    parser.add_argument("--movie", help="make a movie from png slices.", default=True)
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
    global nodeNames, nodeX, nodeY
    nodeNames=[]
    nodeX={}
    nodeY={}
    net = nx.Graph(name=args.model, is_directed=False)
    xcoord=0
    ycoord=0
    for yc in range(1,int(args.x)):
        for xc in range(1,int(args.y)):
            name="assemblage-"+str(xc)+"-"+str(yc)
            net.add_node(name,label=name,xcoord=xc, ycoord=yc)
            nodeNames.append(name)
            nodeX[name]=xc
            nodeY[name]=yc
    return net

def create_slices(graph):
    number_per_slice=int((int(args.x)*int(args.y))/int(args.slices))
    slices=[]
    ## first slice
    newnet = nx.Graph(name=args.model+"-1", is_directed=False)
    current_nodes=set()
    possible_nodes = set(graph.nodes())                             # set of all nodes that are possible
    for node in range(0,number_per_slice):   # select N number of nodes
        chosen_node = choice(list(possible_nodes))                  # pick a random node from the list of possibilities (all)
        possible_nodes.difference_update(chosen_node)               # remove the  node from the possible choices
        newnet.add_node(chosen_node,label=chosen_node,xcoord=nodeX[chosen_node], ycoord=nodeY[chosen_node]) # add node
        current_nodes.update(chosen_node)                           # update set of possible nodes
    slices.append(newnet)

    ## next n slices
    for ns in range(2,int(args.slices)+1):
        newnet.graph['name']=args.model+"-"+str(ns)
        # now we want to use a % of the nodes from the previous slice -- and remove the result. New ones drawn from the original pool.
        num_current_nodes=len(list(current_nodes))
        num_nodes_to_remove= int(float(num_current_nodes) * float(args.overlap))# nodes to remove
        for r in range(0,num_nodes_to_remove):
            chosen_node_to_remove = choice(newnet.nodes())
            #print "chosen node to remove: ", chosen_node_to_remove
            #print "newnet had ", len(newnet.nodes())
            newnet.remove_node(chosen_node_to_remove)
            possible_nodes.difference_update(chosen_node_to_remove)
            #print "now newnet has ", len(newnet.nodes())
            current_nodes.difference_update(chosen_node_to_remove)
        num_nodes_to_add = num_nodes_to_remove

        for r in range(0,num_nodes_to_add):
            chosen_node = choice(list(possible_nodes))
            possible_nodes.difference_update(chosen_node)
            newnet.add_node(chosen_node,label=chosen_node,xcoord=nodeX[chosen_node], ycoord=nodeY[chosen_node])
            #print "adding node: ", chosen_node
            current_nodes.update(chosen_node)
        ## now create a new graph
        updatedNet = nx.Graph(name=args.model+"-"+str(ns), is_directed=False)
        updatedNet.add_nodes_from(newnet.nodes(data=True)) ## copy just the nodes
        newnet = updatedNet.copy() ## copy back to newnet
        slices.append(newnet)  ## note these are just nodes, not edges yet. (next step)
    return slices

def save_slices(wired_slices):
    n=0
    for sl in wired_slices:
        n += 1
        nx.write_gml(sl, args.filename+"-"+str(n)+".gml")

def saveGraph(graph):
    nx.write_gml(graph, args.filename+".gml")

def wire_networks(slices):
    global edgeDistance
    edgeDistance={}
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
                    key1=from_node+"*"+neighbor
                    key2=neighbor+"*"+from_node
                    edgeDistance[key1]=distance
                    edgeDistance[key2]=distance
                    slice.add_edge(from_node,neighbor,name=key1,from_node=from_node,to_node=neighbor,distance=distance,weight=1/distance)

        #create the network the network
        if args.tree == 'mst':
            tree= nx.minimum_spanning_tree(slice,weight='distance')
        elif args.tree == 'complete':
            tree = createCompleteGraphByDistance(input_graph=slice,weight='distance')
        else:
            tree = createMinMaxGraphByWeight(input_graph=slice, weight='weight')

        wired_slices.append(tree)

    return wired_slices


def createCompleteGraphByDistance( **kwargs):
    graph=kwargs.get('input_graph')
    weight=kwargs.get('weight')
    nodes = graph.nodes()
    newnet = nx.Graph(is_directed=False)
    newnet.add_nodes_from(graph.nodes(data=True)) ## copy just the nodes
    edges=itertools.combinations(nodes,2)
    for e in edges:
        distance = calculate_distance(nodeX[e[0]],nodeY[e[0]],nodeX[e[1]],nodeY[e[1]] )
        key1=e[0]+"*"+e[1]
        key2=e[1]+"*"+e[0]
        newnet.add_edge(e[0],e[1],name=key1, from_node=e[0], to_node=e[1], distance=distance,weight=1/distance)
    return newnet

 # from a "summed" graph, create a "min max" solution - but use weights not counts
def createMinMaxGraphByWeight( **kwargs):
    ## first need to find the pairs with the maximum occurrence, then we work down from there until all of the
    ## nodes are included
    ## the weight
    weight = kwargs.get('weight', "weight")
    input_graph = kwargs.get('input_graph')

    output_graph = nx.Graph(is_directed=False)

    ## first add all of the nodes
    for name in input_graph.nodes():
        output_graph.add_node(name, name=name, label=name, xcoord=nodeX[name],ycoord=nodeY[name])

    pairsHash={}

    for e in input_graph.edges_iter():
        d = input_graph.get_edge_data(*e)
        fromAssemblage = e[0]
        toAssemblage = e[1]
        key = fromAssemblage+"*"+toAssemblage
        value = input_graph[fromAssemblage][toAssemblage]['weight']
        pairsHash[key]=value

    for key, value in sorted(pairsHash.iteritems(), key=operator.itemgetter(1), reverse=True ):
        ass1, ass2 = key.split("*")
        edgesToAdd={}
        if nx.has_path(output_graph, ass1, ass2) == False:
            edgesToAdd[key]=value
             ## check to see if any other pairs NOT already represented that have the same value
            for p in pairsHash:
                if pairsHash[p] == value:
                    k1,k2 = p.split("*")
                    if nx.has_path(output_graph, k1,k2) == False:
                        edgesToAdd[p]=pairsHash[p]
            ## now add all of the edges that are the same value if they dont already exist as paths
            for newEdge in edgesToAdd:
                a1,a2 = newEdge.split("*")
                key=a1+"*"+a2
                distance=edgeDistance[key]
                weight=1/distance
                if weight in [0,None,False]:
                    weight=0.000000000001
                output_graph.add_path([a1, a2], distance=distance, weight=weight)
    return output_graph

def calculate_distance(x1,y1,x2,y2):
    return math.sqrt((int(x1)-int(x2))**2 + (int(y1)-int(y2))**2)

def is_there_a_path(G, _from, _to):
    if nx.bidirectional_dijkstra(G,_from, _to):
        return True
    else:
        return False

def get_attribute_from_node(graph, nodename, attribute):
    listOfAttributes=nx.get_node_attributes(graph,attribute)
    return listOfAttributes[nodename]

def get_attribute_from_edge(graph, edgename, attribute):
    listOfAttributes=nx.get_get_attributes(graph,attribute)
    return listOfAttributes[edgename]

def create_movie():
    filename = args.filename+".mp4"
    slicename = args.filename + "Slice-%d.png"
    cmd = "ffmpeg -f image2 -r 1/5 -i " + slicename + " -vcodec mpeg4 -y "
    cmd += filename
    os.system(cmd)

def plot_slices(wired_slices):
    i=0
    for slice in wired_slices:

        pos={}
        for label in slice.nodes():
            x = get_attribute_from_node(slice,label,'xcoord')
            y = get_attribute_from_node(slice,label,'ycoord')
            pos[label]=(x,y)
        nx.draw_networkx(slice,pos,node_size=20,node_color='red', with_labels=False)
        title=args.filename + "Slice-"+str(i)
        plt.title(title)
        i+=1
        plt.savefig(title+".png", dpi=250)
        if args.graphshow == 1:
            plt.show()

if __name__ == "__main__":

    graph = setup()
    slices = create_slices(graph)
    wired_slices=wire_networks(slices)
    if args.graphs == True:
        plot_slices(wired_slices)
        if args.movie==True:
            create_movie()
    save_slices(wired_slices)
    '''
    R=wired_slices[0].copy()
    R.remove_nodes_from(n for n in wired_slices[0] if n in wired_slices[1])
    pos={}
    for label in R.nodes():
        x = get_attribute_from_node(R,label,'xcoord')
        y = get_attribute_from_node(R,label,'ycoord')
        pos[label]=(x,y)
    nx.draw_networkx(R,pos,node_size=20,node_color='red', with_labels=False)
    plt.show()
    '''






