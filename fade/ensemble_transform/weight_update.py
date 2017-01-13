""" weight update calculation for an ensemble and observations - NB: Independent gaussian observation error! """

from __future__ import division

from __future__ import absolute_import

from firedrake import *

from firedrake.mg.utils import get_level

import numpy as np

from fade.observations import *
from fade.localisation import *

from pyop2.profiling import timed_stage


def weight_update(ensemble, weights, observation_operator, sigma, r_loc=0):

    """ Calculates the importance weights of ensemble members around assumed gaussian observations

        :arg ensemble: list of :class:`Function`s in the ensemble
        :type ensemble: tuple / list

        :arg weights: list of current weight :class:`Function`s
        :type weights: tuple / list

        :arg observation_operator: the :class:`Observations` for the assimilation problem - updated
                                   with observations and coordinates for the current assimilation step
        :type observation_operator: :class:`Observations`

        :arg sigma: variance of independent observation error
        :type sigma: float

        Optional Arguments:

        :arg r_loc: radius of coarsening localisation for importance weight update. Default: 0
        :type r_loc: int

    """

    if len(ensemble) < 1:
        raise ValueError('ensemble cannot be indexed')
    if len(weights) < 1:
        raise ValueError('weights cannot be indexed')
    mesh = ensemble[0].function_space().mesh()

    # check that part of a hierarchy - so that one can coarsen localise
    hierarchy, lvl = get_level(mesh)
    if lvl is None:
        raise ValueError('mesh for ensemble members needs to be part of ' +
                         'hierarchy for coarsening loc')

    # function space
    fs = ensemble[0].function_space()

    n = len(ensemble)

    # difference in the observation space
    p = 2
    D = []
    for i in range(n):

        with timed_stage("Calculating observation squared differences"):
            weights[i].dat.data[:] = np.log(weights[i].dat.data[:])
            weights[i].assign((-(1 / (2 * sigma)) *
                               observation_operator.difference(ensemble[i], p)) + weights[i])

        D.append(weights[i])

    # now implement coarsening localisation and find weights
    with timed_stage("Coarsening localisation"):
        W = []
        for i in range(n):
            W.append(CoarseningLocalisation(D[i], r_loc))

    # Find Gaussian likelihood
    with timed_stage("Likelihood calculation"):
        for j in range(n):
            W[j].dat.data[:] = (1 / np.sqrt(2 * np.pi * sigma)) * np.exp(W[j].dat.data[:])

    # normalize and check weights
    t = Function(fs)
    c = Function(fs)
    for j in range(n):
        t.dat.data[:] += W[j].dat.data[:]

    with timed_stage("Checking weights are normalized"):
        for k in range(n):
            W[k].dat.data[:] = np.divide(W[k].dat.data[:], t.dat.data[:])
            c.dat.data[:] += W[k].dat.data[:]

        if np.max(np.abs(c.dat.data[:] - 1)) > 1e-3:
            raise ValueError('Weights dont add up to 1')

    return W