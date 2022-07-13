# -*- coding: utf-8 -*-
"""
Created on Tue May 31 14:37:52 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class MOT_Scan(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")
    
        # 3D MOT coil DC set
        
        self.setattr_argument("Current_high",NumberValue(0.0,min=0.0,max=10.0,
                      unit="A"),"MOT_driver")
        self.setattr_argument("Current_low",NumberValue(0.0,min=0.0,max=10.0,
                      unit="A"),"MOT_driver")
        self.setattr_argument("Ramp_time",NumberValue(0.0,min=0.0,max=5000.0,
                      unit="ms"),"MOT_driver")
        self.setattr_argument("N_points",NumberValue(0.0,min=0.0,max=200),"MOT_driver")
       
        
        

    def prepare(self):
       self.Ahigh=self.Current_high       
       self.Alow=self.Current_low
       self.time = self.Ramp_time
       self.num_pts = self.N_points
                  
    @kernel
    def run(self):
            self.core.reset()
            self.dac_0.init()
            
            delay(10*ms)
            
            
            delt = self.time/(self.num_pts)
            for i in range(1000):
                self.dac_0.write_dac(0,self.Alow)
                self.dac_0.load()
                delay(self.time)
                for ii in range(int(self.num_pts)):
                                delay(delt)
                                self.dac_0.write_dac(0,self.Alow + (self.Ahigh-self.Alow)/self.time*ii*delt )
                                self.dac_0.load()
                                ii+=1 
                delay(200*ms)
                self.dac_0.write_dac(0,0.0)  
                self.dac_0.load()
                delay(self.time)            
                # self.dac_0.write_dac(0,self.Ahigh)
                # self.dac_0.load()
                # delay(100*ms)
                # self.dac_0.write_dac(0,self.Alow)
                # self.dac_0.load()
                # delay(100*ms)
            # self.dac_0.load()        
              