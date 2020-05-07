"""
Unit tests for the diffusion module.
"""
import unittest
import numpy as np
import stochrare.dynamics.diffusion as diffusion

class TestDynamics(unittest.TestCase):
    def setUp(self):
        self.oup = diffusion.OrnsteinUhlenbeck(0, 1, 1, 2, deterministic=True)
        self.wiener = diffusion.Wiener(2, D=0.5, deterministic=True)

    def test_properties(self):
        self.assertEqual(self.oup.D0, 1)
        self.assertEqual(self.oup.mu, 0)
        self.assertEqual(self.oup.theta, 1)
        np.testing.assert_allclose(self.oup.diffusion(np.array([1, 1]), 0),
                                   np.array([[np.sqrt(2), 0], [0, np.sqrt(2)]]))
        self.oup.D0 = 0.5
        np.testing.assert_allclose(self.oup.diffusion(np.array([1, 1]), 0),
                                   np.array([[1, 0], [0, 1]]))
        np.testing.assert_allclose(self.oup.drift(np.array([1, 1]), 0), np.array([-1, -1]))
        self.oup.theta = 2
        np.testing.assert_allclose(self.oup.drift(np.array([1, 1]), 0), np.array([-2, -2]))
        self.oup.mu = np.array([1, 1])
        np.testing.assert_allclose(self.oup.drift(np.array([1, 1]), 0), np.array([0, 0]))
        self.oup.D0 = 1
        self.oup.theta = 1
        self.oup.mu = 0

    def test_wiener_potential(self):
        data = np.ones(10)
        np.testing.assert_array_equal(diffusion.Wiener.potential(data), np.zeros_like(data))
        data = np.ones((10, 10))
        np.testing.assert_array_equal(self.wiener.potential(data), np.zeros_like(data))

    def test_update(self):
        dw = np.random.normal(size=self.wiener.dimension)
        x = np.zeros(self.wiener.dimension)
        np.testing.assert_array_equal(self.wiener.update(x, 0, dw=dw), dw)

    def test_integrate_brownian_path(self):
        num = 4
        dim = 2
        ratio = 3

        dw_wrong_shape = np.array([range(1,11), range(11,1,-1)]).transpose()
        with self.assertRaises(ValueError):
            diffusion.DiffusionProcess._integrate_brownian_path(dw_wrong_shape, num, dim, ratio)

        dw_correct_shape = np.array([range(1,10), range(10,1,-1)]).transpose()
        integrated_dw = diffusion.DiffusionProcess._integrate_brownian_path(dw_correct_shape, num, dim, ratio)
        solution_array = np.array([[6,27],[15,18], [24,9]])
        np.testing.assert_array_equal(integrated_dw, solution_array)

    def test_trajectory_same_timestep(self):
        dt_brownian = 1e-5
        diff = lambda x, t: np.array([[x[0], 0], [0, x[1]]], dtype=np.float32)
        model = diffusion.DiffusionProcess(lambda x, t: 2*x, diff, deterministic=True)
        brownian_path = self.wiener.trajectory(np.array([0., 0.]), 0., T=0.1, dt=dt_brownian)
        traj_exact1 = np.exp(1.5*brownian_path[0]+brownian_path[1][:, 0])
        traj_exact2 = np.exp(1.5*brownian_path[0]+brownian_path[1][:, 1])
        traj = model.trajectory(np.array([1., 1.]), 0., T=0.1, dt=dt_brownian,
                                brownian_path=brownian_path, precision=np.float32)
        np.testing.assert_allclose(traj[1][:, 0], traj_exact1, rtol=1e-2)
        np.testing.assert_allclose(traj[1][:, 1], traj_exact2, rtol=1e-2)

    def test_trajectory_lower_timestep(self):
        dt_brownian = 1e-5
        diff = lambda x, t: np.array([[x[0], 0], [0, x[1]]], dtype=np.float32)
        model = diffusion.DiffusionProcess(lambda x, t: 2*x, diff, deterministic=True)
        brownian_path = self.wiener.trajectory(np.array([0., 0.]), 0., T=0.1, dt=dt_brownian)
        traj_exact1 = np.exp(1.5*brownian_path[0]+brownian_path[1][:, 0])
        traj_exact2 = np.exp(1.5*brownian_path[0]+brownian_path[1][:, 1])
        traj = model.trajectory(np.array([1., 1.]), 0., T=0.1, dt=2*dt_brownian,
                                brownian_path=brownian_path, precision=np.float32)
        np.testing.assert_allclose(traj[1][:, 0], traj_exact1[::2], rtol=1e-2)
        np.testing.assert_allclose(traj[1][:, 1], traj_exact2[::2], rtol=1e-2)

    def test_trajectory_generator(self):
        traj = np.array([x for t, x in self.oup.trajectory_generator(np.array([0, 0]), 0,
                                                                     100, dt=0.01)])
        _, x = self.oup.trajectory(np.array([0, 0]), 0, dt=0.01, T=1)
        np.testing.assert_allclose(x, traj, rtol=1e-5)

if __name__ == "__main__":
    unittest.main()
