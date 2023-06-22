# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 09:32:14 2023

@author: sr
"""
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")
import time 

from artiq.experiment import delay, kernel, ms, EnvExperiment, us, now_mu, parallel, sequential, NumberValue
from NovaTechClass import _NovaTech

class NovaTech_Test_Exp(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.nova = _NovaTech(self)
        self.setattr_device("ttl0")
        
        self.setattr_argument("scale_Zeeman", NumberValue(500, min=0.0, max=1024.0), "AOMs")
        self.setattr_argument("scale_2D", NumberValue(500, min=0.0, max=1024.0), "AOMs")
        self.setattr_argument("freq_Zeeman", NumberValue(210*1e6, min=50*1e6, max=350*1e6, scale=1e6, unit='MHz'), "AOMs")
        self.setattr_argument("freq_2D", NumberValue(195*1e6, min=50*1e6, max=350*1e6, scale=1e6, unit='MHz'), "AOMs")
        
    def prepare(self):
        # self.nova.set_freq(1,self.freq_2D/2)
        # self.nova.set_gain(1,self.scale_2D)  
        # self.nova.set_freq(0,self.freq_Zeeman/2)
        # self.nova.set_gain(0,self.scale_Zeeman)
        
        self.nova.table_init()
        ind = 0
        for _ in range(1):
            self.nova.table_write(ind, self.freq_Zeeman/1e6/2, self.scale_Zeeman,self.freq_2D/1e6/2, self.scale_2D)
            self.nova.table_write(ind+1, 0, 0, 0, 0)
            ind += 2
        self.nova.table_start()

    @kernel
    def run(self):
        self.core.reset()



        
        