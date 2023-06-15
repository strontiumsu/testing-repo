# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 17:18:43 2023

@author: E. Porter
"""


from scan_framework import Scan1D, TimeScan
from artiq.experiment import *
import numpy as np


import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from CameraClass import _Camera
from ThreePhotonClass import _ThreePhoton
from repository.models.scan_models import RamseyModel
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING

class ThreePhoton689_Ramsey_Scan(Scan1D, TimeScan, EnvExperiment):
    
    def build(self, **kwargs):
        # required initializations
        
        super().build(**kwargs)
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.ThPh = _ThreePhoton(self)
        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.scan_arguments(times={
            'start':0*1e-6,
            'stop':50*1e-6,
            'npoints':50,
            'unit':"us",
            'scale':us,
            'global_step':0.1*us,
            'ndecimals':2},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "Fit and Save"}
        
            )

        self.setattr_argument('Shelf', BooleanValue(True), "Detection")
        self.t0 = np.int64(0)
        self.ind = 1
        self.setattr_argument("Rabi_t_pi",NumberValue(0.25*1e-6,min=0.0,max=20.00*1e-6,scale = 1e-6,
                      unit="us"),"Ramsey")
        self.setattr_argument("Rabi_pulse_phase",
            Scannable(default=[RangeScan(0.0, 2.0, 20, randomize=False),NoScan(0.0)],scale=1,
                      unit="Turns"),"Ramsey")
        
        self.setattr_argument("heat_time",NumberValue(1*1e-6,min=0.0,max=100*1e-6,scale = 1e-6,
                      unit="us"),"Params")
        self.setattr_argument("heat",BooleanValue(False),"Params")

        
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        self.ThPh.prepare_aoms()
        # register model with scan framework
        self.enable_histograms = True
        self.model = RamseyModel(self)
        self.register_model(self.model, measurement=True, fit=True)
        
    @kernel
    def before_scan(self):
        # runs before experiment take place
        
        #initialize devices on host
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        self.ThPh.init_aoms(on=False)  # initializes whiling keeping them off
        self.ThPh.set_phase_mode(PHASE_MODE_TRACKING)
        
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.AOMs_on(['3D', '2D', 'Zeeman', "3P0_repump", "3P2_repump"])
        delay(500*ms)
        
    @kernel
    def measure(self, point):
        t_ramsey = point
        #prepare
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)
        self.ThPh.switch_profile(0)
        self.t0 = now_mu()
        

        # do phase stuff
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, self.Rabi_pulse_phase.value, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 1)
            # make this more compact
            
            
            
        # perform experiment    
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(5*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT        
        with parallel:
            if self.heat:
                self.MOTs.set_AOM_freqs([('3D', self.MOTs.f_MOT3D_detect)])
                self.MOTs.set_AOM_attens([('3D', 6.0)]) 
            self.ThPh.set_field()  
        if self.heat:
            with sequential:                   
                self.MOTs.AOMs_on(['3D'])
                delay(self.heat_time)
                self.MOTs.AOMs_off(['3D'])       
        self.ThPh.threePhoton_pulse(self.Rabi_t_pi)
        
        
        #self.ThPh.switch_profile(1)
        delay(t_ramsey)  # offset by half a micro second
        
        self.ThPh.threePhoton_pulse(self.Rabi_t_pi)
        
        
        
        # image
        if self.Shelf:
            self.MOTs.shelf()
        self.MOTs.push()
        self.MOTs.take_MOT_image(self.Camera)
        
        
    
        #process and output
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm
        delay(50*ms)
        self.Camera.process_image(bg_sub=True)
        delay(400*ms) 
        self.ind += 1
        return self.Camera.get_push_stats()
    
    
    def after_fit(self, fit_name, valid, saved, model):
        self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=True)
     