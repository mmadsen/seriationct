#!/usr/bin/env python

#
# $File: utils.py $
# $LastChangedDate: 2014-02-05 14:38:36 -0600 (Wed, 05 Feb 2014) $
# $Rev: 4792 $
#
# This file is part of simuPOP, a forward-time population genetics
# simulation environment. Please visit http://simupop.sourceforge.net
# for details.
#
# Copyright (C) 2004 - 2010 Bo Peng (bpeng@mdanderson.org)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


"""
simuPOP demographic models

This module provides some commonly used demographic models. In addition
to several migration rate generation functions, it provides models that
encapsulate complete demographic features of one or more populations (
population growth, split, bottleneck, admixture, migration). These models
provides:

1. The model itself can be passed to parameter subPopSize of a mating
   scheme to determine the size of the next generation. More importantly,
   it performs necessary actions of population size change when needed.

2. The model provides attribute num_gens, which can be passed to parameter
   ``gens`` of ``Simulator.evolve`` or ``Population.evolve`` function.
   A demographic model can also terminate an evolutionary process by
   returnning an empty list so ``gens=model.num_gens`` is no longer required.

"""


import sys
import time
import math


from simuPOP import Population, RandomSelection, PyOperator


from collections import OrderedDict

# the following lecture provides a good review of demographic models
#
# http://www.stats.ox.ac.uk/~mcvean/L5notes.pdf

try:
    import numpy as np
    import matplotlib.pylab as plt
    has_plotter = True
except ImportError:
    has_plotter = False



class BaseMetapopulationModel:
    '''This class is the base class for all demographic models and 
    provides common interface and utility functions for derived classes. A
    demographic model is essentially a callable Python object that encapsulates
    required functions of a demographic model, to determine initial population
    size (``Population(size=model.init_size, infoFields=model.info_fields)``, 
    to determine size of offspring population during evolution (``subPopSize=model``
    of a mating scheme), and number of generations to evolve (``gen=model.num_gens``),
    although the first and last utility could be relaxed to for models that
    could be applied to populations with different sizes, and models that evolve
    indefinitely. '''
    def __init__(self, numGens=-1, initSize=[], ops=[], infoFields=[]):
        '''Set attributes ``init_size``, ``info_fields``, and ``num_gens``
        to a demographic model. The initial population will be merged or
        split to match ``initSize``. For example, ``N0=[A, [B,C]]`` is a 3-subpop
        model where the last two subpopulation will be split (and resize if needed)
        from the second subpopulation of the initial subpopulation (which should
        have two subpopulations). The population size can be an integer for fixed
        population size, None for the size of the population or subpopulation when
        the demographic model is first applied to, or a float number representing
        the proportion (can be larger than 1) of individuals for the whole or
        corresponding subpopulation. A ``None`` value will be assigned to
        attribute ``init_size`` in such a case because the initial population 
        size is determined dynamically. In addition, whenever a population size
        is allowed, a tuple of ``(size, name)`` is acceptable, which assigns 
        ``name`` to the corresponding subpopulation. ``numGens`` can be a
        non-negative number or ``-1``, which allows the demographic model to 
        be determinated by a terminator. One or more operators (e.g. a migration
        operator or a terminator) could be passed (parameter ``ops``) and will
        be applied to the population. The demographic model will return ``[]``
        (which will effectively terminate the evolutioonary process) if any of the
        operator returns ``False``. Information fields required by these operators
        should be passed to ``infoFields``. '''
        #
        self._raw_init_size = initSize
        self.init_size = self._extractSize(initSize)
        # for demographic model without fixed initial population size, set init_size to []
        if isinstance(self.init_size, int):
            self.init_size = [self.init_size]
        elif self.init_size is None or None in self.init_size or \
            any([isinstance(x, float) for x in self.init_size]):
            self.init_size = []
        #
        if isinstance(infoFields, (list, tuple)):
            self.info_fields = infoFields
        else:
            self.info_fields = [infoFields]
        if numGens is None:
            self.num_gens = -1
        else:
            self.num_gens = numGens
        if isinstance(ops, (tuple, list)):
            self.ops = list(ops)
        else:
            self.ops = [ops]
        #
        # history
        self.size_cache = {}

    def _reset(self):
        if hasattr(self, '_start_gen'):
            del self._start_gen

    def _isNamedSize(self, x):
        return isinstance(x, tuple) and len(x) == 2 and \
            isinstance(x[1], str) and self._isSize(x[0])

    def _isSize(self, x):
        if sys.version_info.major == 2:
            return isinstance(x, (int, long, float)) or x is None
        else:
            return isinstance(x, (int, float)) or x is None

    def _extractSize(self, sz):
        # sz = 100
        if self._isSize(sz):
            return [sz]
        elif self._isNamedSize(sz):
            return sz[0]
        res = []
        for x in sz:
            # sz = [100, 200]
            if self._isSize(x):
                res.append(x)
            # sz = [(100, 'name')]
            elif self._isNamedSize(x):
                res.append(x[0])
            # a group 
            # sz = [[100, 200], 300]
            # sz = [[(100, 'AS'), 200], 300]
            elif isinstance(x, (tuple, list)):
                # sz = [(100, 'AS'), (200, 'ZX')]
                for y in x:
                    if self._isSize(y):
                        res.append(y)
                    elif self._isNamedSize(y):
                        res.append(y[0])
                    else:
                        raise ValueError('Unacceptable population size: %s' % sz)
            else:
                raise ValueError('Unacceptable population size: %s' % sz)
        return res

    def _convertToNamedSize(self, sz):
        # sz = 100
        if self._isSize(sz):
            return [(sz, '')]
        elif self._isNamedSize(sz):
            return [sz]
        res = []
        for x in sz:
            # sz = [100, 200]
            if self._isSize(x):
                res.append((x, ''))
            # sz = [(100, 'name')]
            elif self._isNamedSize(x):
                res.append(x)
            # a group 
            # sz = [[100, 200], 300]
            # sz = [[(100, 'AS'), 200], 300]
            elif isinstance(x, (tuple, list)):
                res.append([])
                # sz = [(100, 'AS'), (200, 'ZX')]
                for y in x:
                    if self._isSize(y):
                        res[-1].append((y, ''))
                    elif self._isNamedSize(y):
                        res[-1].append(y)
                    else:
                        raise ValueError('Unacceptable population size: %s' % sz)
            else:
                raise ValueError('Unacceptable population size: %s' % sz)
        return res

    def _fitToSize(self, pop, size):
        '''
        Fit a population to new size, split and merge population if needed
        '''
        # if size is None or size is [], return unchanged
        if not size:
            return 
        named_size = self._convertToNamedSize(size)
        if pop.numSubPop() > 1:
            # merge subpopualtions
            if len(named_size) == 1:
                pop.mergeSubPops()
                if named_size[0][1] != '':
                    pop.setSubPopName(named_size[0][1], 0)
                # resize if the type is int or float (proportion)
                if isinstance(named_size[0][0], int):
                    pop.resize(named_size[0][0])
                elif isinstance(named_size[0][0], float):
                    pop.resize(int(named_size[0][0] * pop.popSize()), propagate=True)
            elif len(size) != pop.numSubPop():
                raise ValueError('Number of subpopulations mismatch: %d in population '
                    '%d required for ExponentialGrowthModel.' % (pop.numSubPop(), len(size)))
            elif all([self._isNamedSize(x) for x in named_size]):
                # matching number of subpopulations, ...
                new_size = [x[0] for x in named_size]
                # replace None with exsiting size
                new_size = [y if x is None else x for x,y in zip(new_size, pop.subPopSizes())]
                # convert float to int
                new_size = [int(x*y) if isinstance(x, float) else x for x,y in zip(new_size, pop.subPopSizes())]
                # now resize
                pop.resize(new_size, propagate=True)
                for idx, (s,n) in enumerate(named_size):
                    if n != '':
                        pop.setSubPopName(n, idx)
            else:
                # this is a more complex resize method because it can resize and split
                # if a nested list is passed
                new_size = []
                new_names = []
                split_sizes = []
                for idx, (x, y) in enumerate(zip(named_size, pop.subPopSizes())):
                    if isinstance(x[0], int):
                        new_size.append(x[0])
                        new_names.append(x[1])
                    elif isinstance(x[0], float):
                        new_size.append(int(x[0]*y))
                        new_names.append(x[1])
                    elif x[0] is None:
                        new_size.append(y)
                        new_names.append(x[1])
                    else:  # a list
                        split_sizes.insert(0, [idx])
                        for z in x:
                            if isinstance(z[0], int):
                                split_sizes[0].append(z[0])
                            elif sys.version_info.major == 2 and isinstance(z[0], long):
                                split_sizes[0].append(z[0])
                            elif isinstance(z[0], float):
                                split_sizes[0].append(int(z[0]*y))
                            elif z[0] is None:
                                split_sizes[0].append(y)
                            else:
                                raise ValueError('Invalid size %s' % named_size)
                        new_size.append(sum(split_sizes[0][1:]))
                        new_names.append('')
                # resize and rename
                pop.resize(new_size, propagate=True)
                for idx, name in enumerate(new_names):
                    if name != '':
                        pop.setSubPopName(name, idx)
                # handle split
                indexes = [i for i, x in enumerate(named_size) if not self._isNamedSize(x)]
                indexes.reverse()
                for item in split_sizes:
                    idx = item[0]
                    new_size = item[1:]
                    names = [x[1] for x in named_size[idx]]
                    pop.splitSubPop(idx, new_size, names if any([x != '' for x in names]) else [])
        else:
            # now, if the passed population does not have any subpopulation, 
            # we can merge or split ...
            if len(named_size) == 1:
                # integer is size
                if isinstance(named_size[0][0], int):
                    pop.resize(named_size[0][0], propagate=True)
                # float is proportion
                elif isinstance(named_size[0][0], float):
                    pop.resize(int(named_size[0][0] * pop.popSize()), propagate=True)
                # None is unchanged
                if named_size[0][1] != '':
                    pop.setSubPopName(named_size[0][1], 0)
            else:
                # we need to split ...
                if not all([self._isNamedSize(x) for x in named_size]):
                    # cannot have nested population size in this case.
                    raise ValueError('Cannot fit population with size %s to size %s' %
                        (pop.subPopSizes(), named_size))
                # split subpopulations
                new_size = [x[0] for x in named_size]
                # convert None to size
                new_size = [pop.popSize() if x is None else x for x in new_size]
                # convert float to int
                new_size = [int(x*pop.popSize()) if isinstance(x, float) else x for x in new_size]
                #
                pop.resize(sum(new_size), propagate=True)
                pop.splitSubPop(0, new_size)
                for idx, (s,n) in enumerate(named_size):
                    if n != '':
                        pop.setSubPopName(n, idx)

    def _recordPopSize(self, pop):
        gen = pop.dvars().gen
        if (not hasattr(self, '_last_size')) or self._last_size != pop.subPopSizes():
            print('%d: %s' % (gen, 
                ', '.join(
                    ['%d%s' % (x, ' (%s)' % y if y else '') for x, y in \
                        zip(pop.subPopSizes(), pop.subPopNames())])
                ))
            self._last_size = pop.subPopSizes()
        #
        if self.draw_figure:
            sz = 0
            for idx, (s, n) in enumerate(zip(pop.subPopSizes(), pop.subPopNames())):
                if n == '':
                    n = str(idx)
                if n in self.pop_base:
                    sz = max(sz, self.pop_base[n])
                self.pop_base[n] = sz
                if n in self.pop_regions:
                    self.pop_regions[n] = np.append(self.pop_regions[n],
                        np.array([[gen, sz, gen, sz+s]]))
                else:
                    self.pop_regions[n] = np.array([gen, sz, gen, sz+s], 
                        dtype=np.uint64)
                sz += s
        return True

    def plot(self, filename='', title='', initSize=[]):
        '''Evolve a haploid population using a ``RandomSelection`` mating scheme
        using the demographic model. Print population size changes duringe evolution.
        An initial population size could be specified using parameter ``initSize``
        for a demographic model with dynamic initial population size. If a filename
        is specified and if matplotlib is available, this function draws a figure
        to depict the demographic model and save it to ``filename``. An optional
        ``title`` could be specified to the figure. Note that this function can
        not be plot demographic models that works for particular mating schemes
        (e.g. genotype dependent).'''
        if not self.init_size:
            if initSize:
                self.init_size = initSize
            else:
                raise ValueError('Specific self does not have a valid initial population size')
        if filename and not has_plotter:
            raise RuntimeError('This function requires module numpy and matplotlib')
        self.draw_figure = filename and has_plotter
        self.pop_regions = OrderedDict()
        self.pop_base = OrderedDict()
        #
        self._reset()
        if title:
            print(title)
        pop = Population(self.init_size, infoFields=self.info_fields, ploidy=1)
        pop.evolve(
            matingScheme=RandomSelection(subPopSize=self),
            postOps=PyOperator(self._recordPopSize),
            gen=self.num_gens
        )
        self._recordPopSize(pop)
        # 
        if self.draw_figure:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.xaxis.set_ticks_position('bottom')
            ax.yaxis.set_ticks_position('left')
            for name, region in self.pop_regions.items():
                region = region.reshape(region.size / 4, 4)
                points = np.append(region[:, 0:2],
                    region[::-1, 2:4], axis=0)
                plt.fill(points[:,0], points[:,1], label=name, linewidth=0, edgecolor='w')
            leg = plt.legend(loc=2)
            leg.draw_frame(False)
            if title:
                plt.title(title)
            plt.savefig(filename)
            plt.close()

    def _checkSize(self, pop, param):
        gen = pop.dvars().gen
        if gen - param in self.intended_size:
            sz = self.intended_size[gen - param]
            if isinstance(sz, int):
                sz = (sz,)
            else:
                sz = tuple(sz)
            if sz != pop.subPopSizes():
                raise ValueError('Mismatch population size at generation %s (with starting gen %s): observed=%s, intended=%s' % \
                    (gen - param, param, pop.subPopSizes(), sz))
        return True
        
    def _assertSize(self, sizes, initSize=[], startGen=0):
        '''This function is provided for testing purpose.
        '''
        self.intended_size = sizes
        pop = Population(size=initSize if initSize else self.init_size,
            infoFields=self.info_fields)
        pop.dvars().gen = startGen
        pop.evolve(
            matingScheme=RandomSelection(subPopSize=self),
            postOps=PyOperator(self._checkSize, param=startGen),
            finalOps=PyOperator(self._checkSize, param=startGen),
            gen=self.num_gens
        )

    def _expIntepolate(self, N0, NT, T, x, T0=0):
        '''x=0, ... T-1
        '''
        if x == T-1:
            return NT
        elif x >= T:
            raise ValueError('Generation number %d out of bound (0<= t < %d is expected'
                % (x, T))
        else:
            return int(round(math.exp(((x+1-T0)*math.log(NT) + (T-x-1)*math.log(N0))/(T-T0))))

    def _linearIntepolate(self, N0, NT, T, x, T0=0):
        '''x=0, ... T-1
        '''
        if x == T-1:
            return NT
        elif x >= T:
            raise ValueError('Generation number %d out of bound (0<= t < %d is expected)'
                % (x, T))
        else:
            return int(round(((x+1-T0)*NT + (T-x-1)*N0)/(T-T0)))

    def _setup(self, pop):
        return True

    def _save_size(self, gen, sz):
        if self.size_cache:
            prev = [x for x in self.size_cache.keys() if x < gen]
            if prev and self.size_cache[max(prev)] == sz:
                return sz
        self.size_cache[gen] = sz
        return sz

    def _cached_size(self, gen):
        if gen in self.size_cache:
            return self.size_cache[gen]
        if not self.size_cache:
            raise RuntimeError('Failed to determine size for generation {}'
                    .format(gen))
        # if we look further, keep contant size
        if gen > max(self.size_cache.keys()):
            return self.size_cache[max(self.size_cache.keys())]
        prev = [x for x in self.size_cache.keys() if x < gen]
        if prev:
            return self.size_cache[max(prev)]
        else:
            raise RuntimeError('Failed to determine size for generation {}'
                    .format(gen))

    def __call__(self, pop):
        # When calling the demographic function, there are two quite separate scenarios
        #
        # 1. The demographic function is called sequentially. When a demographic model
        #   is initialized, it is considered part of its own generation zero. There can
        #   be two cases, the first one for initialization, the other one for instant
        #   population change (in the case of InstantChangeModel).
        #
        # 2. When the demographic function is called randomly, only a previously evolved
        #   generation is allowed. This is because many demographic models depend on
        #   size of previous generations to determine new population size, which makes
        #   jumping forward impossible.
        # 
        # In the case of multi-model, random access will not call fitSize for any
        # intermediate steps.
        # 
        # the first time this demographic function is called
        self._use_cached = False
        if not hasattr(self, '_start_gen'):
            self._reset()
            self._start_gen = pop.dvars().gen
            self._last_gen = pop.dvars().gen
            # resize populations if necessary
            self._fitToSize(pop, self._raw_init_size)
            # by this time, we should know the initial population size
            self.init_size = pop.subPopSizes()
            # then we can set up model if the model depends on initial
            # population size
            self._setup(pop)
        elif pop.dvars().gen != self._last_gen + 1:
            self._use_cached = True
            return self._cached_size(pop.dvars().gen)
        #
        self._gen = pop.dvars().gen - self._start_gen
        self._last_gen = pop.dvars().gen
        #
        pop.dvars()._gen = self._gen
        pop.dvars()._num_gens = self.num_gens
        for op in self.ops:
            if not op.apply(pop):
                self._reset()
                return []
        if '_expected_size' in pop.vars():
            return self._save_size(pop.dvars().gen, pop.vars().pop('_expected_size'))
        else:
            return self._save_size(pop.dvars().gen, pop.subPopSizes())

