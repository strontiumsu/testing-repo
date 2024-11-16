# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 16:08:07 2024

@author: sr
"""

import numpy as np
from artiq.experiment import *
from CameraClass import _Camera
from BraggClass import _Bragg
from CoolingClass import _Cooling
from UrukulClass import _Urukul
from repository.models.scan_models import RabiModel
from scan_framework import Scan1D, TimeScan



class red_spectroscopy_exp(Scan1D, TimeScan, EnvExperiment):
    
    def build(self, **kwargs):
        # required initializations
        
        super().build(**kwargs)
        
        self.enable_pausing = True
        self.enable_auto_tracking = False
        self.enable_profiling = False
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Bragg = _Bragg(self)
        self.Urukul = _Urukul(self)
        self.Camera = _Camera(self)
        
        self.scan_arguments(times = {'start':0.1,
            'stop':100,
            'npoints':20,
            'unit':"us",
            'scale':1e-6,
            'global_step':0.1e-6,
            'ndecimals':2},
             frequencies={
            'start':-5*MHz,
            'stop':5*MHz,
            'npoints':50,
            'unit':"MHz",
            'scale':MHz,
            'global_step':0.1*MHz,
            'ndecimals':3},
            frequency_center={'default':80.00*MHz},
            pulse_time= {'default':5.0},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "No Fits"}

            )
        
        self.setattr_argument("load_time", NumberValue(20.0*1e-3,min=0.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("wait_time", NumberValue(100.0*1e-3,min=0.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")

    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.Bragg.prepare_aoms()
        self.Urukul.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model = RabiModel(self)
        self.register_model(self.model, measurement=True, fit=True)
        
    @kernel
    def before_scan(self):
        # runs before experiment take place
        
        #initialize devices on host
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        self.Bragg.init_aoms(on=True)  # initializes whiling keeping them off
        self.Urukul.init_aoms(on=False)  # initializes whiling keeping them off
        
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump"])
        delay(5000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump"])
        self.MOTs.atom_source_off()
    
    @kernel
    def run(self, time, frequency):
        self.core.reset()
        self.Camera.arm()
        delay(200*ms)
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        self.Urukul.AOMS_off(self.Urukul.AOMs)
        delay(10*ms)
        
        
        self.MOTs.rMOT_pulse()
        delay(self.load_time)
        
        self.run_exp(time, frequency)
        
        self.Urukul.push()
        self.MOTs.take_MOT_image(self.Camera)
        delay(10*ms)
        self.Camera.process_image(bg_sub=True)
        delay(300*ms)
        self.core.wait_until_mu(now_mu())
        delay(200*ms)
        self.Urukul.AOMs_off(self.Urukul.AOMs)
        self.MOTs.AOMs_off(self.MOTs.AOMs)

        #self.Camera.get_count_stats(m)
        delay(self.wait_time)
        
        
        
    @kernel
    def run_exp(self, t, f):
        self.Urukul.AOMs_on(["AI1"])
        self.delay(t)
        self.Urukul.AOMs_off(["AI1"])
        
        
        
    
    @kernel
    def after_scan(self):
        pass

    
    
            