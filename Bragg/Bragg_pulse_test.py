# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 11:02:56 2023

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, BooleanValue, kernel, ms, NumberValue, delay

# imports
import numpy as np
from BraggClass import _Bragg


class Bragg_pulse_test(EnvExperiment):
    """
    Bragg_pulse_test
    This experiment uses the CoolingClass to control the relevant AOMs and MOT
    coils to pulse the blue MOT off and on. 
    
    parameters:
        <all parameters inherited from CoolingClass>
        pulses: number of times to pulse the coils on
        pulse_duration: how long to keep the pulse on
        wait_time: how long to wait between pulses        
    """    
    def build(self):
        self.setattr_device("core")
        self.Bragg = _Bragg(self)
        
        
        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("pulse_duration", NumberValue(200.0*1e-3,min=10.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")  
        self.setattr_argument("wait_time", NumberValue(1000.0*1e-3,min=10.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")  
        
    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.Bragg.prepare_aoms()
        
    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.Bragg.init_aoms(on=False)
        
        self.Bragg.AOMs_on(['Bragg1','Bragg2'])
        
        # # pulse using the given parameters
        # for _ in range(int(self.pulses)):
        #     self.Bragg.bragg_pulse(self.pulse_duration)
        #     delay(self.wait_time)
 