# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 11:17:41 2023

@author: E. Porter
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, kernel, ms,us, NumberValue, delay, parallel, now_mu,BooleanValue

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera


class Red_MOT_pulse_exp(EnvExperiment):
    """
    Red_MOT_pulse_exp
    This experiment uses the CoolingClass to control the relevant AOMs and MOT
    coils to pulse the Red MOT off and on, taking an image each time to display to the user 
    at detection.images.current_image. 
    
    parameters:
        <all parameters inherited from CoolingClass>
        <all parameters inherited from Detection2>
        pulses: number of times to pulse the red MOT
        wait_time: how long to wait between pulses
              
    """ 
    
    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("ttl0") # probe beam 
        self.setattr_device("ttl1") # 3D MOT beam
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        
        
        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("wait_time", NumberValue(1000.0*1e-3,min=10.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters") 
        self.setattr_argument("push_beam",BooleanValue(False),"Loading")

        
    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        
        # Initialize camera
        self.Camera.camera_init()
        

        
    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        delay(500*ms)
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)
        delay(50*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(500*ms)
        
        for _ in range(int(self.pulses)):
            self.Camera.arm()
            delay(200*ms)  
             
            self.MOTs.rMOT_pulse()
            if self.push_beam:
                self.MOTs.push()
            self.MOTs.take_MOT_image(self.Camera)
            self.MOTs.shutters_off(['3D'])
            delay(10*ms)
            
            
            
            delay(50*ms)
            self.Camera.process_image(bg_sub=True)
            delay(300*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(self.MOTs.AOMs)

            
            delay(self.wait_time)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        
        
        