# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 15:54:07 2022

@author: sr
"""
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
import numpy as np    
from DetectionClass import _Detection
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689

class Blue_MOT_calibration(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=_Detection(self)
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        self.BB.set_atten()
        
        
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()
        
        
    
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.Detect.prep_datasets()
        
        for ii in range(len(self.HC.DP_AOM_frequency.sequence)):
           self.Detect.arm()
           
           delay(500*ms)
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