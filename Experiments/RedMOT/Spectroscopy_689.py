# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 11:48:20 2023

@author: G. Panelli & E. Porter
"""

from scan_framework import Scan1D, TimeFreqScan
from artiq.experiment import *
import numpy as np



from CoolingClass import _Cooling
from CameraClass import _Camera
from ThreePhotonClass import _ThreePhoton
from BraggClass import _Bragg
from repository.models.scan_models import RabiModel

class Spectroscopy_689_exp(Scan1D, TimeFreqScan, EnvExperiment):
    
    def build(self, **kwargs):
        # required initializations
        
        super().build(**kwargs)
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.ThPh = _ThreePhoton(self)
        self.Bragg = _Bragg(self)
        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.scan_arguments(times = {'start':0*us,
            'stop':1.5*us,
            'npoints':20,
            'unit':"us",
            'scale':us,
            'global_step':0.1*us,
            'ndecimals':2},
             frequencies={
            'start':-3*MHz,
            'stop':3*MHz,
            'npoints':50,
            'unit':"MHz",
            'scale':MHz,
            'global_step':0.1*MHz,
            'ndecimals':4},
            frequency_center={'default':100*MHz},
            pulse_time= {'default':0*us},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "No Fits"}
        
            )
        self.t0 = np.int64(0)
        self.setattr_argument("wait_time", NumberValue(1000.0*1e-3,min=0.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"Params")
        self.setattr_argument("No_Scan",BooleanValue(False),"Params")
        self.setattr_argument("No_Scan_Val",NumberValue(0*1e-6,min=0.0*1e-6,max=10000.00*1e-6,scale = 1e-6,
                      unit="us"),"Params")

        
        
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Bragg.prepare_aoms()
        self.Camera.camera_init()
        self.ThPh.prepare_aoms()
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
        self.ThPh.init_ttls()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        self.ThPh.init_aoms(on=False)  # initializes whiling keeping them off
        self.Bragg.init_aoms(on=True)
        delay(10*ms)
        
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
        try:
            frequency = float(frequency)  # Ensure frequency is a float
        except ValueError:
            raise ValueError("Frequency must be a float")
        
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
            self.ThPh.set_AOM_freqs([('Beam3', frequency)])
            
        self.ThPh.ThPh_pulse(10*ms)
        # perform experiment
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(15*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT
        delay(5*ms)
        #self.MOTs.AOMs_on(['3P0_repump', '3P2_repump']) #make sure all atoms go to ground state
        self.MOTs.set_current_dir(1) # XXX let MOT field go to zero and switch H-bridge, 5ms
        self.MOTs.set_current(0.3)
        #self.MOTs.AOMs_off(['3P0_repump', '3P2_repump']) 
        delay(self.wait_time)
        
        self.Bragg.set_AOM_attens([("Dipole",25.0 )])
        self.Bragg.AOMs_off(["Homodyne"])
        delay(20*us)
        self.ThPh.ThPh_pulse(pulse_time) #drive 3P0
        self.ThPh.push_pulse(2*us) #drive 3P0
        delay(2*ms)
        self.Bragg.set_AOM_attens([("Dipole",12.0 )])
        self.Bragg.AOMs_on(["Homodyne"])
        self.MOTs.set_current(0.0)
        
        

        self.MOTs.take_MOT_image(self.Camera)  
        delay(15*ms)
        self.MOTs.set_current_dir(0)
        delay(5*ms)  
        
        #process and output
        self.MOTs.atom_source_on() # just keeps AOMs warm
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm

        self.Camera.process_image(save=True, name='', bg_sub=True)

        delay(400*ms)
        
        return self.Camera.get_push_stats()
            
    
    def after_fit(self, fit_name, valid, saved, model):
        self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=True)

