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
        self.nova = _NovaTech(self)
        self.setattr_device("ttl0")
        
    def prepare(self):
        self.nova.set_freq(0,5*1e6)
        self.nova.set_gain(1,0.5)
        
        self.nova.table_init()
        ind = 0
        for _ in range(10):
            self.nova.table_write(ind, 50, 800, 50, 800)
            self.nova.table_write(ind+1, 0, 200, 1, 200)
            ind += 2
        self.nova.table_start()

    @kernel
    def run(self):
        self.core.reset()
        self.ttl0.output()
        self.ttl0.on()
        delay(100*ms)
        for _ in range(20):
            self.ttl0.off()
            delay(1*ms)
            self.ttl0.on()
            delay(10*ms)


        
        