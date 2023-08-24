# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 10:03:56 2023

@author: E. Porter
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *

# imports
import numpy as np
from CoolingClass import _Cooling



class Leak_Test_exp(EnvExperiment):
  
    def build(self):
        self.setattr_device("core")
        self.MOTs = _Cooling(self)

        
        
        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("pulse_duration", NumberValue(200.0*1e-3,min=10.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")  
        self.setattr_argument("wait_time", NumberValue(1000.0*1e-3,min=10.0*1e-3,max=20000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("on",BooleanValue(False),"Loading")
        
    def prepare(self):
        self.MOTs.prepare_aoms()
        
    @kernel
    def run(self):

        self.core.reset()
        self.MOTs.init_aoms(on=False)
        self.MOTs.init_ttls()
        if self.on:self.MOTs.AOMs_on(['3D'])
        else: self.MOTs.AOMs_off(['3D'])
            
        # delay(5*ms)

        
        for _ in range(int(self.pulses)):
            self.MOTs.push()
            #self.MOTs.ttl1.on()
            # self.MOTs.AOMs_on(['Probe'])
            # delay(self.wait_time)
            # self.MOTs.AOMs_off(['Probe'])
            # delay(self.wait_time)
            delay(self.wait_time)

            

