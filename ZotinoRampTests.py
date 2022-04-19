# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 15:32:35 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    
from ZotinoRampClass import* 


class ZotinoRampTests(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Zot=ZotinoRamp(self)

        
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.Zot.Linear_ramp_profile()

        
    @kernel    
    def run(self):
        
        self.core.reset()
        self.Zot.init_DAC()
        
        # Main loop
        for ii in range(10000):
           
           #delay(300*ms)
           self.Zot.Linear_ramp()
         
        delay(100*ms)   
        self.Zot.zero_dac()  
