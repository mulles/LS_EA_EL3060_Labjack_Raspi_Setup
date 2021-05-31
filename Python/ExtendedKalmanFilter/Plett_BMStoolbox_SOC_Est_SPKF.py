import numpy as np
from scipy import linalg

# --------------------------------------------------------------------
# Step 1c: system output prediction
# --------------------------------------------------------------------
Ya_minus = np.zeros((1,2*na+1))
I = etaI
if abs(I) >= Q/100: Isign = np.sign(I)

for j in range(2*na+1):
Ya_minus[0,j] = Model.OCVfromSOCtemp(Xa_minus[-1,j],T) + M*Xa_minus[numpoles,j] + M0*Isign\
            - R@Xa_minus[:numpoles,j] - R0*I\
            + Xa_plus[-1,j]  # sensor noise

y_hat = Ya_minus@Wfact

# --------------------------------------------------------------------
# Step 2a: estimator gain matrix
# --------------------------------------------------------------------

# Calcualte the covariance of predicted output
y_tilde = Ya_minus - np.repeat(y_hat,2*na+1,axis=1)
Covy = y_tilde@np.diag(Wfact.T[0])@y_tilde.T

# Calcualte the covariance of predicted states and output
Covxy = x_tilde@np.diag(Wfact.T[0])@y_tilde.T

L = Covxy/Covy

# --------------------------------------------------------------------
# Step 2b: state estimate measurement update
# --------------------------------------------------------------------

r = V-y_hat

# When sensor faults heppen, discard the output measurements
if r**2 > 100*Covy: L[:] = 0

x_hat = x_hat + L*r

# Make sure z estimate is within a reasonable range
x_hat[-1] = min(1.05,max(-0.05,x_hat[-1]))

z_hat = x_hat[-1]

# --------------------------------------------------------------------
# Step 2c: error covariance measurement update
# --------------------------------------------------------------------
Covx = Covx - L@Covy@L.T

# Higham's method make sure the covirance is at least semi-positive definite
_,s,vh = linalg.svd(Covx)
HH = vh.T@np.diag(s)@vh
Covx = (Covx+Covx.T+HH+HH.T)/4

# Bumping up the covariance of states helps KF regain the track of actual states
if r**2 > 4*Covy:
print('Bumping Covavriance Matrix of States')
Covx[-1,-1] = Covx[-1,-1]*Qbump

Varz = Covx[-1,-1]

# Update SPKFdata
SPKFData.I = i
SPKFData.Isign = Isign
SPKFData.x_hat = x_hat
SPKFData.Covx = Covx
return z_hat, Varz, SPKFData
