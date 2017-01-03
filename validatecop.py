#!/usr/bin/env python3
# to test cop parameters

from hyperellipsoid import hyperellipsoid
import numpy as np
import math
import COPparamsFs as cp
import matplotlib.pyplot as plt

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return(x, y)

test_hyp = False


if test_hyp:
    # test hyperellipsoid
    cnt = 0
    trls = 1000
    for ia in range(0,trls):
        # create test data
        coords = np.random.normal(0,1,(100,2))
        area, axes, angles, center, rot = hyperellipsoid(coords, show=False)
        # get new data point
        x = np.random.normal(0,1,1)
        y = np.random.normal(0,1,1)
        # test if in ellipse centred at (0,0) and whose axes are aligned to x & y axes
        if x**2/axes[0]**2 + y**2/axes[1]**2 <= 1:
            cnt += 1
    print(cnt/trls)

# test path length
nsamp = 2
# create data with known path length - length = 1 at each section
# create uniform random angles
angs = np.random.rand(nsamp) * 2 * math.pi
uvecs = np.transpose(np.array(pol2cart(1,angs)))
lgths = np.linalg.norm(uvecs, axis=1)
# lghts should all = 1...
print(lgths)
# get cumulative sum
tstdat = np.cumsum(uvecs, axis = 0)
# plt.plot(tstdat[:,0],tstdat[:,1],'ro-')
# plt.axes().set_aspect('equal')
# plt.show()
out = cp.pathl(tstdat)
print(out)
