from __future__ import division
import math
import numpy as np
import random
#import scipy.cluster.vq as vq
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.cm
from mpl_toolkits.mplot3d import Axes3D
import time
from scipy import interpolate
import pickle

interp1d = interpolate.interp1d

norm = np.linalg.norm
exp = math.exp
log = math.log
pi = math.pi
sqrt = math.sqrt
inner = np.inner
#npexp = np.vectorize(math.exp)
npexp = np.exp

def F(x, z, a):
    #xmzovera = [(x-z)/a for i in range(len(x))]
    d = len(x)

    #grad = F*(-0.5)*2*(x-z)/a**2 = F*(-(x-z))/a**2
    return exp(-0.5*norm((x-z)/a)**2)/(2*pi*a**2)**(d/2)

def npF(x, z, a, ax=0):
    #xmzovera = [(x-z)/a for i in range(len(x))]
    d = len(x)

    #grad = F*(-0.5)*2*(x-z)/a**2 = F*(-(x-z))/a**2
    return npexp(-0.5*norm((x-z)/a, axis=ax)**2)/(2*pi*a**2)**(d/2)

def kernel(X, z, a):
    #used for kernel density estimation. Note that the density used here is a Gaussian of variance a^2.
    d = len(X[0])
    n = len(X)

    return sum([(exp(-0.5*norm((x-z)/a)**2)/(2*pi*a**2)**(d/2))/n for x in X]) 

def alpha(X, z):
    d = len(X[0])
    eps = 0.0001 #TODO LIST THIS
    npoints = 10 #TODO LIST THIS, typically set this to 10
    #L = 5

    #a = (npoints/(n+m)*(1/(kernel(X,z,1)+eps) + 1/(kernel(Y, z, 1)+eps)))**(1/d)
    a = (npoints/(n)*(1/(kernel(X,z,1)+eps) + 1/(exp(-(norm(z)**2)/2)+eps)))**(1/d)

    # 1/(2*pi)*sum([exp(-0.5*norm(y-z)**2) for y in Y])))**(1/d)
    
    a = max(a, 1)

    return a

def I(d):
    if d == 1:
        return 1/2
    elif d == 0:
        return sqrt(pi)/2
    else:
        return (d-1)/2*I(d-2)

def S(d):
    if d == 0:
        return 2
    else:
        return 2*pi*V(d-1)

def V(d):
    if d == 0:
        return 1
    else:
        return S(d-1)/d





def MakeCenters(num, d, flag=1):
    #print 'MakeCenters d =', d#REMOVABLE
    # FLAG SETS HOW CENTERS WILL BE CONSTRUCTED

    if flag == 1:
        # Uniformly distributed in box (-4,4) in each dimension
        Z = np.random.uniform(-4,4,(num,d))

    elif flag == 2:
        # Normally distributed points about origin
        # Poor for 1 center. after 900 runs stagnates at a square, even with large cap on betaMax 
        Z = np.random.multivariate_normal(mean,cov,num)
        
    elif flag == 3:
        # Alternate between sample points and normally distributed points
        # Works for 1 center, np = 50, and betamax 100, though a little poor
        indices = np.random.randint(n,size=num) 
        Z = np.empty([num,d])
        for i in range(num):
            choice = np.random.randint(2)
            if choice == 0:
                Z[i] = XAn[indices[i]]
            else:
                Z[i] = np.random.multivariate_normal(mean,cov)

        # Construct centers by K-Means (Doesn't work at all)
        #[Z, dist] = vq.kmeans(XAn, num)

    return Z



def Alphas(X, Z):
    centers = Z.shape[0]
    A = [0.]*centers

    for i,z in enumerate(Z):
        A[i] = alpha(X, z)

    return A



def BCD(A):

    centers = len(A)

    B = [0.]*centers
    C = [0.]*centers
    D = [[0.]*centers for row in range(centers)]
    
    for i in range(centers):
        B[i] = sqrt(1+1/(A[i]**2))
        C[i] = sqrt(1/2+1/(A[i]**2))
            
    for i in range(centers):
        for j in range(centers):
            D[i][j] = 1/2+1/(2*A[i]**2)+1/(2*A[j]**2)

    return (B, C, D)



def MakeG(X, Z, A, B):
    
    n, d = X.shape
    centers = Z.shape[0]
    #print 'MakeG d =', d#REMOVABLE

    Gx = np.zeros(centers)
    Gy = np.empty(centers)
    G = np.empty(centers)

    for i,z in enumerate(Z):
        for x in X:
            Gx[i] += F(x, z, A[i])

        Gx[i] = Gx[i]/n
        Gy[i] = 1/((2*pi)**(d/2)*A[i]**d)*1/(B[i]**d)*exp(norm(z)**2*(1/(2*A[i]**4*B[i]**2)-1/(2*A[i]**2)))
        G[i] = Gx[i] - Gy[i]

    return G
    
    

def Hessian(Z, A, C, D):
    d = len(Z[0])
    #print 'Hessian d =', d#REMOVABLE
    centers = Z.shape[0]

    H = np.empty((centers, centers))

    for i in range(centers):
        for j in range(i):
            zi = Z[i]
            zj = Z[j]
            z = zi/A[i]**2 + zj/A[j]**2
            H[i][j] = (1/((2*pi)**(3*d/2)*A[i]**(d+2)*A[j]**(d+2))
                *(S(d)/D[i][j]**(d+2)*I(d+1)+inner(z/(2*D[i][j]**2)-zi,z/(2*D[i][j]**2)-zj)*(pi/D[i][j]**2)**(d/2))
                *exp(norm(zi)**2/(4*D[i][j]**2*A[i]**4)+norm(zj)**2/(4*D[i][j]**2*A[j]**4)
                +inner(zi,zj)/(2*D[i][j]**2*A[i]**2*A[j]**2)
                -norm(zi)**2/(2*A[i]**2)-norm(zj)**2/(2*A[j]**2)))
            H[j][i] = H[i][j]

##            for y in Y:#
##                gradFi = F(y, zi, aMC[i])*-(y-zi)/(aMC[i]**2)#
##                gradFj = F(y, zj, aMC[j])*-(y-zj)/(aMC[j]**2)#
##                HMC[i][j] += inner(gradFi, gradFj)#
##
##                HMC[j][i] = HMC[i][j]#

    for i, z in enumerate(Z):
        H[i][i] = (1/((2*pi)**(3*d/2)*A[i]**(2*d+4))
            *exp((1/(A[i]**4*C[i]**2)-1/A[i]**2)*norm(z)**2)
            *1/(C[i]**d)*(S(d)/(C[i]**2)*I(d+1)+(1/(A[i]**2*C[i]**2)-1)**2*norm(z)**2*pi**(d/2)))

    return H



def MakeBetas(G, Hinv, betaMax, betaCap, d=0, A=[]):
    
    #print 'MakeBetas d =', d#REMOVABLE
    betas = -np.dot(Hinv, G)

    if (d == 1) and (len(A) == 1):
        #TODO NOTE THIS ONLY TAKES CARE OF CASE OF 1 CENTER
        bound = sqrt(2*pi)*A[0]**3
        if abs(betas[0]) > bound:
            betas = np.sign(betas)*bound

    if norm(betas) > betaMax and betaCap:
        b = betaMax/norm(betas)
        betas = betas*b

    return betas



def Update(X, Z, beta, a):

    n, d = X.shape

    for k in range(n):
        x = X[k]
        for i, z in enumerate(Z):
            X[k] += beta[i]*F(x, z, a[i])*(-(x-z)/a[i]**2)

#    Delta = np.zeros(X.shape)
#
#    for i, z in enumerate(Z):
#        Delta += beta[i]*npF(X, z, a[i], ax=1)*(-(X-z)/a[i]**2)
#
#    X += Delta



def TransportCycle(X, centers, CenterFlag, betaMax, betaCap=True, grid=None, stepsize=0):

    n, d = X.shape

    Z = MakeCenters(centers, d, CenterFlag)
    a = Alphas(X, Z)
    B, C, D = BCD(a)

    G = MakeG(X, Z, a, B)

    #Newton's Method
    if stepsize == 0:
        H = Hessian(Z, a, C, D)
        Hinv = np.linalg.inv(H)
        betas = MakeBetas(G, Hinv, betaMax, betaCap, d, a)
    #Gradient Descent
    else:
        betas = -G*stepsize

    Update(X, Z, betas, a)

########TODO CONSTRUCT JACOBIAN MATRIX (before or after update)###########

    if not grid is None:
        Update(grid, Z, betas, a)

    return (Z, a)

#################################################################
#################################################################
#################################################################

def PlotsOld(X, Z, a):
    
    n, d = X.shape
    if d == 1:
        plt.hist(X, 50)
#        plt.xlim((xmin, xmax))
    else:
        plt.scatter(X[:,0],X[:,1])
        plt.scatter(Z[:,0],Z[:,1],c='violet')
#        plt.xlim((xmin, xmax))
#        plt.ylim((ymin, ymax))
        for i,z in enumerate(Z):
            az.add_patch(plt.Circle(z, radius = a[i], fill=False, color='g'))



def Plots(XAn, Y, XAnOld, Z, aAn):

    (n,d) = XAn.shape

    plt.figure(1)
    plt.clf()
    plt.suptitle('t = %i' %t)
    plt.subplot(321)
    if d == 1:
        plt.hist(X, 50)
    else:
        plt.scatter(X[:,0], X[:,1], 20, color, marker='o', cmap=matplotlib.cm.jet, norm=Norm)
#        plt.scatter(Xstarold[:,0],Xstarold[:,1],c='black')
    plt.subplot(322)
    if d == 1:
        plt.hist(Y, 50)
        xmin, xmax = plt.xlim()
    else:
        plt.scatter(Y[:,0],Y[:,1])
        xmin, xmax = plt.xlim()
        ymin, ymax = plt.ylim()
    az = plt.subplot(323)
    if d == 1:
        plt.hist(XAnOld, 50)
        plt.xlim((xmin, xmax))
    else:
        plt.scatter(XAnOld[:,0],XAnOld[:,1])
        plt.scatter(Z[:,0],Z[:,1],c='violet')
        plt.xlim((xmin, xmax))
        plt.ylim((ymin, ymax))
        for i,z in enumerate(Z):
            az.add_patch(plt.Circle(z, radius = aAn[i], fill=False, color='g'))
    ax = plt.subplot(324)
    plt.title('Analytical')
    if d == 1:
        plt.xlim((xmin, xmax))
        plt.hist(XAn, 50, normed=1)
        plt.plot(Z,[0]*centers,'ro')
        grid = np.linspace(xmin, xmax, 50)
        plt.plot(grid, 1/sqrt(2*pi)*np.exp(-grid**2/2),'--r')
    else:
        plt.xlim((xmin, xmax))
        plt.ylim((ymin, ymax))
        plt.scatter(XAn[:,0], XAn[:,1], 20, color, marker='o', cmap=matplotlib.cm.jet, norm=Norm)
#        plt.scatter(Xstar[:,0],Xstar[:,1],c='black')
        plt.scatter(Z[:,0],Z[:,1],c='violet')
        for i,z in enumerate(Z):
            ax.add_patch(plt.Circle(z, radius = aAn[i], fill=False, color='g'))

    #text = raw_input()
    plt.draw()
    plt.draw()


##            plt.subplot(325)
##            if d == 1:
##                plt.hist(XMC, 50)
##                plt.plot(Z,[0]*centers,'ro')
##            else:
##                plt.scatter(XMC[:,0],XMC[:,1])

#            plt.figure(2)
#            plt.clf()
#            plt.subplot(121)
#            plt.title('KL Divergence')
#            plt.plot(KL[:t+1])
#            plt.draw()

            #plt.show(block=False)
            #text = raw_input()
            #plt.close()

        #if text == 'break':
        #    break




###########################################################
###########################################################
###########################################################


if __name__ == "__main__":

    print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'

    #np.random.seed(4)
    #random.seed(0)
    plt.ion()
    plt.figure(1, figsize=(8,9))
    plt.show()

    d = 2  # dimensions
    n = 500 # number of x samples
    m = n # number of y samples
    T = 5000 # number of iterations
    eps = 1e-7
    centers = 5 
    betaMax = 500
    betaCap = True
    CenterFlag = 1 # CenterFlag determines how centers are distributed
    plotSkip = 50 # Plot after plotSkip iterations
    plotOn = True


    X = np.random.uniform(0,1,(n,d))
    #X = np.random.multivariate_normal([-1,-1],[[2,0],[0,2]],n)
    #X = np.concatenate((np.random.multivariate_normal([-1],[[0.25]],250), np.random.multivariate_normal([0.5],[[.25]],250)))

    n = len(X)
    m = n

    XMC = np.copy(X)#
    XAn = np.copy(X)
    mean = np.zeros(d)
    cov = np.eye(d)
    Target = np.random.multivariate_normal(mean,cov,n)
#    Xstar = np.random.uniform(0,1,(nstar,d))
#    Xstarold = np.array(Xstar)

    color = np.array([norm(x - [0.5,0.5]) for x in X])
    Norm = matplotlib.colors.Normalize(vmin = np.min(color), vmax = np.max(color), clip = False)
    timing = [0,0,0,0]

    for t in range(T + 1):

########TODO Use XAnOld to plot old points or plot old points with XAn at this time
        if (t-1)% plotSkip == 0 or t == 0:
            XAnOld = np.copy(XAn)

        if True:
            Z, aAn = TransportCycle(XAn, centers, CenterFlag, betaMax, betaCap, stepsize=exp(-t**2/100.))
        else:
            Z = MakeCenters(centers, d, CenterFlag)
            aAn = Alphas(XAn, Z)
            B, C, D = BCD(aAn)

##############PLOTS OLD POINTS HERE
#        if plotOn and (t% plotSkip == 0):
#            PlotsOld(XAn, Z, aAn)
#
#        GxAn = np.zeros(centers)
#        GyAn = np.empty(centers)
#        GAn = np.empty(centers)
#        
#        for i,z in enumerate(Z):
#            for x in XAn:
#                GxAn[i] += F(x, z, aAn[i])
#
#            GxAn[i] = GxAn[i]/n
#            GyAn[i] = 1/((2*pi)**(d/2)*aAn[i]**d)*1/(B[i]**d)*exp(norm(z)**2*(1/(2*aAn[i]**4*B[i]**2)-1/(2*aAn[i]**2)))
#            GAn[i] = GxAn[i] - GyAn[i]


            T0 = time.time()
            GAn = MakeG(XAn, Z, aAn, B)

            T1 = time.time()
            HAn = Hessian(Z, aAn, C, D)
            Hinv = np.linalg.inv(HAn)

            T2 = time.time()
            betaAn = MakeBetas(GAn, Hinv, betaMax, betaCap)

            T3 = time.time()
            Update(XAn, Z, betaAn, aAn)
            T4 = time.time()

########TODO CONSTRUCT JACOBIAN MATRIX (before or after update)###########
            timing[0] += T1 - T0
            timing[1] += T2 - T1
            timing[2] += T3 - T2
            timing[3] += T4 - T3

########TODO COMPUTE COST OF TRANSPORT###############


        print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
        print 't =', t
        print 'Z =', Z
        print 'aAn =', aAn
        #print 'GAn = ', GAn
        #print 'GxAn =', GxAn
        #print 'Gy analytical =', GyAn
        #print 'H analytical  =', HAn
        #print 'Analytical beta =', betaAn
        #print 'Norm beta =', norm(betaAn)
        #print 'Timing:', timing

        if plotOn and (t% plotSkip == 0):
            Plots(XAn, Target, XAnOld, Z, aAn)
            if t == T:
                raw_input()


    #print X
    Y0 = norm(X, axis=1)**2+0.1*np.random.randn(n)
    #Y0 = npexp(X).reshape(n,)+0.1*np.random.randn(n)
    #Y0 = np.arcsin(X)+0.03*np.random.randn(n,1)
    Y0 = Y0.reshape(n,1)
    Y = np.copy(Y0)
    #Y = np.random.uniform(0,1,(n, 1))
    print 'min:', np.min(Y)
    print 'max:', np.max(Y)
    grid0 = np.arange(np.min(Y)-4, np.max(Y)+4, .05)
    print 'grid0 =', grid0
    YGrid = np.copy(grid0.reshape(len(grid0),1))
    #print "YGrid =", YGrid
    plt.clf()
    plt.suptitle('Y, t = 0')
    plt.hist(Y, 50)
    plt.show()
    raw_input('Press Enter to continue')
    #plt.scatter(YGrid.reshape(-1),np.zeros(len(YGrid)))
    for t in range(1,T+1):
        Z, a = TransportCycle(Y, 1, 1, 500, grid=YGrid) 
        if plotOn and (t% plotSkip ==0):
            plt.clf()
            plt.suptitle('Y, t = %d' %t)
            plt.hist(Y, 50)
            plt.plot([0],[0],'ro')
            plt.draw()
            plt.draw()
            #raw_input()
        #plt.scatter(YGrid.reshape(-1),np.zeros(len(YGrid)))

#, color, marker='o', cmap=matplotlib.cm.jet, norm=Norm)
    grid1 = YGrid.reshape(len(grid0))
    print 'grid1 =', grid1

    terp = interp1d(grid1, grid0, assume_sorted=True)

    W = np.linalg.lstsq(XAn, Y)[0]
    Xreg = np.dot(XAn, W)
    Xregterp = terp(Xreg)
    Xregterp = Xregterp.reshape(n,1)

    #Plot transported Y against the LSQReg W*Xtransported
    plt.clf()
    plt.subplot(111)
    plt.title('Y vs. f(X) (regressed)')
    plt.plot(Y, Xreg, 'o')
    plt.show()
    raw_input()

    #Plot original Y against interpolated W*Xtransported
    plt.clf()
    plt.subplot(111)
    plt.title('y vs. interpolated f(X)')
    plt.plot(Y0, Xregterp, 'o')
    xmin, xmax = plt.xlim()
    xline = np.arange(xmin, xmax, 0.1)
    plt.plot(xline, xline, 'k--') 
    plt.show()
    raw_input()

    #Plot X against interpolated W*Xtransported
    plt.clf()
    plt.subplot(111)
    plt.plot(X, Y0, 'o')
    plt.title('x vs. y and x vs. interpolated W*X')
    plt.plot(X, Xregterp, 'go')
    plt.show()
    raw_input()

    #Distributions of transported Y and W*Xtransported
    plt.clf()
    plt.subplot(211)
    plt.title('Y')
    plt.hist(Y, 50)
    plt.subplot(212)
    plt.title('Xreg')
    plt.hist(Xreg, 50)
    plt.show()
    raw_input()

    #Distributions of original Y and interpolated W*Xtransported
    plt.clf()
    plt.subplot(211)
    plt.title('y')
    plt.hist(Y0, 50)
    plt.subplot(212)
    plt.title('interpolated f(X)')
    plt.hist(Xregterp, 50)
    plt.plot([0],[0],'ro')
    plt.show()
    raw_input()

    print norm(np.dot(XAn, W) - Y)**2

#    costcheck = []
#    for i in range(5000):
#        print i,
#        fakeX = np.random.multivariate_normal(mean, cov, n)
#        fakeY = np.random.multivariate_normal(np.zeros(1), np.eye(1), n)
#        
#        fakeW = np.linalg.lstsq(XAn, Y)[0]
#        costcheck.append(norm(np.dot(fakeX,fakeW) - Y)**2)
#        print '\r',
#    print 'avg = ', sum(costcheck)/len(costcheck)




