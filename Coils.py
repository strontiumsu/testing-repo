# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 11:16:52 2022

@author: sr

Functions to make smooth pulses for MOT coils

"""

       
from artiq.experiment import *
import numpy as np     

class MotCoils(EnvExperiment):
#     def __init__(self):
    
    def build(self):
    # MOTdriver duration
        #self.setattr_argument("Pulse_duration",
        #    Scannable(default=[NoScan(60*1e-3), RangeScan(10*1e-3, 30*1e-3, 10, randomize=False)],scale=1e-3,
        #              unit="ms"),"MOT_driver")
        self.setattr_argument("Pulse_fully_on_duration", NumberValue(0.0,min=-4.0,max=4.00,scale=1e-3,
                      unit="ms"),"MOT coil driver")         
        self.setattr_argument("t_ramp",NumberValue(0.0,min=-4.0,max=4.00,scale=1e-3,
                      unit="ms"),"MOT coil driver") # ramp duration
        self.setattr_argument("Current_amplitude",NumberValue(0.0,min=-4.0,max=20.00,
                      unit="A"),"MOT coil driver") # Pulse amplitude
        self.setattr_argument("Npoints",NumberValue(3,min=0,max=100.00),"MOT coil driver") # number of discret points in each ramp
        #self.setattr_argument("duty cycle",NumberValue(3,min=0,max=100.00),"MOT_driver") # number of discret points in each ramp
                  
    def Blackman_pulse_profile(self):
    
        if self.Npoints % 2 == 0:
            self.Npoints += 1
            print('changed to odd number of points')
            print(self.Npoints)
        
        
        w=np.blackman(npts+1)  
        w1=np.insert(w,int((self.Npoints)/2),w[int((self.Npoints)/2)])
        self.dt=self.MOT_t_ramp/(self.Npoints/2)    
        
        
        
    def Zero_current(self):
        self.dac_0.write_dac(0,0.0)
        self.dac_0.load()
            
    def Blackman_ramp_up(self):
        delay(10*ms)
        for ii in range(int(self.Npoints/2)):                      
                               delay(self.dt)
                               self.dac_0.write_dac(0,current * w[ii])
                               self.dac_0.load()
                               ii+=1
                               
    def Blackman_ramp_down(self):
        for ii in range(int(self.Npoints/2)):
                               delay(self.dt)
                               self.dac_0.write_dac(0,current * w1[self.Npoints/2+ii])
                               self.dac_0.load()
                               ii+=1

     

            
                          
            
       