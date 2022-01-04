import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md

import numpy as np
from filterpy.kalman import UnscentedKalmanFilter
from filterpy.kalman import MerweScaledSigmaPoints
from filterpy.common import Q_discrete_white_noise


# Resource: https://filterpy.readthedocs.io/en/latest/kalman/UnscentedKalmanFilter.html

csvfilename_measurements = "SmallDataset.csv"


def fx(x, dt):
   # state transition function - predict next state based
   # on constant velocity model x_k+1 = sqrt(5+x_k) + w_k
   F = np.array([[1, dt, 0, 0],
                 [0, 1, 0, 0],
                 [0, 0, 1, dt],
                 [0, 0, 0, 1]], dtype=float)
   return np.dot(F, x)

def hx(x):
    # measurement function - convert state into a measurement
    # where measurements are [x_pos, y_pos]
    return np.array([x[0], x[2]])


dt = 1
 # create sigma points to use in the filter. This is standard for Gaussian processes
points = MerweScaledSigmaPoints(4, alpha=.1, beta=2., kappa=-1)

UKF = UnscentedKalmanFilter(dim_x=4, dim_z=2, dt=dt, fx=fx, hx=hx, points=points)
UKF.x = np.array([-1., 1., -1., 1]) # initial state
UKF.P *= 0.2 # initial uncertainty
z_std = 0.1
UKF.R = np.diag([z_std**2, z_std**2]) # 1 standard
UKF.Q = Q_discrete_white_noise(dim=2, dt=dt, var=0.01**2, block_size=2)

# Read measurements
df = pd.read_csv(csvfilename_measurements)
savedcoluwn = [df['Bat_V {device="mppt-1210-hus", name="V"}'], df['Bat_A {device="mppt-1210-hus", name="A"}'] ]  #you can also use df['column_name']
print(savedcoluwn)

zs = [[savedcoluwn[0][i], savedcoluwn[1][i]] for i in range(150)] # measurements
for z in zs:
   UKF.predict()
   UKF.update(z)
   print(UKF.x, 'log-likelihood', UKF.log_likelihood)
