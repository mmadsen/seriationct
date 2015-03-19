#!/usr/bin/env python
# Copyright (c) 2015.  Carl P. Lipo and Mark E. Madsen
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
A script to create the .gml files needed to establish the network structure for the ct simulations.
Takes some input information and produces a series of .gml files.

 Prototype:

    for example:
    --filename test --model grid ---wiring minmax --slices 5
    --filename test --model grid --slices 5 --x 20 --y 20 --wiring complete
    --filename test --model grid --slices 5 --x 20 --y 20 --wiring random
    --filename test --model grid --slices 5  --wiring hierarchy

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
from itertools import chain
import matplotlib.figure


def setup():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", help="specify output file type (gml, vna, etc.). Default = gml. ", default="gml")
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--filename", help="filename for output", default="graph", required=True)
    parser.add_argument("--x", help="number of assemblages tall to generate", default=20)
    parser.add_argument("--y", help="number of assemblages wide to generate", default=20)
    parser.add_argument("--levels",help="number of levels in hierarchical model.", default=5)
    parser.add_argument("--children",help="number of children per level.",default=5)
    parser.add_argument("--configuration", help="Path to configuration file")
    parser.add_argument("--slices", help="Number of graph slices to create", default=5)
    parser.add_argument("--model", choices=['grid','linear','branch'], required=True, default="grid")
    parser.add_argument("--wiring", help="Kind of wiring to use in underlying model",
                        choices=['minmax','complete','mst','hierarchy','random'], default='complete')
    parser.add_argument("--graphs", help="create plots of networks", default=True)
    parser.add_argument("--graphshow", help="show plots in runtime.", default=True)
    parser.add_argument("--interconnect",help="the weight used for the child/gchild interconnect edges.", default=0.1)
    parser.add_argument("--gchild_interconnect", help="in the case of a heirarchical graph, what fraction of grandchildren are connected to each other (0-1.0) Default is 0.2", default=0.00)
    parser.add_argument("--child_interconnect", help="in the case of a heirarchical graph, what fraction of children are connected to each other (0-1.0) Default is 0.1", default=0.00)
    parser.add_argument("--overlap",
                        help="specify % of nodes to overlap from slice to slice. 0=No overlap, 1 = 100% overlap. Values must be between 0.0 and 1.0. For example. 0.5 for 50%", default=0.80)
    parser.add_argument("--movie", help="make a movie from png slices.", default=True)
    parser.add_argument("--density", help="the percentage of nodes used per slice. When 100% this means all possible nodes are used based on the grid size, overlap, and the number of slices. Must be >0%.", default=0.2)
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
    global nodeNames, nodeX, nodeY, spacefactor, nodeRoot, nodeChildren, nodeGrandchildren, number_per_slice
    nodeNames=[]
    nodeChildren=set()
    nodeX={}
    nodeY={}
    nodeGrandchildren={}
    spacefactor=1
    nodeRoot=""
    net = nx.Graph(name=args.model, is_directed=False)
    xcoord=0
    ycoord=0
    xyfile = open(args.filename+"XY.txt", 'w')
    xyfile.write("assemblage\teasting\tnorthing\n")
    if args.model=="grid":
        for yc in range(1,int(args.x)):
            for xc in range(1,int(args.y)):
                name="assemblage-"+str(xc)+"-"+str(yc)
                net.add_node(name,label=name,xcoord=xc, ycoord=yc,level=None,parent_node=None)
                nodeNames.append(name)
                nodeX[name]=xc
                nodeY[name]=yc
                xyfile.write(name+"\t"+str(xc)+"\t"+str(yc)+"\n")
        xyfile.close()
    else:
        print "Please choose a model for the vertices. Default is grid. Others are currently unimplemented."
    # 100% overlap = no change in # of nodes so can use ALL possible nodes (X*Y)
    # 0% overlap = complete change in nodes every slice so can only have X*Y/num_slices
    if float(args.overlap)>= 1.0:
        number_per_slice= int(int(args.x)*int(args.y)*float(args.density))
    else:
        number_per_slice = int(float(args.density)*(int(args.x)*int(args.y)/(int(args.slices)+1)*(1-float(args.overlap))))

    return net


def create_slices(graph):
    if args.wiring in ["hierarchy", "minmax", "complete"]:
        slices = create_slices_hierarchy(graph)
    else:
        slices= create_slices_random(graph)

    return slices

def create_slices_hierarchy(graph):
    global nodeRoot, nodeChildren, nodeGrandchildren, number_per_slice

    slices=[]
    ## first slice
    newnet = nx.Graph(name=args.model+"-1", is_directed=False)
    current_nodes=set([])
    possible_nodes = set(list(graph.nodes()))
    possible_nodes.difference_update([nodeRoot])# remove Root from nodes that can change

    for node in range(0,number_per_slice):   # select N number of nodes
        list_of_nodes = list(possible_nodes)
        #print list_of_nodes
        random_selection =random.randint(1,len(list_of_nodes))
        try:
            chosen_node = list_of_nodes[random_selection]       # pick a random node from the list of possibilities (all)
            possible_nodes.difference_update([chosen_node])     # remove the  node from the possible choices
            newnet.add_node(chosen_node,label=chosen_node,
                            xcoord=nodeX[chosen_node],
                            ycoord=nodeY[chosen_node],
                            level=None,
                            parent_node="initial") # add node
            current_nodes.update([chosen_node])
        except:
            pass# update set of possible nodes

    if args.wiring=="hierarchy":
        hierarchy_net = create_hierarchy_in_graph(newnet)
        wired_net=wire_networks(hierarchy_net)
    else:
        wired_net=wire_networks(newnet)

    slices.append(wired_net.copy())

    ## we are going to use this copy of the graph to iteratively modify
    nextNet = nx.Graph(is_directed=False)
    nextNet.add_nodes_from(wired_net.nodes(data=True)) ## copy just the nodes

    # now we want to use a % of the nodes from the previous slice -- and remove the result. New ones drawn from the original pool.
    num_current_nodes=len(list(current_nodes))

    ## based on the total number of nodes remaining (after the previous slice), divide up how many can be in each slice by the # of slices
    ## note this means that the MAX change with full replacement will use up all the nodes.

    #num_nodes_to_remove= int(float(num_current_nodes) * (1-float(args.overlap)))-(int(float(args.slices)))# nodes to remove

    num_nodes_to_remove= int(float(num_current_nodes) * (1-float(args.overlap)))# nodes to remove

    ## now create T+1, T+2, ... T+args.slices slices
    for ns in range(1,int(args.slices)):

        possible_parent_nodes = set(nextNet.nodes()) ## this list of possible parents
                                                     ## (any from previous slice)

        ## remove 1 node at a time
        for r in range(0,num_nodes_to_remove):

            ## pick a node to remove from existing nodes in graph
            chosen_node_to_remove = choice(nextNet.nodes())

            ## now add the node and deal with child/gchild lists
            ## if this is a child, we need to know what grandchildren need a new parent...
            if nextNet.node[chosen_node_to_remove]['level'] =="child":
                nodeChildren.difference_update([chosen_node_to_remove])
                listOfAbandonedGchildren=nodeGrandchildren[chosen_node_to_remove]
                new_node_to_add = choice(list(possible_nodes))
                possible_nodes.update([new_node_to_add])
                ## set this node as the parent of the grandchildren...
                nodeGrandchildren[new_node_to_add]=listOfAbandonedGchildren
                nodeChildren.update([new_node_to_add])
                ##parent_node = choice(nextNet.nodes())
                nextNet.add_node(new_node_to_add,
                            label=new_node_to_add,
                            xcoord=nodeX[new_node_to_add],
                            ycoord=nodeY[new_node_to_add],level="child")
                            #parent_node=parent_node )
                current_nodes.update([new_node_to_add])
            elif nextNet.node[chosen_node_to_remove]['level']=="grandchild":
                new_node_to_add = choice(list(possible_nodes))
                possible_nodes.difference_update([new_node_to_add])
                current_nodes.update([new_node_to_add])
                ##parent_node = choice(nextNet.nodes())
                nextNet.add_node(new_node_to_add,
                            label=new_node_to_add,
                            xcoord=nodeX[new_node_to_add],
                            ycoord=nodeY[new_node_to_add],level="grandchild")
                            #parent_node=parent_node )
                current_nodes.update([new_node_to_add])

                for key in nodeGrandchildren.iterkeys():
                    setOfGrandchildrenForChild=set(nodeGrandchildren[key])
                    if chosen_node_to_remove in nodeGrandchildren[key]:
                        setOfGrandchildrenForChild.difference_update([chosen_node_to_remove])
                        nodeGrandchildren[key]=list(setOfGrandchildrenForChild)
                        nodeGrandchildren[key].append(new_node_to_add)
            else:  ### minmax case since nothing will be in the children/grandchildren lists.
                chosen_node = choice(list(possible_nodes)) ## choose a node from the possible nodes to choose from (i.e., those not already added or deleted)
                possible_nodes.difference_update([chosen_node]) ## remove this from possible choices
                ##parent_node = choice(nextNet.nodes())
                nextNet.add_node(chosen_node,
                            label=chosen_node,
                            xcoord=nodeX[chosen_node],
                            ycoord=nodeY[chosen_node],level="ooops")
                            #parent_node=parent_node )
                current_nodes.update([chosen_node])  ## maintain the list of what's currently listed in the nodes

            ## remove node from net
            nextNet.remove_node(chosen_node_to_remove)

            ## remove from list of possible nodes to add
            possible_nodes.difference_update([chosen_node_to_remove])

            ## remove from list of nodes that are currently linked
            current_nodes.difference_update([chosen_node_to_remove])

            ## remove from list of parents
            possible_parent_nodes.difference_update([chosen_node_to_remove])

        ## now wire the network
        wired_net = wire_networks(nextNet)
        for unlinked_node in nx.isolates(wired_net):
            wired_net.remove_node(unlinked_node)

        parents = nx.get_node_attributes(wired_net, 'parent_node')
        for n in wired_net.nodes():
            try:
                test=parents[n];
            except:
                temp_set = possible_parent_nodes    ## temporary set
                temp_set.difference_update([n])     ## remove this from options (cant be own parent)
                wired_net.node[n]['parent_node']=choice(list(temp_set))

        check_parent_nodes(wired_net)

        slices.append(wired_net.copy())  ## note these are just nodes, not edges yet. (next step)


    return slices

def check_parent_nodes(graph):

    for n in graph.nodes():

        parent_node = graph.node[n]["parent_node"]
        if parent_node is not "initial" and parent_node not in graph.nodes():
            print "parent_node is set to ", parent_node, " but parent_node is not currently a node."

def create_slices_random(graph):
    global number_per_slice
    slices=[]
    ## first slice
    newnet = nx.Graph(name=args.model+"-1", is_directed=False)
    current_nodes=set([])
    possible_nodes = set(list(graph.nodes()))
    possible_nodes.difference_update([nodeRoot])# remove Root from nodes that can change

    for node in range(0,number_per_slice):   # select N number of nodes
        list_of_nodes = list(possible_nodes)
        #print list_of_nodes

        random_selection =random.randint(1,len(list_of_nodes))
        try:
            chosen_node = list_of_nodes[random_selection]  # pick a random node from the list of possibilities (all)

            possible_nodes.difference_update([chosen_node])     # remove the  node from the possible choices
            newnet.add_node(chosen_node,label=chosen_node,
                            xcoord=nodeX[chosen_node],
                            ycoord=nodeY[chosen_node],
                            parent_node="initial",level=None) # add node
            current_nodes.update([chosen_node])
        except:
            pass# update set of possible nodes

    wired_net=wire_networks(newnet)
    print "first slice!"
    plot_slice(wired_net)
    slices.append(wired_net)

    for ns in range(1,int(args.slices)):
        slices.append(newnet.copy())
        nodes_to_delete=[]
        slices[ns].graph['name']=args.model+"-"+str(ns+1)
        # now we want to use a % of the nodes from the previous slice -- and remove the result. New ones drawn from the original pool.
        num_current_nodes=len(list(current_nodes))
        num_nodes_to_remove= int(float(num_current_nodes) * (1-float(args.overlap)))# nodes to remove

        for r in range(0,num_nodes_to_remove):
            chosen_node_to_remove = choice(newnet.nodes())
            possible_parent_nodes = set(newnet.nodes()) ## this list of possible parents is going to have all
                 ##  the old nodes minus the ones that are removed (but no new ones)
            nodes_to_delete.append(chosen_node_to_remove)
            possible_nodes.difference_update([chosen_node_to_remove])
            current_nodes.difference_update([chosen_node_to_remove])
        num_nodes_to_add = num_nodes_to_remove

        for r in range(0,num_nodes_to_add):
            chosen_node = choice(list(possible_nodes))
            possible_nodes.difference_update(chosen_node)

            temp_set = possible_parent_nodes
            temp_set.difference_update([chosen_node])
            slices[ns].add_node(chosen_node,label=chosen_node,
                                xcoord=nodeX[chosen_node],
                                ycoord=nodeY[chosen_node],
                                parent_node=choice(list(temp_set)) )
            ## we need to link the new node back into the edges that already existed
            old_node=nodes_to_delete[r]
            edges=slices[ns].edges(old_node)
            for fnode,tnode in edges:
                key1=chosen_node+"*"+tnode
                weight=random.random()
                distance=calculate_distance(nodeX[chosen_node],
                                            nodeY[chosen_node],
                                            nodeX[tnode],
                                            nodeY[tnode])
                slices[ns].add_edge(chosen_node, tnode,name=key1,
                        unnormalized_weight=weight,
                        from_node=chosen_node,
                        to_node=tnode,
                        distance=distance,
                        weight=weight)
            try:
                slices[ns].remove_node(old_node)
            except:
                pass
            current_nodes.update([chosen_node])
    return slices


def save_slices(wired_slices):
    n=0
    for sl in wired_slices:
        n += 1
        nx.write_gml(sl, args.filename+"-"+str(n)+".gml")

def saveGraph(graph):
    nx.write_gml(graph, args.filename+".gml")

def calc_sum_distance(slice):
    global nodeX, nodeY
    sumDistance = 0
    for n in slice.nodes():
            x1=nodeX[n]
            y1=nodeY[n]
            for n1 in slice.nodes():
                testx=nodeX[n1]
                testy=nodeY[n1]
                distance=calculate_distance(x1,y1,testx,testy)
                if distance>0:
                    sumDistance += distance
    return sumDistance/2 # since the distances are measured both ways, the actual sum distance is half the total



def wire_networks(slice):
    global edgeDistance
    edgeDistance={}

    #create the network
    if args.wiring == 'mst':
        tree= nx.minimum_spanning_tree(slice,weight='distance')
    elif args.wiring == 'random':
        tree = createRandomGraph(input_graph=slice)
    elif args.wiring == 'complete':
        tree = createCompleteGraphByDistance(input_graph=slice,weight='distance')
    elif args.wiring == "hierarchy":
        tree= wire_hierarchy(slice)
    elif args.wiring == "minmax":
        tree = createMinMaxGraphByWeight(input_graph=slice, weight='weight')
    else:
        ## use minmax as default
        tree = createMinMaxGraphByWeight(input_graph=slice, weight='weight')

    return tree

def createRandomGraph(**kwargs):
    global nodeX, nodeY
    graph=kwargs.get('input_graph')

    nodes = graph.nodes()

    ## list of nodes that are already linked with edges
    nodes_linked=set([])

    ## the set of nodes from which to choose
    possible_nodes=set(nodes)

    ## pick a random node to start
    first_node = choice(nodes)

    ## remove this from the possible nodes
    possible_nodes.difference_update([first_node])

    ## now add this node to the links of nodes to link
    nodes_linked.update([first_node])

    ## now a random other node to link to the first (to create the basic link structure)
    second_node = choice(list(possible_nodes))

    sumDistance=calc_sum_distance(graph)
    key1=first_node+"*"+second_node
    distance=calculate_distance(nodeX[first_node],nodeY[first_node],nodeX[second_node],nodeY[second_node])
    weight=random.random()
    graph.add_edge(first_node,second_node,name=key1,
            normalized=weight/sumDistance,
            unnormalized_weight=weight,
            from_node=first_node, to_node=second_node, distance=distance,weight=weight)

    ## remove this from the possible nodes
    possible_nodes.difference_update([second_node])

    for n in range(0,len(nodes)-2):
        ## choose a random node from ones that are not yet linked
        chosen_node_to_add = choice(list(possible_nodes))

        ## remove this node from the list of possible nodes to link
        possible_nodes.difference_update([chosen_node_to_add])

        ## choose a place to link this node -- node the nodes to link should only be those that are already linked
        list_of_nodes=map(list,graph.edges())
        unconnected = False
        chosen_node_to_link=choice(list(chain.from_iterable(list_of_nodes)))
        while unconnected == False:
            num_nodes_connected = nx.node_connected_component(graph,chosen_node_to_link)
            if len(num_nodes_connected)>1:
                unconnected= True
                break

        ## create a simple key for the edge
        key1=chosen_node_to_add+"*"+chosen_node_to_link

        ## random weight 0-1
        weight=random.random()

        ## calculate distance between the nodes
        distance=calculate_distance(nodeX[chosen_node_to_add],nodeY[chosen_node_to_add],nodeX[chosen_node_to_link],nodeY[chosen_node_to_link])

        ## add edge
        graph.add_edge(chosen_node_to_link,chosen_node_to_add,name=key1,
                        normalized=weight/sumDistance,
                        unnormalized_weight=weight,
                        from_node=chosen_node_to_add, to_node=chosen_node_to_link, distance=distance,weight=weight)


        ## now add the link that was added to the already linked node
        nodes_linked.update([chosen_node_to_add])
        #plot_slice(graph)
    return graph


def create_hierarchy_in_graph(graph):
    global spacefactor, nodeRoot, nodeChildren, nodeGrandchildren
    # first find a random node to be the root
    nodes = graph.nodes()
    nodeRoot = random.choice(nodes)
    graph.node[nodeRoot]['level']="root"
    possible_nodes = set(nodes)
    possible_nodes.difference_update([nodeRoot])
    linked_nodes=set([])
    ## now find a random set of children
    for n in range(0,int(args.children)):
        random_child=random.choice(list(possible_nodes))
        possible_nodes.difference_update([random_child])
        nodeChildren.update([random_child])
        linked_nodes.update([random_child])
        graph.node[random_child]['level']="child"
    # now link grandchildren to children

    for n in list(nodeChildren):
        nodeGrandchildren[n]=[]
        for m in range(0,int(args.children)):
            random_gchild=random.choice(list(possible_nodes))
            possible_nodes.difference_update([random_gchild])
            nodeGrandchildren[n].append(random_gchild)
            linked_nodes.update([random_gchild])
            graph.node[random_gchild]['level']="grandchild"

    ## filter nodes that are not part of hierarchy...
    for node in graph.nodes():
        if graph.node[node]['level']==None:
            graph.remove_node(node)

    return graph

def all_pairs(lst):
    return list((itertools.permutations(lst, 2)))

def wire_hierarchy(graph):
    global spacefactor, nodeRoot, nodeChildren, nodeGrandchildren, nodeX, nodeY

    output_graph = nx.Graph(is_directed=False)
    output_graph.add_nodes_from(graph.nodes(data=True)) ## copy just the nodes

    sumDistance=calc_sum_distance(graph)
    list_of_grandchildren=[]
    ##  wire to root
    for node in list(nodeChildren):
        key1=nodeRoot+"*"+node
        weight=1
        xcoord = nodeX[node]
        ycoord = nodeY[node]
        rootX = nodeX[nodeRoot]
        rootY = nodeY[nodeRoot]
        distance=calculate_distance(xcoord,ycoord,rootX,rootY)
        output_graph.add_edge(nodeRoot, node,name=key1,
                normalized=weight/sumDistance,
                unnormalized_weight=weight,
                from_node=nodeRoot, to_node=node, distance=distance,weight=weight)

        ## now find the grandchildren and wire to children
        for gnode in nodeGrandchildren[node]:
            list_of_grandchildren.append(gnode)
            key1=node+"*"+gnode
            weight=1.0
            xcoord = nodeX[node]
            ycoord = nodeY[node]
            gnodeX = nodeX[gnode]
            gnodeY = nodeY[gnode]

            distance=calculate_distance(xcoord,ycoord,gnodeX,gnodeY)
            output_graph.add_edge(node, gnode,name=key1,
                normalized=float(weight)/float(sumDistance),
                unnormalized_weight=weight,
                from_node=node, to_node=gnode, distance=distance,weight=weight)

    # wire % of the children together at low weight
    pairs = all_pairs(list(nodeChildren))
    for n in range(0,int(len(pairs)*float(args.child_interconnect))):
        random_pair = random.choice(pairs)
        chosen_child=random_pair[0]
        link_child=random_pair[1]
        distance=calculate_distance(nodeX[chosen_child],nodeY[chosen_child],nodeX[link_child],nodeY[link_child])
        key1=chosen_child+"*"+link_child
        weight=float(args.interconnect)
        output_graph.add_edge(chosen_child, link_child,name=key1,
                        normalized=weight/sumDistance,
                        unnormalized_weight=weight,
                        from_node=chosen_child,
                        to_node=link_child, distance=distance,weight=weight)

    ## wire some fraction of the grandchildren together
    pairs = all_pairs(list_of_grandchildren)
    # wire some % of those grand children to each other at low connectivity
    for n in range(0,int(len(pairs)*float(args.gchild_interconnect))):
        random_pair = random.choice(pairs)
        chosen_gchild=random_pair[0]
        link_gchild=random_pair[1]
        distance=calculate_distance(nodeX[chosen_gchild],nodeY[chosen_gchild],nodeX[link_gchild],nodeY[link_gchild])
        key1=chosen_gchild+"*"+link_gchild
        weight=float(args.interconnect)
        output_graph.add_edge(chosen_gchild, link_gchild,name=key1,
                        normalized=weight/sumDistance,
                        unnormalized_weight=weight,
                        from_node=chosen_gchild, to_node=link_gchild,
                        distance=distance,weight=weight)
    return output_graph


def createCompleteGraphByDistance( **kwargs ):
    global edgeDistance
    graph=kwargs.get('input_graph')
    weight=kwargs.get('weight')
    nodes = graph.nodes()
    newnet = nx.Graph(is_directed=False)
    newnet.add_nodes_from(graph.nodes(data=True)) ## copy just the nodes
    edges=itertools.combinations(nodes,2)
    sumDistance=calc_sum_distance(graph)

    for e in edges:
        distance = calculate_distance(nodeX[e[0]],nodeY[e[0]],nodeX[e[1]],nodeY[e[1]] )
        key1=e[0]+"*"+e[1]
        key2=e[1]+"*"+e[0]
        edgeDistance[key1]=distance
        edgeDistance[key2]=distance
        normalized_weight = distance/sumDistance
        newnet.add_edge(e[0],e[1],name=key1,
                        normalized_weight=normalized_weight,
                        unnormalized_weight=1/distance,
                        from_node=e[0], to_node=e[1], distance=distance,weight=1/distance)
    return newnet

 # from a "summed" graph, create a "min max" solution - but use weights not counts
def createMinMaxGraphByWeight( **kwargs):
    ## first need to find the pairs with the maximum occurrence, then we work down from there until all of the
    ## nodes are included
    ## the weight

    weight = kwargs.get('weight', "weight")
    input_graph = kwargs.get('input_graph')
    sumDistance = calc_sum_distance(input_graph)

    #first create a graph that is complete
    new_graph = createCompleteGraphByDistance(input_graph=input_graph, weight='weight')

    output_graph = nx.Graph(is_directed=False)
    output_graph.add_nodes_from(input_graph.nodes(data=True)) ## copy just the nodes

    pairsHash={}

    for e in new_graph.edges_iter():
        d = new_graph.get_edge_data(*e)
        fromAssemblage = e[0]
        toAssemblage = e[1]
        key = fromAssemblage+"*"+toAssemblage
        value = new_graph[fromAssemblage][toAssemblage]['weight']
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
                normalized_weight=distance/sumDistance
                if weight in [0,None,False]:
                    weight=0.000000000001 ## use this value so that we never get a 1/0
                output_graph.add_path([a1, a2], normalized_weight=normalized_weight,unnormalized_weight=weight,
                                      distance=distance, weight=weight)
    ## now remove all of the non linked nodes.
    outdeg = output_graph.degree()
    to_remove = [n for n in outdeg if outdeg[n] < 1]
    input_graph.remove_nodes_from(to_remove)
    return output_graph

def calculate_distance(x1,y1,x2,y2):
    return math.sqrt((int(x1)-int(x2))**2 + (int(y1)-int(y2))**2)

def is_there_a_path(G, _from, _to):
    if nx.bidirectional_dijkstra(G,_from, _to):
        return True
    else:
        return False

def get_attribute_from_node( nodename, attribute):
    global graph
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

def plot_slice(slice):
    i=0
    pos={}
    for label in slice.nodes():
        x = get_attribute_from_node(label,'xcoord')
        y = get_attribute_from_node(label,'ycoord')
        pos[label]=(x,y)

    nx.draw_networkx(slice,pos,node_size=20,node_color='red', with_labels=False )
    title=args.filename + "Slice-"+str(i)
    plt.title(title)
    plt.axis('equal')
    i+=1
    if args.graphshow == 1:
        plt.show()

def plot_slices(wired_slices):
    i=0
    for slice in wired_slices:
        figsize=(int(args.x),int(args.y))
        fig = matplotlib.figure.Figure(figsize=figsize)
        ax = fig.add_subplot(aspect='equal')
        pos={}
        for label in slice.nodes():
            x = get_attribute_from_node(label,'xcoord')
            y = get_attribute_from_node(label,'ycoord')
            pos[label]=(y,x)
        nx.draw_networkx(slice,pos,node_size=20,node_color='red', with_labels=False, ax=ax)
        title=args.filename + "Slice-"+str(i)
        plt.title(title)
        plt.axis('equal')
        i+=1
        plt.savefig(title+".png", dpi=250)
        if args.graphshow == 1:
            plt.show()

if __name__ == "__main__":

    graph = setup()
    slices = create_slices(graph)
    if args.graphs == True:
        plot_slices(slices)
        if args.movie==True:
            create_movie()
    save_slices(slices)
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






