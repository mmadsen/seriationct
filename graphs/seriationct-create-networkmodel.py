

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
    python create_graphs.py --filename test --model grid --writing minmax -slices 5
    python create_graphs.py --filename test --model grid --slices 5 --x 20 --y 20 --wiring complete
    python create_graphs.py --filename test --model grid --slices 5 --x 20 --y 20 --wiring random
    python create_graphs.py --filename test --model grid --slices 5  --wiring hierarchy

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
    parser.add_argument("--levels",help="number of levels in hierarchical model.", default=5)
    parser.add_argument("--children",help="number of children per level.",default=5)
    parser.add_argument("--configuration", help="Path to configuration file")
    parser.add_argument("--slices", help="Number of graph slices to create", default=5)
    parser.add_argument("--model", choices=['grid','linear','branch'], required=True, default="grid")
    parser.add_argument("--wiring", help="Kind of wiring to use in underlying model",
                        choices=['minmax','complete','mst','hierarchy','random'], default='complete')
    parser.add_argument("--graphs", help="create plots of networks", default=True)
    parser.add_argument("--graphshow", help="show plots in runtime.", default=True)
    parser.add_argument("--gchild_interconnect", help="in the case of a heirarchical graph, what fraction of grandchildren are connected to each other (0-1.0) Default is 0.2", default=0.00)
    parser.add_argument("--child_interconnect", help="in the case of a heirarchical graph, what fraction of children are connected to each other (0-1.0) Default is 0.1", default=0.00)
    parser.add_argument("--overlap",
                        help="specify % of nodes to overlap from slice to slice. 0=No overlap, 1 = 100% overlap. Values must be between 0.0 and 1.0. For example. 0.5 for 50%", default=0.80)
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
    global nodeNames, nodeX, nodeY, spacefactor, nodeRoot, nodeChildren, nodeGrandchildren
    nodeNames=[]
    nodeChildren=[]
    nodeX={}
    nodeY={}
    nodeGrandchildren={}
    spacefactor=1
    nodeRoot=""
    net = nx.Graph(name=args.model, is_directed=False)
    xcoord=0
    ycoord=0
    if args.model=="grid":
        for yc in range(1,int(args.x)):
            for xc in range(1,int(args.y)):
                name="assemblage-"+str(xc)+"-"+str(yc)
                net.add_node(name,label=name,xcoord=xc, ycoord=yc)
                nodeNames.append(name)
                nodeX[name]=xc
                nodeY[name]=yc
    else:
        print "Please choose a model for the vertices. Default is grid. Others are currently unimplemented."

    return net


def create_slices(graph):

    if args.wiring in ["hierarchy", "minmax"]:
        slices = create_slices_hierarchy(graph)
    else:
        slices= create_slices_random(graph)

    return slices

def create_slices_hierarchy(graph):
    global nodeRoot, nodeChildren, nodeGrandchildren
    number_per_slice=int((int(args.x)*int(args.y))/int(args.slices))
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
            newnet.add_node(chosen_node,label=chosen_node,xcoord=nodeX[chosen_node], ycoord=nodeY[chosen_node]) # add node
            current_nodes.update([chosen_node])
        except:
            pass# update set of possible nodes

    if args.wiring=="hierarchy":
        hierarchy_net = create_hierarchy_in_graph(newnet)
        wired_net=wire_networks(hierarchy_net)
    else:
        wired_net=wire_networks(newnet)

    #plot_slice(wired_net)
    slices.append(wired_net)
    #print current_nodes
    ## next n slices

    children=set(nodeChildren)

    for ns in range(2,int(args.slices)+1):
        newnet.graph['name']=args.model+"-"+str(ns)
        # now we want to use a % of the nodes from the previous slice -- and remove the result. New ones drawn from the original pool.
        num_current_nodes=len(list(current_nodes))
        num_nodes_to_remove= int(float(num_current_nodes) * (1-float(args.overlap)))+1# nodes to remove

        for r in range(0,num_nodes_to_remove):
            chosen_node_to_remove = choice(newnet.nodes())
            #print "chosen node to remove: ", chosen_node_to_remove
            #print "newnet had ", len(newnet.nodes())
            newnet.remove_node(chosen_node_to_remove)
            ## for hierarchy
            if chosen_node_to_remove in nodeChildren:
                children.difference_update([chosen_node_to_remove])
                nodeChildren=list(children)
                listOfAbandonedGchildren=nodeGrandchildren[chosen_node_to_remove]
                ## need to find new children to attach grandchildren to...
                for gc in listOfAbandonedGchildren:
                    newParent=random.choice(nodeChildren)
                    nodeGrandchildren[newParent].append(gc)

            elif chosen_node_to_remove in nodeGrandchildren.items():
                for key in nodeGrandchildren.iterkeys():

                    setOfGrandchildrenForChild=set(nodeGrandchildren[key])
                    if chosen_node_to_remove in nodeGrandchildren[key]:
                        setOfGrandchildrenForChild.difference_update([chosen_node_to_remove])
                        nodeGrandchildren[key]=list(setOfGrandchildrenForChild)

            possible_nodes.difference_update([chosen_node_to_remove])
            #print "now newnet has ", len(newnet.nodes())
            current_nodes.difference_update([chosen_node_to_remove])

        num_nodes_to_add = num_nodes_to_remove

        for r in range(0,num_nodes_to_add):
            chosen_node = choice(list(possible_nodes))
            possible_nodes.difference_update(chosen_node)
            ## find a parent for the node - must be from one of the existing nodes
            parent_node = choice(list(possible_nodes))
            newnet.add_node(chosen_node,label=chosen_node,xcoord=nodeX[chosen_node], ycoord=nodeY[chosen_node], parent_node=parent_node )
            current_nodes.update([chosen_node])

        ## now create a new graph
        updatedNet = nx.Graph(name=args.model+"-"+str(ns), is_directed=False)
        updatedNet.add_nodes_from(newnet.nodes(data=True)) ## copy just the nodes
        newnet = updatedNet.copy() ## copy back to newnet
        ## now wire the network
        wired_net = wire_networks(newnet)
        slices.append(wired_net)  ## note these are just nodes, not edges yet. (next step)
    return slices


def create_slices_random(graph):
    number_per_slice=int((int(args.x)*int(args.y))/int(args.slices))
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
            newnet.add_node(chosen_node,label=chosen_node,xcoord=nodeX[chosen_node], ycoord=nodeY[chosen_node]) # add node
            current_nodes.update([chosen_node])
        except:
            pass# update set of possible nodes

    wired_net=wire_networks(newnet)
    #plot_slice(wired_net)
    slices.append(wired_net)

    for ns in range(2,int(args.slices)+1):
        newnet.graph['name']=args.model+"-"+str(ns)
        # now we want to use a % of the nodes from the previous slice -- and remove the result. New ones drawn from the original pool.
        num_current_nodes=len(list(current_nodes))
        num_nodes_to_remove= int(float(num_current_nodes) * (1-float(args.overlap)))+1# nodes to remove

        for r in range(0,num_nodes_to_remove):
            chosen_node_to_remove = choice(newnet.nodes())
            newnet.remove_node(chosen_node_to_remove)
            possible_nodes.difference_update([chosen_node_to_remove])
            current_nodes.difference_update([chosen_node_to_remove])
        num_nodes_to_add = num_nodes_to_remove

        for r in range(0,num_nodes_to_add):
            chosen_node = choice(list(possible_nodes))
            possible_nodes.difference_update(chosen_node)
            parent_node = choice(list(possible_nodes))
            newnet.add_node(chosen_node,label=chosen_node,xcoord=nodeX[chosen_node], ycoord=nodeY[chosen_node],parent_node=parent_node )
            random_link_node=random.choice(newnet.nodes())

            key1=chosen_node+"*"+random_link_node
            weight=random.random()
            distance=calculate_distance(nodeX[chosen_node],nodeY[chosen_node],nodeX[random_link_node],nodeY[random_link_node])
            newnet.add_edge(chosen_node, random_link_node,name=key1,
                        unnormalized_weight=weight,
                        from_node=chosen_node, to_node=random_link_node, distance=distance,weight=weight)
            #print "adding node: ", chosen_node
            current_nodes.update([chosen_node])

        slices.append(newnet)  ## note these are just nodes, not edges yet. (next step)
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
    elif args.wiring == 'complete':
        tree = createCompleteGraphByDistance(input_graph=slice,weight='distance')
    elif args.wiring =="hierarchy":
        tree= wire_hierarchy(slice)
    elif args.wiring=="minmax":
        tree = createMinMaxGraphByWeight(input_graph=slice, weight='weight')
    elif args.wiring=="random":
        tree = createRandomGraph(input_graph=slice)
    else:
        ## use minmax as default
        tree = createMinMaxGraphByWeight(input_graph=slice, weight='weight')

    return tree

def createRandomGraph(**kwargs):
    global nodeX, nodeY
    graph=kwargs.get('input_graph')

    nodes = graph.nodes()
    nodes_linked=set([])
    possible_nodes=set(nodes)

    # pick a random node to start
    first_node = choice(nodes)
    possible_nodes.difference_update([first_node])
    nodes_linked.update([first_node])

    sumDistance=calc_sum_distance(graph)

    for n in list(possible_nodes):
        chosen_node_to_add = choice(list(possible_nodes))

        nodes_linked.update([chosen_node_to_add])
        possible_nodes.difference_update([chosen_node_to_add])
        chosen_node_to_link=choice(list(nodes_linked))
        key1=chosen_node_to_add+"*"+chosen_node_to_link
        weight=random.random()
        distance=calculate_distance(nodeX[chosen_node_to_add],nodeY[chosen_node_to_add],nodeX[chosen_node_to_link],nodeY[chosen_node_to_link])
        graph.add_edge(chosen_node_to_add, chosen_node_to_link,name=key1,
                        normalized=weight/sumDistance,
                        unnormalized_weight=weight,
                        from_node=chosen_node_to_add, to_node=chosen_node_to_link, distance=distance,weight=weight)

    return graph


def create_hierarchy_in_graph(graph):
    global spacefactor, nodeRoot, nodeChildren, nodeGrandchildren
    # first find a random node to be the root
    nodes = graph.nodes()
    root = random.choice(nodes)
    nodeRoot=root
    possible_nodes = set(nodes)
    linked_nodes=set([])
    ## now find a random set of children
    for n in range(0,int(args.children)):
        random_child=random.choice(list(possible_nodes))
        possible_nodes.difference_update([random_child])
        nodeChildren.append(random_child)
        linked_nodes.update([random_child])
    # now link grandchildren to children
    for n in nodeChildren:
        gchildlist=[]
        for m in range(0,int(args.children)):
            random_gchild=random.choice(list(possible_nodes))
            possible_nodes.difference_update([random_gchild])
            gchildlist.append(random_gchild)
            linked_nodes.update([random_gchild])

        nodeGrandchildren[n]=gchildlist

    ## filter nodes that are part of hierarchy...
    for node in graph.nodes():
        if node==root or node in nodeChildren or node in nodeGrandchildren:
            pass
        else:
            graph.remove_node(node)

    return graph

def wire_hierarchy(graph):
    global spacefactor, nodeRoot, nodeChildren, nodeGrandchildren, nodeX, nodeY

    sumDistance=calc_sum_distance(graph)

    ##  wire to root
    for node in nodeChildren:
        key1=nodeRoot+"*"+node
        weight=1
        xcoord = nodeX[node]
        ycoord = nodeY[node]
        rootX = nodeX[nodeRoot]
        rootY = nodeY[nodeRoot]
        distance=calculate_distance(xcoord,ycoord,rootX,rootY)
        graph.add_edge(nodeRoot, node,name=key1,
                normalized=weight/sumDistance,
                unnormalized_weight=weight,
                from_node=nodeRoot, to_node=node, distance=distance,weight=weight)

        ## now find the grandchildren and wire to children

        for gnode in nodeGrandchildren[node]:
            key1=node+"*"+gnode
            weight=1
            xcoord = nodeX[node]
            ycoord = nodeY[node]
            gnodeX = nodeX[gnode]
            gnodeY = nodeY[gnode]
            distance=calculate_distance(xcoord,ycoord,gnodeX,gnodeY)
            graph.add_edge(node, gnode,name=key1,
                normalized=weight/sumDistance,
                unnormalized_weight=weight,
                from_node=node, to_node=gnode, distance=distance,weight=weight)

    # wire 20% of the children together at low rate

    number_of_children=len(nodeChildren)
    possible_children=set(nodeChildren)
    for n in range(0,int(number_of_children*float(args.child_interconnect))):
        chosen_child=choice(list(possible_children))
        possible_children.difference_update([chosen_child])
        link_child=choice(list(possible_children))
        distance=calculate_distance(nodeX[chosen_child],nodeY[chosen_child],nodeX[link_child],nodeY[link_child])
        key1=chosen_child+"*"+link_child
        weight=0.1
        graph.add_edge(chosen_child, link_child,name=key1,
                        normalized=weight/sumDistance,
                        unnormalized_weight=weight,
                        from_node=chosen_child, to_node=link_child, distance=distance,weight=weight)

    ## wire some fraction of the grandchildren together
    gchildren=[]
    for g in nodeChildren:
        for gg in nodeGrandchildren:
            if gg not in gchildren:
                gchildren.append(gg)
    number_of_gchildren=len(gchildren)
    possible_gchildren=set(gchildren)
    # wire 50% of those grand children to each other at low connectivity
    for n in range(0,int(number_of_gchildren*float(args.gchild_interconnect))):
        chosen_gchild=choice(list(possible_gchildren))
        possible_gchildren.difference_update([chosen_gchild])
        link_gchild=choice(list(possible_gchildren))
        distance=calculate_distance(nodeX[chosen_gchild],nodeY[chosen_gchild],nodeX[link_gchild],nodeY[link_gchild])
        key1=chosen_gchild+"*"+link_gchild
        weight=0.1
        graph.add_edge(chosen_child, link_gchild,name=key1,
                        normalized=weight/sumDistance,
                        unnormalized_weight=weight,
                        from_node=chosen_gchild, to_node=link_gchild, distance=distance,weight=weight)

    return graph

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
    output_graph.add_nodes_from(graph.nodes(data=True)) ## copy just the nodes
    ## first add all of the nodes
    ##for name in new_graph.nodes():
    ##    output_graph.add_node(name, name=name, label=name, xcoord=nodeX[name],ycoord=nodeY[name])

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
                    weight=0.000000000001
                output_graph.add_path([a1, a2], normalized_weight=normalized_weight,unnormalized_weight=weight,
                                      distance=distance, weight=weight)
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
    nx.draw_networkx(slice,pos,node_size=20,node_color='red', with_labels=False)
    title=args.filename + "Slice-"+str(i)
    plt.title(title)
    i+=1
    if args.graphshow == 1:
        plt.show()

def plot_slices(wired_slices):
    i=0
    for slice in wired_slices:

        pos={}
        for label in slice.nodes():
            x = get_attribute_from_node(label,'xcoord')
            y = get_attribute_from_node(label,'ycoord')
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
    #wired_slices=wire_networks(slices)
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






