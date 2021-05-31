import numpy as np
from scipy import linalg


class SPKF_Data:
# ----------------------------------------------------------------------------------------------------------------
# This is a class containing necessary data to proceed state estimate through SOC_Est_SPKF function
# ----------------------------------------------------------------------------------------------------------------
    
    def __init__(self):
        
        self.I = None              # prior input
        self.Isign = None          # prior input
        self.x_hat = None          # prior states (iR,h,z)
        
        self.Covx = None           # prior state covariance
        self.Covw = None           # process noise
        self.Covv = None           # sensor noise
        
        self.nx = None             # number of states
        self.nw = None             # number of process noise
        self.nv = None             # number of sensor noise
        self.na = None             # number of states, process noise and sensor noise
        
        self.gamma = None          # weighting factor
        self.Wfact = None          # weighting factors
        
        self.Qbump = None          # bumping factor
     
    
    def setup(self,I,Isign,iR,h,z,Covx,Covw,Covv,Qbump):
        # Initiate the data structure
        
        self.I = I          
        self.Isign = Isign
        self.x_hat = np.concatenate((iR,h,z))
        self.x_hat.shape = (len(self.x_hat),1)
        
        self.Covx = Covx
        self.Covw = Covw
        self.Covv = Covv
        
        self.nx = len(Covx)
        self.nw = len(Covw)
        self.nv = len(Covv)
        self.na = self.nx + self.nw + self.nv
        
        # Specify weighting factors for Central Difference Kalman Filter (CDKF)
        self.gamma = 3**0.5  # for Gaussian random variables
        alpha0 = (self.gamma**2 - self.na)/(self.gamma**2)
        alphai = 1/(2*self.gamma**2)
        self.Wfact = alphai*np.ones((2*self.na+1,1))
        self.Wfact[0] = alpha0
        
        self.Qbump = Qbump


def SOC_Est_SPKF(T,i,v,delta_t,SPKFData,Model):
# ----------------------------------------------------------------------------------------------------------------
# This function estimates states through SPKF with an ESC cell model.
# Input: temperature(T), current(i), voltage(v), sampling interval(delta_t), SPKFdata(SPKFData), ESC model(Model)
# Output: SOC estimate(z_hat), variance of SOC estimate(Varz), SPKFdata update(SPKFData)
# ----------------------------------------------------------------------------------------------------------------
    
    # Load model parameters
    eta = Model.getParam('etaParam',T)
    Q  = Model.getParam('QParam',T)
    G  = Model.getParam('GParam',T)
    M  = Model.getParam('MParam',T)
    M0 = Model.getParam('M0Param',T)
    RC = Model.getParam('RCParam',T)
    R  = Model.getParam('RParam',T)
    R0 = Model.getParam('R0Param',T)
    numpoles = Model.getParam('numpoles',T)
    
    # Load SPKFdata
    I = SPKFData.I
    Isign = SPKFData.Isign
    x_hat = SPKFData.x_hat
    Covx = SPKFData.Covx
    Covw = SPKFData.Covw
    Covv = SPKFData.Covv
    nx = SPKFData.nx
    nw = SPKFData.nw
    nv = SPKFData.nv
    na = SPKFData.na
    gamma = SPKFData.gamma
    Wfact = SPKFData.Wfact
    
    
    etaI = i
    if i < 0: etaI = etaI*eta
    V = v
    
    # --------------------------------------------------------------------
    # Step 1a: state prediction time update
    # --------------------------------------------------------------------
    
    # Calculate SigmaX points
    xa_hat = np.concatenate((x_hat,np.zeros((nw+nv,1))))
    
    try:
        Covxa = linalg.block_diag(Covx,Covw,Covv)
        sqrtCovxa = np.linalg.cholesky(Covxa)
    except:
        print('Cholesky error.  Recovering...')
        Covx = np.diag(np.maximum(abs(np.diag(Covx)),np.diag(Covw)))
        #Covx = np.diag(abs(np.diag(Covx)))
        Covxa = linalg.block_diag(Covx,Covw,Covv)
        sqrtCovxa = np.linalg.cholesky(Covxa)
    
    Xa_plus = np.repeat(xa_hat,2*na+1,axis=1)
    Xa_plus[:,1:1+na] = Xa_plus[:,1:1+na] + gamma*sqrtCovxa
    Xa_plus[:,-na:] = Xa_plus[:,-na:] - gamma*sqrtCovxa
    
    # Calculate predicted SigmaX points
    Xa_minus = np.zeros((nx,2*na+1))

    for j in range(2*na+1):
        Ij = I + Xa_plus[nx,j]  # process noise
        
        RCfact = np.exp(-delta_t/RC)
        Xa_minus[:numpoles,j] = RCfact*Xa_plus[:numpoles,j] + (1-RCfact)*Ij
        
        AH = np.exp(-abs(G*Ij*delta_t/(3600*Q)))
        Xa_minus[numpoles,j] = AH*Xa_plus[numpoles,j] + (AH-1)*np.sign(Ij)
        
        Xa_minus[numpoles+1,j] = Xa_plus[numpoles+1,j] - (Ij*delta_t/(3600*Q))       
    
    # Calcualte state prediction
    x_hat = Xa_minus@Wfact
    
    # Make sure h and z are withun a reasonable range
    x_hat[numpoles] = min(1,max(-1,x_hat[numpoles]))
    x_hat[-1] = min(1.05,max(-0.05,x_hat[-1]))

    # --------------------------------------------------------------------
    # Step 1b: error covariance time update
    # --------------------------------------------------------------------
    
    # Calcualte the covariance of predicted states
    x_tilde = Xa_minus - np.repeat(x_hat,2*na+1,axis=1)
    Covx = x_tilde@np.diag(Wfact.T[0])@x_tilde.T
    
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
