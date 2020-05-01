"""
Tools for time series analysis.
These tools should apply in particular to trajectories generated by stochastic processes
using the dynamics subpackage.
"""
import numpy as np

def running_mean(x, N):
    """
    Return the running mean of a time series.

    Parameters
    ----------
    x: ndarray (1D)
        The trajectory.
    N: int
        The window size.

    Returns
    -------
    xavg: ndarray (1D)
        If x has length n, then xavg has length n-N+1.
    """
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / N

def transitionrate(x, threshold, window=1):
    """
    Count the number of times a given trajectory goes across a given threshold.
    A typical use case is to study transitions from one attractor to the other.

    Parameters
    ----------
    x: ndarray (1D)
        The time series
    threshold: float
        The threshold (e.g. separating the two attractors)
    window (optional): int, default=1
        Averaging window for smoothing timeseries before computing transition rate.

    Returns
    -------
    lambda: float
        The transition rate.

    Notes
    -----
    Without smoothing (avg=1), the result should coincide with the number of items in the generator
    levelscrossing(x,0) when starting with the right transition,
    or that number +1 if we use the wrong isign in levelscrossing.
    """
    y = running_mean(x, window) if window > 1 else x
    return float(((y[1:]-threshold)*(y[:-1]-threshold) < 0).sum())/len(y)

def levelscrossing(x, threshold, sign=1):
    """
    Maps the stochastic process x(t) onto a stochastic process {t_i}
    where the 't_i's correspond to crossing levels +- c

    Parameters
    ----------
    x: ndarray (1D)
        The time series
    threshold: float
        The threshold (e.g. separating the two attractors)
    sign (optional): int, default=1
        The initial sign: detect transitions going up (sign=-1) or down (sign=1) first.

    Yields
    ------
    index: int
        The indices corresponding to the transitions.

    Notes
    -----
    This function is useful for transition between two states corresponding to two symmetric
    thresholds with opposite signs.
    """
    # By default we start by detecting the transition below the -c threshold
    if sign == 0:
        sign = 1
    if not abs(sign) == 1:
        sign /= abs(sign)
    for i in range(len(x)-1):
        if (threshold+sign*x[i]) > 0 and (threshold+sign*x[i+1]) < 0:
            sign *= -1
            yield i

def residencetimes(x, threshold):
    """
    Return the time spent in each of the attractors defined by the threshold.

    Parameters
    ----------
    x: ndarray (1D)
        The time series
    threshold: float
        The threshold (e.g. separating the two attractors)

    Returns
    -------
    residencetime: ndarray (1D)
        The time (number of samples) spent in each region between two transitions.

    Notes
    -----
    This function is useful for transition between two states corresponding to two symmetric
    thresholds with opposite signs.

    In the future the function should be modified to generate realizations of two random variables,
    corresponding to the time spent in each of the two regions.
    Mybe it should be done as a generator yielding a pair of residence times.
    """
    transtimes = np.fromiter(levelscrossing(x, threshold), int)
    return transtimes[1:]-transtimes[:-1]


def traj_fpt(M, *args):
    """
    Compute the first passage time for each trajectory given as argument.

    Parameters
    ----------
    M: float
        The threshold
    args: pairs t,x (ndarrays)
        The trajectories

    Yields
    ------
    t: float
        First-passage time for the trajectories
    """
    for tt, xx in args:
        for t, x in zip(tt, xx):
            if x > M:
                yield t
                break



def blockmaximum(traj, nblocks, mode='proba', modified=False, **kwargs):
    """
    Generate pairs (a, p(a)) (mode='proba') or (a, r(a)) (mode='returntime'),
    where p(a) is the probability to reach a and r(a) the corresponding return time (see below).

    Block maximum method.
    Given a timeseries X_t, we define the probability to reach a given threshold a over a time T:
    p(a) = Prob[max_{0 < t < T} X_t > a]
    Or equivalently, the return time of the even X_t > a: r(a)=T/p(a)

    To do so, we divide the input trajectory in same-size blocks and compute the maximum in each
    block. We sort the maxima in descending order and assign probability n/nblocks to the maximum
    of rank n: in the input timeseries, maximum n has been reached n times.

    Parameters
    ----------
    traj: ndarray (1D)
        The timeseries X_t
    nblocks: int
        The number of blocks. It should be chosen so that each block is larger than the
        correlation time of the timeseries, but we also want as many blocks as possible.
    mode: str
        'proba' (default) or 'returntime': determine whether to return probability
        or return time of the event X_t > a.
    modified: bool (default False)
        Use the modified version of the bock maximum estimator defined in
        Lestang, Ragone, Brehier, Herbert and Bouchet, J. Stat. Mech. 2018
    time: ndarray
        sampling times (default is just 0,1,2,...)

    Yields
    ------
    a, p: float, float
        The amplitude and associated probability (mode 'proba')
    a, r: float, float
        The amplitude and associated return time (mode 'returntime')
    """
    time = kwargs.get('time', np.arange(len(traj)))
    trajlen = float(time[-1]-time[0])
    blocklen = int(len(traj)/nblocks)
    blockmax = [np.max(traj[k*blocklen:(k+1)*blocklen]) for k in range(nblocks)]
    last = 0 if modified else None
    for cnt, maxi in enumerate(np.sort(blockmax)[:last:-1], 1):
        if mode == 'proba':
            yield maxi, float(cnt)/float(nblocks)
        else:
            yield maxi, -trajlen/(nblocks*np.log(1-float(cnt)/nblocks)) if modified else trajlen/cnt
