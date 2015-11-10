#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Functions for adding annotations to IDSS seriation output (sumgraph or minmax graph, by weight or count), from a
seriationct network model.

"""

import logging as log
import zipfile
import networkx as nx
from networkx.utils import open_file, make_str
import os
from decimal import *
from re import compile
import pprint as pp


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


def copy_attributes_to_minmax(g_slice, g_mm, modeltype):
    """
    Given the nodes in the slice, copy appropriate attributes
    to the minmax graph. The nodes are identified by their
    label/name attributes, since the ID numbers have no guarantee
    of matching.

    """
    #log.debug("mm nodes: %s", g_mm.nodes())

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
        lineage = g_slice.node[slice_node]['lineage_id']
        if lineage is not None:
            g_mm.node[mm_node_id]['lineage_id'] = lineage
        if modeltype == 'hierarchy':
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
        slice_ids.add(int(g.node[node]['appears_in_slice']))

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



def _create_greyscale_map(g):
    """
    Given an input graph which defines a number of slices, and the range of slice ID's,
    create a useful spread of greyscale values mapped to slice ID's for a given graph.
    Returns a tuple of color_scheme, color_map for use by the caller.
    """
    slice_ids = set()
    for node, data in g.nodes_iter(data=True):
        slice_ids.add(int(g.node[node]['appears_in_slice']))

    num_slices = len(slice_ids)
    slice_max = max(list(slice_ids))

    # heuristic for figuring out spacing and colors given number of slices
    # practical range runs from grey30 to 100

    step = int(70 / slice_max)

    color_names = []
    for color in xrange(30,100,step):
        color_name = "grey" + str(color)
        color_names.append(color_name)

    slices = range(1,slice_max+1)
    color_map = dict(zip(slices,color_names))

    #log.info("color_map: %s", color_map)
    return ('x11', color_map)



def get_clustered_annotated_graphviz(input_graph):
    """
    Iterates over the nodes in a graph, annotating them for
    origin time and duration.
    """

    # base scheme has large number of greyscale options
    base_color_scheme = 'x11'


        # make a copy so we don't touch the original graph, we'll return a new one
    g = input_graph.copy()

    # sometimes the "id" attribute is also the label, which we don't want for DOT production
    g = nx.convert_node_labels_to_integers(g)


    base_color_scheme, color_map = _create_greyscale_map(g)



    # max_slice = max(slice_ids)
    max_penwidth = 6.0

    # grandchildren might point their child_of attribute at a node which is not present
    # in this minmax graph given that we're operating with a sample of assemblages.
    # So when we find a child_of that's not represented in the
    for node, data in g.nodes_iter(data=True):


        lab = g.node[node]['label']
        short_label = lab.replace('assemblage-','')
        #del g.node[node]['label']
        g.node[node]['short_label']= short_label

        g.node[node]['colorscheme'] = base_color_scheme
        #g.node[node]['penwidth'] = (float(g.node[node]['appears_in_slice']) / max_slice) * max_penwidth

        g.node[node]['fillcolor'] = color_map[int(g.node[node]['cluster_id'])]
        #g.node[node]['penwidth'] = (float(g.node[node]['appears_in_slice']) / max_slice) * max_penwidth

    for node, data in g.nodes_iter(data=True):
        g.node[node]['label'] = g.node[node]['short_label']

    return g


def get_lineage_annotated_graphviz(input_graph):
    """
    Iterates over the nodes in a graph, annotating them for
    origin time and duration.
    """

    # base scheme has color sets from 3 to 9
    base_color_scheme = 'x11'

    lineage_to_shape = dict()
    lineage_to_shape[0] = 'circle'
    lineage_to_shape[1] = 'square'
    lineage_to_shape[2] = 'diamond'
    lineage_to_shape[3] = 'parallelogram'
    lineage_to_shape[4] = 'pentagon'



        # make a copy so we don't touch the original graph, we'll return a new one
    g = input_graph.copy()

    # sometimes the "id" attribute is also the label, which we don't want for DOT production
    g = nx.convert_node_labels_to_integers(g)


    base_color_scheme, color_map = _create_greyscale_map(g)
    max_penwidth = 6.0

    # grandchildren might point their child_of attribute at a node which is not present
    # in this minmax graph given that we're operating with a sample of assemblages.
    # So when we find a child_of that's not represented in the
    for node, data in g.nodes_iter(data=True):


        lab = g.node[node]['label']
        short_label = lab.replace('assemblage-','')
        #del g.node[node]['label']
        g.node[node]['short_label']= short_label

        g.node[node]['colorscheme'] = base_color_scheme
        #g.node[node]['penwidth'] = (float(g.node[node]['appears_in_slice']) / max_slice) * max_penwidth

        g.node[node]['fillcolor'] = color_map[int(g.node[node]['appears_in_slice'])]
        g.node[node]['shape'] = lineage_to_shape[int(g.node[node]['lineage_id'])]
        #g.node[node]['penwidth'] = (float(g.node[node]['appears_in_slice']) / max_slice) * max_penwidth

    for node, data in g.nodes_iter(data=True):
        g.node[node]['label'] = g.node[node]['short_label']

    return g





def get_graphics_title(root, sample_type, experiment, modeltype, addlabel):
    import re

    log.debug("root: %s", root)

    occur = 12  # get the UUID and sampling fractions, and whether it's a minmax graph
    indices = [x.start() for x in re.finditer("-", root)]
    uuid_part = root[0:indices[occur-1]]
    rest = root[indices[occur-1]+1:]

    if re.match(r".*continuity.*", rest):
        seriation_type = "continuity"
    else:
        seriation_type = "frequency"

    title = experiment
    title += "  "
    if addlabel != None:
        title += addlabel
        title += " "
    title += sample_type
    title += "  "
    title += uuid_part
    title += "  "
    title += modeltype
    title += "  "
    title += seriation_type

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

    log.debug("Plot title: %s", name)

    P=generate_ordered_dot(N, name)




    p = P.to_string();
    #log.debug("dot: %s", p)


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
    #node_attrs["label"] = ""
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