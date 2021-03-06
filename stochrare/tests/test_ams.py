"""
Unit tests for the ams module.
"""
import unittest
import numpy as np
import stochrare.dynamics.diffusion1d as diffusion1d
import stochrare.rare.ams as ams

class TestAMS(unittest.TestCase):

    def test_getlevel(self):
        data = np.random.random(100)
        data[10] = 2.
        algo = ams.TAMS(None, (lambda t, x: x), 10.)
        self.assertEqual(algo.getlevel(np.arange(100), data), 2.0)

    def test_crossingtime(self):
        data = np.random.random(100)
        data[10] = 2.
        algo = ams.TAMS(None, (lambda t, x: x), 10.)
        self.assertEqual(algo.getcrossingtime(1.5, np.arange(100), data), (10, 2.0))

    def test_resample(self):
        told = np.linspace(0, 1, 101)
        xold = np.random.random(101)
        algo = ams.TAMS(diffusion1d.OrnsteinUhlenbeck1D(0, 1, 0.5), (lambda t, x: x), 1.)
        tnew, xnew = algo.resample(told[51], xold[51], told, xold, dt=0.01)
        np.testing.assert_allclose(xold[:52], xnew[:52])
        np.testing.assert_allclose(told, tnew)

    def test_selectams(self):
        levels = np.array([0.5, 1.1, 0.2, 0.6, 0.2, 0.5])
        np.testing.assert_array_equal(ams.TAMS.selectionstep(levels[:-2], npart=1)[0], [2])
        np.testing.assert_array_equal(ams.TAMS.selectionstep(levels, npart=1)[0], [2, 4])
        np.testing.assert_array_equal(ams.TAMS.selectionstep(levels[:-2], npart=2)[0], [0, 2])
        np.testing.assert_array_equal(ams.TAMS.selectionstep(levels[:-1], npart=2)[0], [0, 2, 4])
        np.testing.assert_array_equal(ams.TAMS.selectionstep(levels, npart=2)[0], [0, 2, 4, 5])
        np.testing.assert_array_equal(ams.TAMS.selectionstep(levels, npart=3)[0], [0, 2, 3, 4, 5])
        np.testing.assert_array_equal(ams.TAMS.selectionstep(levels, npart=4)[0], [])
        np.testing.assert_array_equal(ams.TAMS.selectionstep(levels, npart=5)[0], [])

    def test_initialize(self):
        algo = ams.TAMS(diffusion1d.OrnsteinUhlenbeck1D(0, 1, 0.5), (lambda t, x: x), 1.)
        algo.initialize_ensemble(10, dt=0.01)
        self.assertEqual(algo._weight, 1)
        self.assertEqual(algo._levels.size, 10)
        for ind in range(10):
            np.testing.assert_allclose(algo._ensemble[ind][0], np.linspace(0., 1.0, num=101))
            self.assertEqual(algo._ensemble[ind][0].size, algo._ensemble[ind][1].size)

    def test_mutateams(self):
        algo = ams.TAMS(diffusion1d.OrnsteinUhlenbeck1D(0, 1, 0.5), (lambda t, x: x), 1.)
        algo.initialize_ensemble(10, dt=0.01)
        kill, survive = algo.selectionstep(algo._levels)
        algo.mutationstep(kill, survive, dt=0.01)
        self.assertEqual(algo._weight, 1-float(kill.size)/10)


if __name__ == "__main__":
    unittest.main()
