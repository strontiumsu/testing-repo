# -*- coding: utf-8 -*-
"""
Created on Sun Jun  6 12:33:41 2021

@author: sr
"""

import numpy as np
import numpy as np
import matplotlib.pyplot as plt


tramp=40*1e-3
tflat=50*1e-3
A=2.0  # Amplitude 
npoints=51

def blackman(tramp,tflat,A,npoints):
     
    #Ensure odd number of points
    if npoints %2 == 0:
        npoints+=1
        
        
    w=np.blackman(npoints+1)  
    # repeat middle element
    w1=np.insert(w,int((npoints)/2),w[int((npoints)/2)])

    dt=tramp/npoints/2
     
    t=[]
    T=0
    t.append(0)
    for ii in range(npoints+1):
        if ii<npoints/2:
           T+=dt 
           ii+=1
        elif ii==(npoints+1)/2:
          
            T+=tflat
            ii+=1
        else:
          T+=dt
          ii+=1
        t.append(T)

    return A*w1, t

a,t=blackman(tramp,tflat,A,npoints)

plt.plot(t,a)

