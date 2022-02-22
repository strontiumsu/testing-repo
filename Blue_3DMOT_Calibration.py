# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 19:37:10 2022

@author: sr
"""


from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461 import*
from HCDL import* 

class Blue_3DMOT_calibration(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        #self.HC=HCDL(self)
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        self.BB.set_atten()
        #self.HC.set_atten()
        
        
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()
        
        
    
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        #self.HC.init_aoms()
        self.Detect.prep_datasets()
        #self.HC.set_lock_DP_aom_frequency(0)
        
        for ii in range(len(self.BB.MOT3DDP_AOM_frequency.sequence)):
           self.Detect.arm()
           
           delay(500*ms)
           self.BB.set_MOT3DDP_aom_frequency(ii)
           self.MC.Blackman_ramp_up()
           self.MC.flat()
           
           with parallel:
               self.MC.Blackman_ramp_down()
           
               self.Detect.trigger_camera()            
           
           
           self.Detect.acquire()
           self.Detect.transfer_image(ii)
           self.Detect.disarm()
        
        delay(500*ms)
        self.MC.Zero_current()    
        #self.Detect.clean_up()