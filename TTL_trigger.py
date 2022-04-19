# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 15:34:33 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    


class TTL_trigger(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl4")
        
    @kernel    
    def run(self):
        self.core.reset()
        # Main loop
        for ii in range(10000):
            
            delay(20*ms)
            self.ttl4.on()
            delay(1*ms)
            self.ttl4.off()
            
            ii+=1
            