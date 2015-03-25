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
import matplotlib
matplotlib.use('Agg')
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
    parser.add_argument("--children",help="number of children per level.",default=3)
    parser.add_argument("--grandchildren",help="number of grandchildren per level.", default=3)
    parser.add_argument("--configuration", help="Path to configuration file")
    parser.add_argument("--slices", help="Number of graph slices to create", default=5)
    parser.add_argument("--model", choices=['grid','linear','branch'], required=True, default="grid")
    parser.add_argument("--wiring", help="Kind of wiring to use in underlying model",
                        choices=['minmax','complete','mst','hierarchy','random'], default='complete')
    parser.add_argument("--graphs", help="create plots of networks", default=True)
    parser.add_argument("--graphshow", help="show plots in runtime.", default=True)
    parser.add_argument("--child_interconnect_weight",help="the weight used for the child interconnect edges.", default=0.1)
    parser.add_argument("--gchild_interconnect_weight",help="the weight used for the gchild interconnect edges.", default=0.1)
    parser.add_argument("--gchild_interconnect_percentage", help="in the case of a hierarchical graph, what fraction of grandchildren are connected to each other (0-1.0) Default is 0.2", default=0.00)
    parser.add_argument("--child_interconnect_percentage", help="in the case of a hierarchical graph, what fraction of children are connected to each other (0-1.0) Default is 0.1", default=0.00)
    parser.add_argument("--root_child_weight", help="the weight used for edges between root/child nodes",type=float, default=1.0)
    parser.add_argument("--child_gchild_weight", help="the weight used for edges between child/gchild nodes",type=float, default=1.0)
    parser.add_argument("--overlap",
                        help="specify % of nodes to overlap from slice to slice. 0=No overlap, 1 = 100% overlap. Values must be between 0.0 and 1.0. For example. 0.5 for 50%", default=0.80)
    parser.add_argument("--movie", help="make a movie from png slices.", default=True)
    parser.add_argument("--root_swap_probability", help="probability of the root being swapped in any slice. Default is 0.2", default=0.2)
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
                net.add_node(name,label=name,
                             xcoord=xc, ycoord=yc,
                             level=None,parent_node=None,
                             child_of=None,
                             appears_in_slice=None)
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
    if args.wiring == "hierarchy":
        slices = create_slices_hierarchy(graph)
    elif args.wiring == "random":
        slices = create_slices_random(graph)
    else:
        slices = create_slices_minmax(graph)

    return slices

def create_slices_hierarchy(graph):
    global nodeRoot, nodeChildren, nodeGrandchildren, number_per_slice

    slices=[]
    ## first slice
    newnet = nx.Graph(name=args.model+"-1", is_directed=False)
    current_nodes=set([])
    possible_nodes = set(list(graph.nodes()))
    possible_nodes.difference_update([nodeRoot])# remove Root from nodes that can change
    print "now on slice:  1"
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
                            parent_node=None,
                            child_of=None,
                            appears_in_slice=1) # add node
            current_nodes.update([chosen_node])
        except:
            pass# update set of possible nodes

    ## create the hiearchy
    hierarchy_net = create_hierarchy_in_graph(newnet)
    wired_net= wire_hierarchy(hierarchy_net)

    ## first slice created
    slices.append(wired_net.copy())

    ## we are going to use this copy of the graph to iteratively modify
    nextNet = nx.Graph(is_directed=False)
    nextNet.add_nodes_from(wired_net.nodes(data=True)) ## copy just the nodes

    # now we want to use a % of the nodes from the previous slice -- and remove the result. New ones drawn from the original pool.
    num_current_nodes=len(nextNet.nodes())

    ## based on the total number of nodes remaining (after the previous slice), divide up how many can be in each slice by the # of slices
    ## note this means that the MAX change with full replacement will use up all the nodes.

    num_nodes_to_remove= int(float(num_current_nodes) * (1-float(args.overlap)))# nodes to remove
    valid_parent_list=set()
    valid_parent_list.update(['i_am_root'])
    valid_parent_list.update([nodeRoot])
    ## now create T+1, T+2, ... T+args.slices slices
    for ns in range(2,int(args.slices)+1):
        print "now on slice: ", ns
        child_nodes_from_previous_slice = list(nodeChildren)
        #print "these are the child nodes from the previous slice: ", child_nodes_from_previous_slice

        ## check to see if root is going to be swapped this slice or not based on a fixed probability

        check_for_root_swap=random.random()
        if check_for_root_swap < float(args.root_swap_probability):
                # find a new node to be root
                old_root = nodeRoot  ## temporarily keep the old_root
                new_root = choice(list(possible_nodes))  ## get any valid node that is unchosen
                possible_nodes.difference_update([new_root]) ## get rid of this node from pool of choices
                valid_parent_list.update([old_root])  ## place the node into the list of nodes that can be parents
                valid_parent_list.update([new_root])   ## place the new node into the list of nodes that can be parents
                nextNet.add_node(new_root,
                                label=new_root,
                                xcoord=nodeX[new_root],
                                ycoord=nodeY[new_root],
                                level="root",
                                child_of=old_root,
                                parent_node=old_root,
                                appears_in_slice=ns)
                nodeRoot=new_root
                current_nodes.update([new_root])            ## add to current _nodes
                current_nodes.difference_update([old_root])  ## remove from current nodes
                print "swapping root ", old_root, " for new root: ", new_root

        ## create a set for choosing  nodes to remove from graph (w/root as a choice)
        nodes_from_which_i_can_choose_without_root=set(nextNet.nodes())
        nodes_from_which_i_can_choose_without_root.difference_update([nodeRoot])

        ## remove 1 node at a time
        #print "slice #: ", ns, "now going to remove ", num_nodes_to_remove, " nodes out of a graph of ", len(nextNet.nodes()), " nodes"
        for r in range(0,int(num_nodes_to_remove)):
            chosen_node_to_remove = choice(list(nodes_from_which_i_can_choose_without_root))
            ## should only choose root *once* per slice (not over and over)
            original_child_of_value=nextNet.node[chosen_node_to_remove]['child_of']
            nodes_from_which_i_can_choose_without_root.difference_update([chosen_node_to_remove])
            ## now add the node and deal with child/gchild lists
            ## if this is a child, we need to know what grandchildren need a new parent...
            if chosen_node_to_remove == nodeRoot:
                print "ruh roh! root shouldnt be on this list!!"
                exit()  ## this should *NEVER* be the case

            else:
                if nextNet.node[chosen_node_to_remove]['level'] == "child":
                    nodeChildren.difference_update([chosen_node_to_remove])

                    listOfAbandonedGchildren=nodeGrandchildren[chosen_node_to_remove]
                    new_node_to_add = choice(list(possible_nodes))

                    possible_nodes.update([new_node_to_add])

                    ## set this node as the parent of the grandchildren...
                    nodeGrandchildren[new_node_to_add]=listOfAbandonedGchildren
                    nodeChildren.update([new_node_to_add])

                    ## new children will always have a parent of root
                    nextNet.add_node(new_node_to_add,
                                label=new_node_to_add,
                                xcoord=nodeX[new_node_to_add],
                                ycoord=nodeY[new_node_to_add],
                                level="child",
                                child_of=nodeRoot,
                                parent_node=nodeRoot,
                                appears_in_slice=ns)
                    #print "adding child node: ", new_node_to_add
                    current_nodes.update([new_node_to_add])
                    current_nodes.difference_update([chosen_node_to_remove])

                else:  ## must be grandkid
                    new_node_to_add = choice(list(possible_nodes))
                    possible_nodes.difference_update([new_node_to_add])
                    current_nodes.update([new_node_to_add])
                    ##parent_node = choice(nextNet.nodes())

                    #new grandchildren will have a parent from one of the children (not gchild)# .
                    #print "adding new grandchild: ", new_node_to_add
                    new_parent = random.choice(child_nodes_from_previous_slice)
                    #print "this will have parent_node: ", new_parent
                    nextNet.add_node(new_node_to_add,
                                label=new_node_to_add,
                                xcoord=nodeX[new_node_to_add],
                                ycoord=nodeY[new_node_to_add],
                                level="grandchild",
                                child_of=original_child_of_value,
                                parent_node=new_parent,
                                appears_in_slice=ns)

                    current_nodes.update([new_node_to_add])
                    # now need to put this new node in the
                    for key in nodeGrandchildren.iterkeys():
                        setOfGrandchildrenForChild=set(nodeGrandchildren[key])
                        if chosen_node_to_remove in nodeGrandchildren[key]:
                            setOfGrandchildrenForChild.difference_update([chosen_node_to_remove])
                            ## set the list w/o this node
                            nodeGrandchildren[key]=list(setOfGrandchildrenForChild)
                            ## add this node to the other list
                            nodeGrandchildren[new_parent].append(new_node_to_add)
                ## remove node from net
                nextNet.remove_node(chosen_node_to_remove)

                ## remove from list of possible nodes to add
                possible_nodes.difference_update([chosen_node_to_remove])

                ## remove from list of nodes that are currently linked
                current_nodes.difference_update([chosen_node_to_remove])

        ## now wire the network
        wired_net = wire_hierarchy(nextNet)
        for unlinked_node in nx.isolates(wired_net):
            wired_net.remove_node(unlinked_node)

        #print "checking nodes... (3)"


        valid_parent_list.update(set(child_nodes_from_previous_slice))

        for n in wired_net.nodes():
            if wired_net.node[n]['level'] is None or wired_net.node[n]['xcoord'] is None:
                print "problem with node ", n, " somehow added without data"
                exit

            if wired_net.node[n]['parent_node'] not in list(valid_parent_list):
                print "on slice: ", ns
                print "child nodes from previous slice: ", child_nodes_from_previous_slice
                print "problem with node: ", n, " parent_node is: ", wired_net.node[n]['parent_node'], "but this node is not in previous slice and not root."
                exit()
        slices.append(wired_net.copy())  ## note these are just nodes, not edges yet. (next step)

    return slices

def create_slices_minmax(graph):
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

    wired_net=wire_networks(newnet)

    slices.append(wired_net.copy())

    ## we are going to use this copy of the graph to iteratively modify
    nextNet = nx.Graph(is_directed=False)
    nextNet.add_nodes_from(wired_net.nodes(data=True)) ## copy just the nodes

    # now we want to use a % of the nodes from the previous slice -- and remove the result. New ones drawn from the original pool.
    num_current_nodes=len(list(current_nodes))

    ## based on the total number of nodes remaining (after the previous slice), divide up how many can be in each slice by the # of slices
    ## note this means that the MAX change with full replacement will use up all the nodes.

    num_nodes_to_remove= int(float(num_current_nodes) * (1-float(args.overlap)))# nodes to remove

    ## now create T+1, T+2, ... T+args.slices slices
    for ns in range(1,int(args.slices)):


        possible_parent_nodes = set(nextNet.nodes()) ## this list of possible parents (current set)
        ## remove 1 node at a time
        print "going to review ", num_nodes_to_remove, " nodes from graph with ", len(nextNet.nodes()), " nodes "

        ## create a set of nodes from tht will be those that can be removed (exclude newly created nodes at each slice)
        nodes_from_which_i_can_choose_to_remove = set(nextNet.nodes())

        for r in range(0,num_nodes_to_remove):

            ## pick a node to remove from existing nodes in graph
            chosen_node_to_remove = choice(list(nodes_from_which_i_can_choose_to_remove))
            nodes_from_which_i_can_choose_to_remove.difference_update([chosen_node_to_remove])
            chosen_node = choice(list(possible_nodes)) ## choose a node from the possible nodes to choose from (i.e., those not already added or deleted)
            possible_nodes.difference_update([chosen_node]) ## remove this from possible choices
            ##parent_node = choice(nextNet.nodes())
            nextNet.add_node(chosen_node,
                        label=chosen_node,
                        xcoord=nodeX[chosen_node],
                        ycoord=nodeY[chosen_node],level="ooops")
                        #parent_node=parent_node )
            current_nodes.update([chosen_node])  ## maintain the list of what's currently listed in the nodes

            ## remove node from current graph
            nextNet.remove_node(chosen_node_to_remove)

            ## remove from list of possible nodes to add
            possible_nodes.difference_update([chosen_node_to_remove])

            ## remove from list of nodes that are currently linked
            current_nodes.difference_update([chosen_node_to_remove])

            ## shouldnt have to remove the node from possible_parents since we
            ## get that list from the previous graph slice
            ##possible_parent_nodes.difference_update([chosen_node_to_remove])

        ## now wire the network
        wired_net = wire_networks(nextNet)

        parents = nx.get_node_attributes(wired_net, 'parent_node')
        ## find the node that is closest.

        #listOfWeights=nx.get_get_attributes(wired_net,'weight')
        #closestNode = min(listOfWeights, key=listOfWeights.get)
        for n in wired_net.nodes():
            try:
                test=parents[n];
            except:
                temp_set = possible_parent_nodes    ## temporary set
                temp_set.difference_update([n])     ## remove this from options (cant be own parent)
                wired_net.node[n]['parent_node']=choice(list(temp_set))
                ## now we need to update the edges -- so that the new node is in the right grou

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
    graph.node[nodeRoot]['child_of']='nobody'
    graph.node[nodeRoot]['parent_node']='i_am_root'
    possible_nodes = set(nodes)
    possible_nodes.difference_update([nodeRoot])
    linked_nodes=set([])
    ## now find a random set of children
    for n in range(0,int(args.children)):
        random_child=random.choice(list(possible_nodes))
        possible_nodes.difference_update([random_child])
        nodeChildren.update([random_child])
        linked_nodes.update([random_child])
        graph.node[random_child]['child_of']="root"
        graph.node[random_child]['level']="child"
        graph.node[random_child]['parent_node']=nodeRoot
    # now link grandchildren to children

    for n in list(nodeChildren):
        nodeGrandchildren[n]=[]
        for m in range(0,int(args.grandchildren)):
            random_gchild=random.choice(list(possible_nodes))
            possible_nodes.difference_update([random_gchild])
            nodeGrandchildren[n].append(random_gchild)
            linked_nodes.update([random_gchild])
            graph.node[random_gchild]['level']="grandchild"
            graph.node[random_gchild]['child_of']=n
            graph.node[random_gchild]['parent_node']=n
            #print "setting the parent_node to be: ", n

    ## filter nodes that are not part of hierarchy...
    for node in graph.nodes():
        if graph.node[node]['level']==None:
            graph.remove_node(node)

    return graph

def all_pairs(lst):
    return list((itertools.combinations(lst, 2)))

def wire_hierarchy(graph):
    global nodeChildren, nodeGrandchildren, nodeX, nodeY

    output_graph = nx.Graph(is_directed=False)
    output_graph.add_nodes_from(graph.nodes(data=True)) ## copy just the nodes

    root = None
    list_of_children = []
    list_of_grandchildren = []
    # get the list of children, root and grandchildren from the graph (not the lists)
    for n in graph.nodes():
        if graph.node[n]['level']=="root":
            root = n
        elif graph.node[n]['level']=="child":
            list_of_children.append(n)
        else:
            list_of_grandchildren.append(n)

    sumDistance=calc_sum_distance(graph)

    ##  wire to root
    for node in list_of_children:
        key1=root+"*"+node
        weight=float(args.root_child_weight)
        xcoord = nodeX[node]
        ycoord = nodeY[node]
        rootX = nodeX[root]
        rootY = nodeY[root]
        distance=calculate_distance(xcoord,ycoord,rootX,rootY)
        ## test to see that nodes exist

        if root not in output_graph.nodes():
            print "error: root (", root, ") not in list of nodes"
            break
        if node not in output_graph.nodes():
            print "error: node (", node, ") not in list of nodes."
            break
        output_graph.add_edge(root, node,name=key1,
                normalized=weight/sumDistance,
                unnormalized_weight=weight,
                from_node=root,
                to_node=node,
                distance=distance,
                weight=weight,
                type="root_to_child",
                linked_from="root",
                group="level_1")

        ## now find the grandchildren and wire to children
        for gnode in nodeGrandchildren[node]:
            if gnode not in output_graph.nodes():
                print "error: gnode (", gnode, ") not in list of nodes."
                break
            list_of_grandchildren.append(gnode)
            key1=node+"*"+gnode
            weight=float(args.child_gchild_weight)
            xcoord = nodeX[node]
            ycoord = nodeY[node]
            gnodeX = nodeX[gnode]
            gnodeY = nodeY[gnode]

            distance=calculate_distance(xcoord,ycoord,gnodeX,gnodeY)
            output_graph.add_edge(node, gnode,name=key1,
                normalized=float(weight)/float(sumDistance),
                unnormalized_weight=weight,
                from_node=node, to_node=gnode,
                distance=distance,
                weight=weight,
                type="child_to_gchild",
                linked_from=node,
                group="level_2")

    # wire % of the children together at low weight
    pairs_tuple = (all_pairs(list_of_children))
    pairs_string=[p[0]+"*"+p[1] for p in pairs_tuple]

    number_of_child_interconnects= int(len(pairs_string)*float(args.child_interconnect_percentage))
    #print number_of_child_interconnects
    if len(pairs_tuple)>0:
        random_pairs = np.random.choice(pairs_string, number_of_child_interconnects, replace=False)
        for random_pair_choice in random_pairs:
            random_pair = random_pair_choice.split("*")
            chosen_child=random_pair[0]
            link_child=random_pair[1]
            distance=calculate_distance(nodeX[chosen_child],nodeY[chosen_child],nodeX[link_child],nodeY[link_child])
            key1=chosen_child+"*"+link_child
            weight=float(args.child_interconnect_weight)

            output_graph.add_edge(chosen_child,
                                  link_child,name=key1,
                            normalized=weight/sumDistance,
                            unnormalized_weight=weight,
                            from_node=chosen_child,
                            to_node=link_child,
                            distance=distance,
                            weight=weight,
                            type="child_to_child",
                            linked_from="interconnect",
                            group="root")

    ## wire some fraction of the grandchildren together (by children)
    for n in list_of_children:
        gchildren_of_this_node = nodeGrandchildren[n]
        pairs_tuple = all_pairs(gchildren_of_this_node)
        pairs_string=[p[0]+"*"+p[1] for p in pairs_tuple]
        # wire some % of those grand children to each other at low connectivity
        number_of_gchild_interconnects= int(len(pairs_string)*float(args.gchild_interconnect_percentage))
        #print "Number of gchild interconnects: ", number_of_gchild_interconnects
        if len(pairs_tuple)>0:
            random_pairs = np.random.choice(pairs_string, number_of_gchild_interconnects, replace=False)
            for random_pair_string in random_pairs:
                random_pair=random_pair_string.split("*")
                chosen_gchild=random_pair[0]
                link_gchild=random_pair[1]
                if random_pair[0] != random_pair[1]:
                    distance=calculate_distance(nodeX[chosen_gchild],nodeY[chosen_gchild],nodeX[link_gchild],nodeY[link_gchild])
                    key1=chosen_gchild+"*"+link_gchild
                    weight=float(args.gchild_interconnect_weight)
                    output_graph.add_edge(chosen_gchild,
                                link_gchild,name=key1,
                                normalized=weight/sumDistance,
                                unnormalized_weight=weight,
                                from_node=chosen_gchild,
                                to_node=link_gchild,
                                distance=distance,
                                weight=weight,
                                type="gchild_to_gchild",
                                linked_from="interconnect",
                                group=n)
    #remove selfloops
    output_graph.remove_edges_from(output_graph.selfloop_edges())

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






