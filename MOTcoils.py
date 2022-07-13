# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 11:16:52 2022

@author: sr

Functions to make smooth pulses for MOT coils

"""

       
from artiq.experiment import *
import numpy as np     

class MOTcoils(EnvExperiment):
      
    
    def build(self):
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")
        #self.setattr_argument("Pulse_duration",
        #    Scannable(default=[NoScan(60*1e-3), RangeScan(10*1e-3, 30*1e-3, 10, randomize=False)],scale=1e-3,
        #              unit="ms"),"MOT_driver")
        self.setattr_argument("Pulse_fully_on_duration", NumberValue(200.0*1e-3,min=10.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"MOT coil driver")         
        self.setattr_argument("t_ramp",NumberValue(50.0*1e-3,min=1.0*1e-3,max=100.00*1e-3,scale=1e-3,
                      unit="ms"),"MOT coil driver") # ramp duration
        self.setattr_argument("Current_amplitude",NumberValue(0.0,min=0.0,max=10.0,
                      unit="A"),"MOT coil driver") # Pulse amplitude
        self.setattr_argument("Npoints",NumberValue(30,min=0,max=100.00),"MOT coil driver") # number of discret points in each ramp
        #self.setattr_argument("duty cycle",NumberValue(3,min=0,max=100.00),"MOT_driver") # number of discret points in each ramp
        #self.conversion = 19.4
                  
    def Blackman_pulse_profile(self):
    
        if self.Npoints % 2 == 0:
            self.Npoints += 1
            print('changed to odd number of points')
            print(self.Npoints)
        
        
        self.w=np.blackman(self.Npoints+1)  
        self.A=self.Current_amplitude
        self.dt=self.t_ramp/(self.Npoints/2)    
        
        
    @kernel    
    def Zero_current(self):
        self.dac_0.write_dac(0,0.0)
        self.dac_0.load()
        
    @kernel    
    def Set_current(self,A):
        self.dac_0.write_dac(0,A)
        self.dac_0.load()    
    
    @kernel
    def init_DAC(self):
        self.dac_0.init()
        
       
    
    @kernel         
    def Blackman_ramp_up(self):
        
        for ii in range(int(self.Npoints/2)+1):                      
                               delay(self.dt)
                               self.dac_0.write_dac(0,self.A*self.w[ii])
                               self.dac_0.load()
                               ii+=1
    
    
    
    @kernel                    
    def flat(self):
        delay(self.Pulse_fully_on_duration) 
    
    @kernel                        
    def Blackman_ramp_down(self):
        for ii in range(int(self.Npoints/2)):
                               delay(self.dt)
                               self.dac_0.write_dac(0,self.A * self.w[int(self.Npoints/2+1+ii)])
                               self.dac_0.load()
                               ii+=1
                               
    @kernel                        
    def Blackman_ramp_down_from_to(self, top, bottom):
        for ii in range(int(self.Npoints/2)):
                               delay(self.dt)
                               self.dac_0.write_dac(0,(top - bottom) * self.w[int(self.Npoints/2+ii+1)] + bottom)
                               self.dac_0.load()
                               ii+=1  
                            
                               
    @kernel                        
    def Linear_ramp(self, bottom, top, time,num_pts):
        delt = time/(num_pts)
        for ii in range(int(num_pts)):
                               delay(delt)
                               self.dac_0.write_dac(0,bottom + (top-bottom)/time*ii*delt )
                               self.dac_0.load()
                               ii+=1  

     

            
            
       