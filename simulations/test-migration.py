#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import simuOpt
simuOpt.setOptions(alleleType='long',optimized=True,numThreads=4)
import simuPOP as sim

from simuPOP.utils import migrIslandRates
import random

print "threads: %s" % sim.moduleInfo()["threads"]

def demo(pop):
  # this function randomly split populations
  numSP = pop.numSubPop()
  if random.random() > 0.99:
      pop.splitSubPop(random.randint(0, numSP-1), [0.5, 0.5])
  return pop.subPopSizes()

def migr(pop):
  numSP = pop.numSubPop()
  sim.migrate(pop, migrIslandRates(0.01, numSP))
  return True

pop = sim.Population(10000, infoFields='migrate_to')
simu = sim.Simulator(pop, rep = 4)
simu.evolve(
    initOps=sim.InitSex(),
    preOps=[
        sim.PyOperator(func=migr),
        sim.Stat(popSize=True),
        sim.PyEval(r'"Gen %d:\t%s\n" % (gen, subPopSize)', step=100)
    ],
    matingScheme=sim.RandomMating(subPopSize=demo),
    gen = 1000
)