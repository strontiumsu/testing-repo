# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 11:19:09 2023

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/novatech409b-master")
import time 

from artiq.experiment import delay, kernel, ms, EnvExperiment, us, now_mu, parallel, sequential
import driver

class NovaTech_table_test_Exp(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        # self.nova = _NovaTech(self)
        self.setattr_device("ttl1") 
        self.dev = driver.Novatech409B("COM5")
        
    def prepare(self):
        
        self.dev.set_gain(0, 0.2)
        self.dev.set_freq(0, 10*1e6)
        
        self.dev.table_init()
        ind = 0
        for _ in range(2):
            self.dev.table_write(ind, 50, 800, 50, 1023)
            self.dev.table_write(ind+1, 0, 0, 50, 1023)
            ind += 2
        self.dev.table_start()
    
    @kernel
    def run(self):
        self.core.reset()
        self.ttl1.output()
        
        for _ in range(20):
            self.ttl1.pulse(1*ms)
            delay(200*ms)
        
        
        
        self.core.wait_until_mu(now_mu())
        self.dev.close()
        
