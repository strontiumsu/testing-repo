# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 15:20:32 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np     

class ZotinoRamp(EnvExperiment):
      
    
    def build(self):
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")
        #self.setattr_argument("Pulse_duration",
        #    Scannable(default=[NoScan(60*1e-3), RangeScan(10*1e-3, 30*1e-3, 10, randomize=False)],scale=1e-3,
        #              unit="ms"),"MOT_driver")
        self.setattr_argument("Zotino_channel", NumberValue(0,min=0,max=11),"Zotino Ramp")
        self.setattr_argument("Start_value", NumberValue(0.0,min=-10.0,max=10.0,
                      unit="V"),"Zotino Ramp")
        self.setattr_argument("End_Value",NumberValue(0.0,min=-10.0,max=10.0,
                      unit="V"),"Zotino Ramp") # Pulse amplitude         
        self.setattr_argument("Zotino_t_ramp",NumberValue(50.0*1e-3,min=0.0*1e-3,max=100.00*1e-3,scale=1e-3,
                      unit="ms"),"Zotino Ramp") # ramp duration
        self.setattr_argument("Npoints",NumberValue(30,min=0,max=100.00),"Zotino Ramp") # number of discret points in each ramp
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
        
        
    def Linear_ramp_profile(self):
    
        #if self.Npoints % 2 == 0:
        #    self.Npoints += 1
            #print('changed to odd number of points')
            #print(self.Npoints)
        
        
        self.w=np.linspace(self.Start_value,self.End_Value,num = int(self.Npoints), endpoint=True)  
        self.dt=self.Zotino_t_ramp/(self.Npoints)
        
        
    @kernel    
    def zero_dac(self):
        self.dac_0.write_dac(int(self.Zotino_channel),0.0)
        self.dac_0.load()
        
    @kernel    
    def set_dac(self,A):
        self.dac_0.write_dac(int(self.Zotino_channel),A)
        self.dac_0.load()    
    
    @kernel
    def init_DAC(self):
        self.dac_0.init()
        
    @kernel         
    def Linear_ramp(self):
        
        
        for ii in range(int(self.Npoints)):                      
            delay(self.dt)
            self.dac_0.write_dac(int(self.Zotino_channel),self.w[ii])
            self.dac_0.load()
            ii+=1
    
    # @kernel         
    # def Blackman_ramp_up(self):
        
    #     for ii in range(int(self.Npoints/2)):                      
    #                            delay(self.dt)
    #                            self.dac_0.write_dac(0,self.A*self.w[ii])
    #                            self.dac_0.load()
    #                            ii+=1
    
    
    
    # @kernel                    
    # def flat(self):
    #     delay(self.Pulse_fully_on_duration) 
    
    # @kernel                        
    # def Blackman_ramp_down(self):
    #     for ii in range(int(self.Npoints/2)):
    #                            delay(self.dt)
    #                            self.dac_0.write_dac(0,self.A * self.w[int(self.Npoints/2+ii)])
    #                            self.dac_0.load()
    #                            ii+=1
                               
    # @kernel                        
    # def Blackman_ramp_down_from_to(self, top, bottom):
    #     for ii in range(int(self.Npoints/2)):
    #                            delay(self.dt)
    #                            self.dac_0.write_dac(0,(top - bottom) * self.w[int(self.Npoints/2+ii)] + bottom)
    #                            self.dac_0.load()
    #                            ii+=1  
                            
                               
    # @kernel                        
    # def Linear_ramp(self, bottom, top, time):
    #     delt = time/(self.Npoints/2)
    #     for ii in range(int(self.Npoints/2)):
    #                            delay(self.dt)
    #                            self.dac_0.write_dac(0,bottom + (top-bottom)/time*ii*delt )
    #                            self.dac_0.load()
    #                           ii+=1  