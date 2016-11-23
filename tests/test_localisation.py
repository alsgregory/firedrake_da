from __future__ import division

from __future__ import absolute_import

from firedrake import *

from firedrake_da import *

import numpy as np

import pytest


def test_localisation_single_cell_dg0():

    mesh = UnitIntervalMesh(1)

    fs = FunctionSpace(mesh, 'DG', 0)

    r_locs = [0, 1, 2]

    index = 0

    for r in r_locs:

        l = Localisation(fs, r, index)
        assert l.dat.data[index] == 1.0


def test_localisation_single_cell_cg1():

    mesh = UnitIntervalMesh(1)

    fs = FunctionSpace(mesh, 'CG', 1)

    r_locs = [0, 1, 2]

    index = 0

    for r in r_locs:

        l = Localisation(fs, r, index)
        assert l.dat.data[index] == 1.0


def test_localisation_double_cell_dg0():

    mesh = UnitIntervalMesh(2)

    fs = FunctionSpace(mesh, 'DG', 0)

    r_locs = [0, 1, 2]

    index = 0

    for r in r_locs:

        l = Localisation(fs, r, index)
        assert l.dat.data[index] == 1.0
        assert np.abs(l.dat.data[1] - (((2 ** r) - 1) / (2 ** r))) < 1e-5


def test_coarsening_localisation_single_cell_dg0():

    mesh = UnitIntervalMesh(1)

    mesh_hierarchy = MeshHierarchy(mesh, 3)

    r_loc = 2

    fs_hierarchy = tuple([FunctionSpace(m, 'DG', 0) for m in mesh_hierarchy])

    WLoc = Function(fs_hierarchy[-1]).assign(1.0)

    WLocNew = CoarseningLocalisation(WLoc, r_loc)

    assert norm(assemble(WLoc - WLocNew)) == 0


def test_coarsening_localisation_no_localisation():

    mesh = UnitIntervalMesh(1)

    mesh_hierarchy = MeshHierarchy(mesh, 3)

    r_loc = 0

    fs_hierarchy = tuple([FunctionSpace(m, 'DG', 0) for m in mesh_hierarchy])

    WLoc = Function(fs_hierarchy[-1])

    WLoc.dat.data[0] += 1.0

    WLocNew = CoarseningLocalisation(WLoc, r_loc)

    assert norm(assemble(WLoc - WLocNew)) == 0


def test_coarsening_localisation_no_hierarchy():

    mesh = UnitIntervalMesh(1)

    fs = FunctionSpace(mesh, 'DG', 0)

    r_locs = [0, 1]

    for r in r_locs:

        WLoc = Function(fs)

        WLoc.dat.data[0] += 1.0

        if r == 1:
            with pytest.raises(Exception):
                CoarseningLocalisation(WLoc, r)

        if r == 0:
            C = CoarseningLocalisation(WLoc, r)
            assert C == WLoc


if __name__ == "__main__":
    import os
    pytest.main(os.path.abspath(__file__))
