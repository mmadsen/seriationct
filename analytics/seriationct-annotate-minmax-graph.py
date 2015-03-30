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
import zipfile
import networkx as nx
from networkx.utils import open_file, make_str
import os
from decimal import *
from re import compile
import pprint as pp


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--networkmodel", help="path to ZIP format network model containing GML slices", required=True)
    parser.add_argument("--inputfile", help="path to GML version of minmax seriation output file", required=True)
    parser.add_argument("--modeltype", choices=['hierarchy', 'other', 'clustered'], required=True, default='other')
    parser.add_argument("--experiment", help="Experiment name, used to label graphics", required=True)
    #parser.add_argument("--")

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

"""

 Example of a node in a slice of a networkmodel:

  node [
    id 0
    label "assemblage-9-6"
    appears_in_slice 1
    ycoord 6
    level "child"
    child_of "root"
    xcoord 9
    parent_node "assemblage-19-20"
  ]

"""

def remove_exponent(d):
    '''Remove exponent and trailing zeros.  Used to ensure that we don't have
    scientific notation in node or edge attributes when we write the GML

    >>> remove_exponent(Decimal('5E+3'))
    Decimal('5000')

    '''
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()

def get_node_for_key(name, key, graph):
    """
    Returns the node ID for a node with a given "name" as the value
    for attribute "key", or None if there is no match
    """
    for n in graph.nodes():
        #log.debug("graph node: %s", graph.node[n])
        if graph.node[n][key] == name:
            return n
    return None



def read_gml_and_normalize_floats(file):
    """
    Read a GML file line by line, looking for scientific notation
    and when found, normalize it using the Decimal library.
    Then pass the lines of text to networkx parse_gml to
    parse it.  This is a drop-in replacement for read_gml()
    """
    exp_regex = compile(r"(\d+(\.\d+)?)[Ee](\+|-)(\d+)")

    input_lines = []

    with open(file, 'rb') as gmlfile:
        for line in gmlfile:
            result = exp_regex.search(line)
            if result is not None:
                matched_value = result.group(0)
                replacement = str(remove_exponent(Decimal(float(matched_value))))
                line = line.replace(matched_value, replacement)
                #log.debug("Replacing %s with %s", matched_value, replacement)

            input_lines.append(line)

    return nx.parse_gml(input_lines)


def parse_gml_and_normalize_floats(slice_lines):
    """
    Read a slice GML line by line, looking for scientific notation
    and when found, normalize it using the Decimal library.
    Then pass the lines of text to networkx parse_gml to
    parse it.  This is a drop-in replacement for read_gml()
    """
    exp_regex = compile(r"(\d+(\.\d+)?)[Ee](\+|-)(\d+)")

    input_lines = []


    for line in slice_lines:
        result = exp_regex.search(line)
        if result is not None:
            matched_value = result.group(0)
            replacement = str(remove_exponent(Decimal(float(matched_value))))
            line = line.replace(matched_value, replacement)
            #log.debug("Replacing %s with %s", matched_value, replacement)

        input_lines.append(line)

    return nx.parse_gml(input_lines)


def copy_attributes_to_minmax(g_slice = None, g_mm = None):
    """
    Given the nodes in the slice, copy appropriate attributes
    to the minmax graph. The nodes are identified by their
    label/name attributes, since the ID numbers have no guarantee
    of matching.

    """
    log.debug("mm nodes: %s", g_mm.nodes())

    for slice_node in g_slice.nodes():
        #log.debug("slice node: %s", g_slice.node[slice_node])

        mm_node_id = get_node_for_key(slice_node, "name", g_mm)

        if mm_node_id is None:
            # if we use samples of the original network model for seriation, not all of the slice
            # nodes will appear in the minmax graph.  this is NOT a bug, but we need to just
            # move on.
            continue

        g_mm.node[mm_node_id]['appears_in_slice'] = g_slice.node[slice_node]['appears_in_slice']

        # if the cluster_id attribute exists (meaning, new network creation scripts), copy it
        # but do not cause problems if the old program is in use.

        cluster = g_slice.node[slice_node]['cluster_id']
        if cluster is not None:
            g_mm.node[mm_node_id]['cluster_id'] = cluster
        if args.modeltype == 'hierarchy':
            g_mm.node[mm_node_id]['level'] = g_slice.node[slice_node]['level']
            g_mm.node[mm_node_id]['child_of'] = g_slice.node[slice_node]['child_of']
            g_mm.node[mm_node_id]['parent_node'] = g_slice.node[slice_node]['parent_node']

        #log.debug("annotated: %s", g_mm.node[mm_node_id])


def get_hierarchy_level_annotated_graphviz(input_graph, scheme):
    """
    Iterates over the nodes in a graph, looking for 'level' attributes.  For
    each child, picks a color and caches it, and a color for the root, using the
    specified graphviz color scheme.  Then, assigns
    grandchildren the color of their 'child_of' attribute.  Adds the 'fillcolor' attribute
    to each node in the NetworkX graph, and then returns the graph.
    """

        # make a copy so we don't touch the original graph, we'll return a new one
    g = input_graph.copy()

    # sometimes the "id" attribute is also the label, which we don't want for DOT production
    g = nx.convert_node_labels_to_integers(g)

    color_cache = dict()
    color_list = range(1, 11) # rdylgn11 brewer scheme in graphviz
    root_color = color_list.pop()

    # figure out penwidth scaling
    slice_ids = []
    for node, data in g.nodes_iter(data=True):
        slice_ids.append(g.node[node]['appears_in_slice'])

    max_slice = max(slice_ids)
    max_penwidth = 5.0

    # grandchildren might point their child_of attribute at a node which is not present
    # in this minmax graph given that we're operating with a sample of assemblages.
    # So when we find a child_of that's not represented in the
    for node, data in g.nodes_iter(data=True):

        # check if we're getting low on new colors...
        if len(color_list) == 0:
            log.info("All colors in scheme have been used, recycling but keeping roots unique")
            color_list = range(1,10)

        lab = g.node[node]['label']
        short_label = lab.replace('assemblage-','')
        #del g.node[node]['label']
        g.node[node]['short_label']= short_label

        g.node[node]['colorscheme'] = scheme
        g.node[node]['penwidth'] = (float(g.node[node]['appears_in_slice']) / max_slice) * max_penwidth

        if g.node[node]['level'] == 'root':
            g.node[node]['fillcolor'] = root_color
            color_cache[node] = root_color
            g.node[node]['shape'] = 'square'
        elif g.node[node]['level'] == 'child':
            name = g.node[node]['label']
            g.node[node]['shape'] = 'diamond'
            if name not in color_cache:
                color = color_list.pop()
                g.node[node]['fillcolor'] = color
                color_cache[name] = color
            else:
                color = color_cache[name]
                g.node[node]['fillcolor'] = color
        elif g.node[node]['level'] == 'grandchild':
            parent = g.node[node]['child_of']
            g.node[node]['shape'] = 'circle'
            if parent not in color_cache:
                color = color_list.pop()
                color_cache[parent] = color
                g.node[node]['fillcolor'] = color
            else:
                color = color_cache[parent]
                g.node[node]['fillcolor'] = color

    for node, data in g.nodes_iter(data=True):
        g.node[node]['label'] = g.node[node]['short_label']

    return g


def get_nonhierarchical_oldstyle_annotated_graphviz(input_graph):
    """
    Iterates over the nodes in a graph, annotating them for
    origin time and duration.
    """

    # base scheme has color sets from 3 to 9
    base_color_scheme = 'pubu'


        # make a copy so we don't touch the original graph, we'll return a new one
    g = input_graph.copy()

    # sometimes the "id" attribute is also the label, which we don't want for DOT production
    g = nx.convert_node_labels_to_integers(g)


    # figure out penwidth scaling
    slice_ids = set()
    for node, data in g.nodes_iter(data=True):
        slice_ids.add(g.node[node]['appears_in_slice'])

    num_slices = len(slice_ids)
    slice_max = max(list(slice_ids))

    if num_slices > 9:
        log.error("More slices than colors in the scheme list!!!")

    if num_slices < 3:
        log.info("Less slices than colors in the scheme, using pubu3")

    scheme = base_color_scheme
    scheme += str(slice_max)

    x = range(1,slice_max+1)
    y = reversed(range(1,slice_max+1))

    color_map = dict(zip(x,y))
    log.debug("x: %s", x)
    log.debug("y: %s", y)
    log.debug("color_map: %s", color_map)


    max_slice = max(slice_ids)
    max_penwidth = 5.0

    # grandchildren might point their child_of attribute at a node which is not present
    # in this minmax graph given that we're operating with a sample of assemblages.
    # So when we find a child_of that's not represented in the
    for node, data in g.nodes_iter(data=True):


        lab = g.node[node]['label']
        short_label = lab.replace('assemblage-','')
        #del g.node[node]['label']
        g.node[node]['short_label']= short_label

        g.node[node]['colorscheme'] = scheme
        #g.node[node]['penwidth'] = (float(g.node[node]['appears_in_slice']) / max_slice) * max_penwidth

        g.node[node]['fillcolor'] = color_map[int(g.node[node]['appears_in_slice'])]

    for node, data in g.nodes_iter(data=True):
        g.node[node]['label'] = g.node[node]['short_label']

    return g



def get_clustered_annotated_graphviz(input_graph):
    """
    Iterates over the nodes in a graph, annotating them for
    origin time and duration.
    """

    # base scheme has color sets from 3 to 9
    base_color_scheme = 'gnbu'


        # make a copy so we don't touch the original graph, we'll return a new one
    g = input_graph.copy()

    # sometimes the "id" attribute is also the label, which we don't want for DOT production
    g = nx.convert_node_labels_to_integers(g)


    # figure out penwidth scaling
    slice_ids = set()
    for node, data in g.nodes_iter(data=True):
        slice_ids.add(g.node[node]['appears_in_slice'])

    num_slices = len(slice_ids)
    slice_max = max(list(slice_ids))

    if num_slices > 9:
        log.error("More slices than colors in the scheme list!!!")

    if num_slices < 3:
        log.info("Less slices than colors in the scheme, using gnbu3")

    scheme = base_color_scheme
    scheme += str(slice_max)

    x = range(1,slice_max+1)
    y = reversed(range(1,slice_max+1))

    color_map = dict(zip(x,y))
    log.debug("x: %s", x)
    log.debug("y: %s", y)
    log.debug("color_map: %s", color_map)


    max_slice = max(slice_ids)
    max_penwidth = 6.0

    # grandchildren might point their child_of attribute at a node which is not present
    # in this minmax graph given that we're operating with a sample of assemblages.
    # So when we find a child_of that's not represented in the
    for node, data in g.nodes_iter(data=True):


        lab = g.node[node]['label']
        short_label = lab.replace('assemblage-','')
        #del g.node[node]['label']
        g.node[node]['short_label']= short_label

        g.node[node]['colorscheme'] = scheme
        #g.node[node]['penwidth'] = (float(g.node[node]['appears_in_slice']) / max_slice) * max_penwidth

        g.node[node]['fillcolor'] = color_map[int(g.node[node]['cluster_id'])]
        g.node[node]['penwidth'] = (float(g.node[node]['appears_in_slice']) / max_slice) * max_penwidth

    for node, data in g.nodes_iter(data=True):
        g.node[node]['label'] = g.node[node]['short_label']

    return g



def get_graphics_title(filename):
    import re

    occur = 6  # get the UUID and the replication number

    indices = [x.start() for x in re.finditer("-", filename)]
    uuid_part = filename[0:indices[occur-1]]
    rest = filename[indices[occur-1]+1:]

    title = args.experiment
    title += "-"
    title += uuid_part
    title += "-minmax-"
    title += args.modeltype

    return title




def write_ordered_dot(N,path,name="minmax seriation graph"):
    """Write NetworkX graph G to Graphviz dot format on path.

    Path can be a string or a file handle.
    """
    try:
        import pydot
    except ImportError:
        raise ImportError("write_dot() requires pydot",
                          "http://code.google.com/p/pydot/")

    title = get_graphics_title(name)

    log.debug("Plot title: %s", title)

    P=generate_ordered_dot(N, title)


    p = P.to_string();


    with open(path, 'wb') as pathfile:
        pathfile.write(p)
    return




def generate_ordered_dot(N, name=None):
    """
    The networkx write_dot() function generates
    """
    try:
        import pydot
    except ImportError:
        raise ImportError('to_pydot() requires pydot: '
                          'http://code.google.com/p/pydot/')

    # set Graphviz graph type
    if N.is_directed():
        graph_type='digraph'
    else:
        graph_type='graph'
    strict=N.number_of_selfloops()==0 and not N.is_multigraph()

    node_attrs = dict()
    node_attrs["shape"] = "circle"
    node_attrs["width"] = "0.75"
    node_attrs["height"] = "0.75"
    node_attrs["label"] = ""
    node_attrs["fixedsize"] = "true"
    node_attrs["style"] = "filled"

    graph_defaults=N.graph.get('graph',{})
    graph_defaults["ratio"] = "auto"
    graph_defaults["labelloc"] = "b"
    graph_defaults["label"] = name
    graph_defaults["pad"] = "1.0"


    if name is None:
        P = pydot.Dot(graph_type=graph_type,strict=strict,**graph_defaults)
    else:
        P = pydot.Dot('"%s"'%name,graph_type=graph_type,strict=strict,
                      **graph_defaults)
    try:
        P.set_node_defaults(**node_attrs)
    except KeyError:
        pass
    try:
        P.set_edge_defaults(**N.graph['edge'])
    except KeyError:
        pass

    for n,nodedata in sorted(N.nodes_iter(data=True), key=lambda n: int(n[0])):
        str_nodedata=dict((k,make_str(v)) for k,v in nodedata.items())

        if "name" in str_nodedata:
            del str_nodedata['name']

        #print "str_nodedata: %s" % str_nodedata
        p=pydot.Node(make_str(n),**str_nodedata)
        P.add_node(p)

    if N.is_multigraph():
        for u,v,key,edgedata in N.edges_iter(data=True,keys=True):
            str_edgedata=dict((k,make_str(v)) for k,v in edgedata.items())
            edge=pydot.Edge(make_str(u),make_str(v),key=make_str(key),**str_edgedata)
            P.add_edge(edge)

    else:



        for u,v,edgedata in sorted(N.edges_iter(data=True), key=lambda u: int(u[0]) ):
            str_edgedata=dict((k,make_str(v)) for k,v in edgedata.items())
            if int(v) < int(u):
                edge = pydot.Edge(make_str(v),make_str(u),**str_edgedata)
            else:
                edge=pydot.Edge(make_str(u),make_str(v),**str_edgedata)
            P.add_edge(edge)
    return P









if __name__ == "__main__":
    setup()

    # parse the inputfile and calculate the output file name
    input_basename = os.path.basename(args.inputfile)
    root, ext = os.path.splitext(input_basename)
    input_path = os.path.dirname(args.inputfile)
    if input_path is '':
        input_path = '.'
    output_filename = input_path + '/' + root + "-annotated.gml"
    log.info("Processing input %s to output %s", input_basename, output_filename)

    # read the minmax input file
    mm = read_gml_and_normalize_floats(args.inputfile)

    # parse the slices in the networkmodel
    zf = zipfile.ZipFile(args.networkmodel, 'r')
    for file in [f for f in zf.namelist() if f.endswith(".gml")]:
        if file.startswith("__"):
            pass
        else:
            gml = zf.read(file)
            slice = parse_gml_and_normalize_floats(gml)

            copy_attributes_to_minmax(g_slice = slice, g_mm = mm)


    # now save the annotated graph to a file in GML format
    nx.write_gml(mm, output_filename)


    if args.modeltype == 'hierarchy':
        # for hierarchical models, label them with their level and child groupings and
        # write a graph to the filesystem
        gv_annotated = get_hierarchy_level_annotated_graphviz(mm, 'rdylgn11')
        dot_filename = input_path + '/' + root + "-annotated-hierarchy.dot"
        png_filename = input_path + '/' + root + "-annotated-hierarchy.png"
    elif args.modeltype == 'other':
        # for other models, annotate the graph with origin time and duration of assemblages
        gv_annotated = get_nonhierarchical_oldstyle_annotated_graphviz(mm)
        dot_filename = input_path + '/' + root + "-annotated-chronological.dot"
        png_filename = input_path + '/' + root + "-annotated-chronological.png"
    elif args.modeltype == 'clustered':
        gv_annotated = get_clustered_annotated_graphviz(mm)
        dot_filename = input_path + '/' + root + "-clustered-annotated-chronological.dot"
        png_filename = input_path + '/' + root + "-clustered-annotated-chronological.png"


    write_ordered_dot(gv_annotated, dot_filename, name=root)

    cmd = "neato -Tpng "
    cmd += dot_filename
    cmd += " -o "
    cmd += png_filename

    os.system(cmd)




