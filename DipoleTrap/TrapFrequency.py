# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 17:36:29 2023

@author: E.Porter
"""


from scan_framework import Scan1D, TimeScan
from artiq.experiment import *
import numpy as np

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from CameraClass import _Camera
from repository.models.scan_models import TemperatureModel

class TrapFrequency_exp(Scan1D, TimeScan, EnvExperiment):
    
    def build(self, **kwargs):
        # required initializations
        
        super().build(**kwargs)
        
        self.enable_pausing = True
        self.enable_auto_tracking = False
        self.enable_profiling = False
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        
        # scan settings
        self.scan_arguments(times = {'start':1*1e-3,
            'stop':1000*1e-3,
            'npoints':20,
            'unit':"ms",
            'scale':ms,
            'global_step':1*us,
            'ndecimals':2},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default':"Fit and Save"}
            )
        
        # attrs for this exp
        # self.setattr_argument('ScanType', EnumerationValue(['CoM', 'Tx', 'Tz']) )
        self.setattr_argument("Detection_pulse_time",NumberValue(0.2*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        self.setattr_argument("wait_time", NumberValue(15*1e-3,min=1.0*1e-3,max=5000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")

        
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model = TemperatureModel(self, Direction=self.Direction)
        self.register_model(self.model, measurement=True, fit=True)
        
        
      
        
        
        
    @kernel
    def before_scan(self):
        # runs before experiment take place
        
        #initialize devices on host
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump"])
        delay(2000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump"])
        self.MOTs.atom_source_off()
                


    @kernel
    def measure(self, point):
        t_delay = point
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        #delay(1000*ms)
        self.Camera.arm()
        delay(200*ms)
        
        
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(10*ms)
        self.MOTs.rMOT_pulse()
        delay(self.wait_time)
        
        
        self.MOTs.AOMs_on(['Probe'])
        delay(self.MOTs.Push_pulse_time)
        self.MOTs.AOMs_off(['Probe'])
        
        
        delay(t_delay)
        self.MOTs.take_MOT_image(self.Camera)
        delay(10*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        
        delay(50*ms)
        return 0
    
    
    def after_fit(self, fit_name, valid, saved, model):
        self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=True)
     