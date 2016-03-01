#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Methods and classes from algebraic graph theory for graph analysis.

"""

import networkx as nx
import numpy as np

def graph_spectral_similarity(g1, g2, threshold = 0.9):
    """
    Returns the eigenvector similarity, between [0, 1], for two NetworkX graph objects, as
    the sum of squared differences between the sets of Laplacian matrix eigenvalues that account
    for a given fraction of the total sum of the eigenvalues (default = 90%).

    Similarity scores of 0.0 indicate identical networkmodeling (given the adjacency matrix, not necessarily
    node identity or annotations), and large scores indicate strong dissimilarity.  The statistic is
    unbounded above.
    """
    l1 = nx.spectrum.laplacian_spectrum(g1, weight=None)
    l2 = nx.spectrum.laplacian_spectrum(g2, weight=None)
    k1 = _get_num_eigenvalues_sum_to_threshold(l1, threshold=threshold)
    k2 = _get_num_eigenvalues_sum_to_threshold(l2, threshold=threshold)
    k = min(k1,k2)
    sim = sum((l1[:k] - l2[:k]) ** 2)
    return sim


def _get_num_eigenvalues_sum_to_threshold(spectrum, threshold = 0.9):
    """
    Given a spectrum of eigenvalues, find the smallest number of eigenvalues (k)
    such that the sum of the k largest eigenvalues of the spectrum
    constitutes at least a fraction (threshold, default = 0.9) of the sum of all the eigenvalues.
    """
    if threshold is None:
        return len(spectrum)

    total = sum(spectrum)
    if total == 0.0:
        return len(spectrum)

    spectrum = sorted(spectrum, reverse=True)
    running_total = 0.0

    for i in range(len(spectrum)):
        running_total += spectrum[i]
        if running_total / total >= threshold:
            return i + 1
    # guard
    return len(spectrum)



