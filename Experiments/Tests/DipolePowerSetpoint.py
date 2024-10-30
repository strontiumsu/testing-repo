# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 14:09:47 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
   


class DipolePowerSetpoint_exp(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")
        
        
        self.setattr_argument("Dipole_Power_On",NumberValue(0.5,min=0.0,max=2.0, ndecimals=4),"DAC")
        self.setattr_argument("Dipole_Power_Off",NumberValue(0.01,min=0.0,max=2.0, ndecimals=4),"DAC")

         
    @kernel
    def run(self):
             
        self.core.reset()
        self.dac_0.init()
        delay(500*ms)
        
        for _ in range(100):
            self.dac_0.write_dac(3,self.Dipole_Power_On)
            self.dac_0.load()
            delay(5*ms)
            
            self.dac_0.write_dac(3,self.Dipole_Power_Off)
            self.dac_0.load()
            delay(5*ms)
            
            
        self.dac_0.write_dac(3,self.Dipole_Power_On)
        self.dac_0.load()

           
            
                       


             
       
        
   
                        