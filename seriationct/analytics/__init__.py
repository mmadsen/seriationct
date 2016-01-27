#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
from networkmodel_annotation import read_gml_and_normalize_floats, \
    get_graphics_title, \
    parse_gml_and_normalize_floats, \
    copy_attributes_to_minmax, \
    get_clustered_annotated_graphviz, \
    get_hierarchy_level_annotated_graphviz, \
    get_lineage_annotated_graphviz, \
    get_nonhierarchical_oldstyle_annotated_graphviz, \
    write_ordered_dot


from graph_algebra import graph_spectral_similarity