# -*- coding: utf-8 -*-
"""
Created on Mon Aug 22 11:06:21 2022

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

import numpy as np    
from DetectionClass import _Detection
from  artiq.language.environment import EnvExperiment
from artiq.language import scan, delay
from artiq.language.units import ms
from artiq.language.core import kernel

class CameraBugsTest(EnvExperiment):
    
    def build(self):
        self.setattr_device("core")
        self.Detect=_Detection(self)
        
        self.setattr_argument("Delay_duration",
            scan.Scannable(default=[scan.RangeScan(10.0*1e-3, 500.0*1e-3, 20, randomize=False),scan.NoScan(0.0)],scale=1e-3,
                      unit="ms"),"Loading")
        if not hasattr(self.Delay_duration,'sequence'):
            self.x=np.array([0,0])
        else:
            self.x=self.Delay_duration.sequence
        self.y=np.full(len(self.x), np.nan)
        
        
        
    def prepare(self):
        
        self.Detect.camera_init()
       
        
    @kernel    
    def run(self):
        self.core.reset()
        
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        # for ii in range(len(self.x)):
            
        #############
        # background image
        delay(300*ms) 
        self.Detect.arm()  # arm device
        # self.core.break_realtime()
        delay(300*ms)   # wait some amount of time
        self.Detect.trigger_camera()
        delay(10*ms)
        delay(self.Detect.Exposure_Time)
        delay(100*ms)
        self.Detect.acquire() 
        delay(100*ms)
        # self.Detect.transfer_background_image(ii)
        delay(300*ms)
        self.Detect.disarm() 
        
        
        ###########
        # do experiment thing here
        ###########
        
        # self.Detect.arm()
        # delay(300*ms) 
        # self.Detect.trigger_camera()
        # # delay(10*ms)
        # # delay(self.Detect.Exposure_Time)
        # # self.Detect.acquire()
        # # self.Detect.transfer_background_image(ii)
        # # delay(100*ms)
        # # print('disarming')
        # self.Detect.disarm()
        
        # self.mutate_dataset("time_delay",ii,self.x[ii])
        # self.mutate_dataset("detection.index",ii, ii)
