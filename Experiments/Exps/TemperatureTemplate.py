# -*- coding: utf-8 -*-
"""
@author: E. Porter
"""

import numpy as np
from artiq.experiment import *
from CameraClass import _Camera
from CoolingClass import _Cooling
from numpy import unravel_index
from repository.models.scan_models import TemperatureModel
from scan_framework import Scan1D, TimeScan
from scipy.optimize import curve_fit


class _Temperature_scan__template_exp(Scan1D, TimeScan, EnvExperiment):
    
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
        self.scan_arguments(times = {'start':0.1*1e-3,
            'stop':50*1e-3,
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
        
        self.setattr_argument("Detection_pulse_time",NumberValue(0.2*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")



        
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model = TemperatureModel(self, pix2um=67.8)
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
        delay(5000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump"])
        self.MOTs.atom_source_off()
                


    @kernel
    def measure(self, point):
        t_delay = point
        self.initialize()
        self.prepare_atoms()
        delay(t_delay)
        return self.process()
       
    
    @kernel
    def initialize(self):
        self.core.reset()
        self.Camera.arm()
        delay(200*ms)
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(10*ms)
        
    @kernel
    def prepare_atoms(self):
        pass
    
    @kernel
    def process(self) -> TInt32:
        self.MOTs.take_MOT_image(self.Camera)
        
        delay(10*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        
        delay(50*ms)
        self.Camera.process_image(bg_sub=True)
        delay(400*ms)
        return 0
    
        
    def after_fit(self, fit_name, valid, saved, model):
        self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=True)
     