# Copyright (c) $today.year.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Creative Commons-GNU General Public Llicense 2.0, as "non-commercial/sharealike".  You may use, modify, and distribute this software for non-commercial purposes, and you must distribute any modifications under the same license.  
#
# For detailed license terms, see:
# http://creativecommons.org/licenses/GPL/2.0/

# this module exists so that we can do logging functions which are usable as PyOperators in simuPOP.
"""
.. module:: simlogging
    :platform: Unix, Windows
    :synopsis: Extensions to the native python logging mechanism for use in simuPOP simulations.

.. moduleauthor:: Mark E. Madsen <mark@madsenlab.org>

"""

import logging as log


def logGenerationCount(pop, param):
        """Operator for logging the generation count using simuPOP's PyOperator hook.

        Args:

            implicitly called with a Population object by simuPOP, requires no other arguments

        Returns:

            Boolean true (required of all PyOperator methods)

    """

        gen = pop.dvars().gen
        log.info("Generation: %s", gen)
        return True

