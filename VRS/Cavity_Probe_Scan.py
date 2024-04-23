# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 11:48:20 2023

@author: G. Panelli & E. Porter
"""

from scan_framework import Scan1D, TimeFreqScan
from artiq.experiment import *
import numpy as np


import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg
from SqueezingClass import _Squeezing
from repository.models.scan_models import RabiModel

class Cavity_Probe_Scan(Scan1D, TimeFreqScan, EnvExperiment):
    
    def build(self, **kwargs):
        # required initializations
        
        super().build(**kwargs)
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.Bragg = _Bragg(self)
        self.Squeezing = _Squeezing(self)
        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.scan_arguments(times = {'start':0*ms,
            'stop':5*ms,
            'npoints':20,
            'unit':"ms",
            'scale':ms,
            'global_step':0.1*ms,
            'ndecimals':2},
             frequencies={
            'start':-3*MHz,
            'stop':3*MHz,
            'npoints':50,
            'unit':"MHz",
            'scale':MHz,
            'global_step':0.1*MHz,
            'ndecimals':4},
            frequency_center={'default':84*MHz},
            pulse_time= {'default':0*ms},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "No Fits"}
        
            )
        self.setattr_argument('FS', BooleanValue(True), "Params")
        self.t0 = np.int64(0)
        self.setattr_argument("No_Scan",BooleanValue(False),"Params")
        self.setattr_argument("No_Scan_Val",NumberValue(0*1e-3,min=0.0*1e-3,max=10000.00*1e-3,scale = 1e-3,
                      unit="ms"),"Params")
        self.ind = -1

        
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Bragg.prepare_aoms()
        self.Squeezing.prepare_aoms()
        self.Camera.camera_init()
        
        if self.scan == 'frequency':     
            self.Camera.prep_datasets(np.full(int(len(self.frequencies)), np.nan))
        else:     
            self.Camera.prep_datasets(np.full(int(len(self.times)), np.nan))
        
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
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        self.Bragg.init_aoms(on=True)
        self.Squeezing.init_aoms(on=False)
        delay(10*ms)
        
        #self.MOTs.dac_set(4,-1.0)
        
        self.MOTs.set_current_dir(0)
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump", "Probe"])
        delay(2000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump", "Probe"])
        self.MOTs.atom_source_off()    
        

                   

    @kernel
    def measure(self, time, frequency):
        
        pulse_time = time
        if self.No_Scan: pulse_time = self.No_Scan_Val 
        #prepare
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(100*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        if self.scan == 'frequency':            
            ## Set Probe Frequency (either VCO or DDS)
            delay(10*ms)
            
        # perform experiment
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(15*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT
        delay(25*ms) # load into lattice
        
        if self.FS:
           self.Bragg.set_AOM_attens([("Dipole",20.0 ), ("Homodyne",30.0)])

        ## Probe cavity for pulse time
        with parallel:
            self.MOTs.cavity_scan_trig()
            with sequential:
                delay(2*ms)
                self.Squeezing.cavity_probe_pulse(pulse_time)
                #self.Squeezing.cavity_probe_scan(pulse_time,99*MHz,101*MHz,40)
        
        self.MOTs.set_current(0.0)
        
        if self.FS:
            self.Bragg.set_AOM_attens([("Dipole",4.0 ), ("Homodyne",3.0)])
        

        self.MOTs.take_MOT_image(self.Camera)
        delay(200*ms)
        self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D']) 
        
        #process and output
        self.MOTs.atom_source_on() # just keeps AOMs warm
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm
        self.Bragg.set_AOM_attens([("Dipole",4.0 ), ("Homodyne",3.0)])

        self.Camera.process_image(save=True, name='', bg_sub=True)

        delay(400*ms)
        self.ind += 1
        
        return self.Camera.get_count_stats(self.ind)
            
    
    def after_fit(self, fit_name, valid, saved, model):
        self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=True)

