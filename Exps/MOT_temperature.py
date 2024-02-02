# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 11:48:20 2023

@author: E. Porter
"""

from scan_framework import Scan1D, TimeScan
from artiq.experiment import *
import numpy as np
from scipy.optimize import curve_fit
from numpy import unravel_index

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from CameraClass import _Camera
from repository.models.scan_models import TemperatureModel

class Temperature_scan_exp(Scan1D, TimeScan, EnvExperiment):
    
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
        
        # attrs for this exp
        # self.setattr_argument('ScanType', EnumerationValue(['CoM', 'Tx', 'Tz']) )
        self.setattr_argument("Detection_pulse_time",NumberValue(0.2*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        self.setattr_argument("Direction",EnumerationValue(['X', 'Y']),"Fit Settings")
        self.setattr_argument("heat_time",NumberValue(1*1e-6,min=0.0,max=100*1e-6,scale = 1e-6,
                      unit="us"),"Params")
        self.setattr_argument("heat",BooleanValue(False),"Params")

        
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
        delay(5000*ms)
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
        # delay(50*ms)
        with parallel:
            if self.heat:
                with sequential:
                    self.MOTs.set_AOM_freqs([('3D', self.MOTs.f_MOT3D_detect)])
                    self.MOTs.set_AOM_attens([('3D', 6.0)])                    
                    self.MOTs.AOMs_on(['3D'])
                    delay(self.heat_time)
                    self.MOTs.AOMs_off(['3D'])
            delay(t_delay)

        self.MOTs.take_MOT_image(self.Camera)
        delay(10*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        
        delay(50*ms)
        self.Camera.process_image(bg_sub=True)
        delay(400*ms)
        # if self.Direction == 'X':
        #     return self.Camera.process_gaussian(3)
        # elif self.Direction == 'Y':
        #     return self.Camera.process_gaussian(4)
        return 0
    
    
    def after_fit(self, fit_name, valid, saved, model):
        self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=True)
     