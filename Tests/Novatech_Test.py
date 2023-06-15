# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 09:32:14 2023

@author: sr
"""
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")
import time 

from artiq.experiment import delay, kernel, ms, EnvExperiment, us, now_mu, parallel, sequential
from NovaTechClass import _NovaTech

class NovaTech_Test_Exp(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        # self.nova = _NovaTech(self)
        self.setattr_device("ttl4") 
        
    def prepare(self):
        # self.nova.setup()
        pass
    # 
    
    @kernel
    def run(self):
        self.core.reset()
        delay(10*ms)
        self.ttl4.on()                
        delay(10*ms)
        self.ttl4.off()
        # delay(20*ms) 
        # self.core.wait_until_mu(now_mu())
        # self.nova.set_gain(0,0)
        # time.sleep(150*1e-3) 
        # self.nova.set_gain(0,0.5)
        


        
        