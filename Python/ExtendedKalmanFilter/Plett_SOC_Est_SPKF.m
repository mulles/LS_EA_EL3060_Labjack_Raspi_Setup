
#Initialize simulation variables
SigmaW= 1; # Process noise covariance
SigmaV= 2; # Sensor noise covariance
maxIter= 40;
xtrue= 2 +randn(1); # Initialize true system initial state

xhat= 2; # Initialize Kalman filter initial estimate

SigmaX= 1; # Initialize Kalman filter covariance
u= 0; # Unknown initial driving input: assume zero

# Reserve storage for variables we might want to plot/evaluate
xstore=zeros(maxIter+1,length(xtrue));
xstore(1,:) =xtrue;
xhatstore=zeros(maxIter,length(xhat));
SigmaXstore=zeros(maxIter,length(xhat)^2);
for k= 1:maxIter,
# EKF Step 0: Compute Ahat, Bhat
# Note: For this example, x(k+1) = sqrt(5+x(k)) + w(k)
Ahat= 0.5/sqrt(5+xhat);Bhat= 1;
# EKF Step 1a: State estimate time update
# Note: You need to insert your system's f(...) equation here
xhat=sqrt(5+xhat);
# EKF Step 1b: Error covariance time update
SigmaX=Ahat*SigmaX*Ahat' +Bhat*SigmaW*Bhat';
# [Implied operation of system in background, with
# input signal u, and output signal y]
w=chol(SigmaW)'*randn(1);
v=chol(SigmaV)'*randn(1);
ytrue=xtrue^3 +v; # y is based on present x and u
xtrue=sqrt(5+xtrue) +w;  # future x is based on present u

# EKF Step 1c: Estimate system output
# Note: You need to insert your system's h(...) equation here
Chat= 3*xhat^2;
Dhat= 1;
yhat=xhat^3;
# EKF Step 2a: Compute Kalman gain matrix
SigmaY=Chat*SigmaX*Chat' +Dhat*SigmaV*Dhat';
L=SigmaX*Chat'/SigmaY;
# EKF Step 2b: State estimate measurement update
xhat=xhat+L*(ytrue-yhat);
xhat=max(-5,xhat); # don't get square root of negative xhat!

# EKF Step 2c: Error covariance measurement update

SigmaX=SigmaX-L*SigmaY*L';
[~,S,V] =svd(SigmaX);
HH=V*S*V';
SigmaX= (SigmaX+SigmaX' +HH+HH')/4;
# Help to keep robust
# [Store information for evaluation/plotting purposes]
xstore(k+1,:) =xtrue;
xhatstore(k,:) =xhat;
SigmaXstore(k,:) = (SigmaX(:))';
end;
figure(1);
clf;
t=0:maxIter-1;
plot(t,xstore(1:maxIter),'k-',t,xhatstore,'b--', ...
  t,xhatstore+3*sqrt(SigmaXstore),'m-.',...
  t,xhatstore-3*sqrt(SigmaXstore),'m-.');
grid;
legend('true','estimate','bounds');
xlabel('Iteration');
ylabel('State');
title('Extended Kalman filter in action');
figure(2);

clf;
plot(t,xstore(1:maxIter)-xhatstore,'b-',t, ...
  3*sqrt(SigmaXstore),'m--',t,-3*sqrt(SigmaXstore),'m--');
grid;
legend('Error','bounds',0);
title('EKF Error with bounds');
xlabel('Iteration');
ylabel('Estimation error');
