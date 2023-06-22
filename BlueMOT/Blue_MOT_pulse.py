# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 10:03:56 2023

@author: E. Porter
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, BooleanValue, kernel, ms, NumberValue, delay, parallel, sequential, RTIOUnderflow

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera


class Blue_MOT_pulse_exp(EnvExperiment):
    """
    Blue_MOT_pulse_exp
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
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        
        
        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("wait_time", NumberValue(1000.0*1e-3,min=10.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("image", BooleanValue(False),"parameters")
        
    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms(int(self.pulses*1.5))
        self.MOTs.prepare_coils()
        
        if self.image: self.Camera.camera_init()
        
    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        delay(5*ms)
        if self.image: self.MOTs.take_background_image_exp(self.Camera)
        
        
        
        # pulse using the given parameters
        for _ in range(int(self.pulses)):
                         
            if self.image:self.Camera.arm()
        
            delay(200*ms)     
            self.MOTs.bMOT_load()
            if self.image: self.MOTs.take_MOT_image(self.Camera)
            delay(10*ms)

            self.MOTs.Blackman_ramp_down()
            self.MOTs.atom_source_off()
            self.MOTs.AOMs_off(["3D", "3P0_repump", "3P2_repump"])
            delay(50*ms)    
       
            if self.image: self.Camera.process_image(bg_sub=True)
           
            delay(self.wait_time)
            
            
            
            

