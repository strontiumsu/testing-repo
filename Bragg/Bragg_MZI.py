# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 16:41:22 2024

@author: E. Porter
"""
from scan_framework import Scan1D, TimeFreqScan
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, BooleanValue, Scannable, RangeScan, kernel, now_mu, ms, us, MHz,kHz,  NumberValue, delay, parallel, sequential

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg
from repository.models.scan_models import RabiModel

class Bragg_MZI_exp(Scan1D, EnvExperiment):
    
    def build(self, **kwargs):
    # required initializations
    
        super().build(**kwargs)
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.Bragg = _Bragg(self)
        
        
        # attributes here
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks
    
        self.t0 = np.int64(0)
        self.ind = 1
        
        self.setattr_argument('pulse_phase', 
            Scannable(default=RangeScan(
            start=0.0,
            stop=2.0,
            npoints=20),
            scale=1,
            ndecimals=2,
            unit="Turns"), 'Ramsey')
        
        self.scan_arguments(nbins={'default':1000},
                    nrepeats={'default':1},
                    npasses={'default':1},
                    fit_options={'default':"No Fits"})
    
        self.setattr_argument("dipole_load_time", NumberValue(25.0*1e-3,min=0.0*1e-3,max=1000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("drift_time", NumberValue(15.0*1e-3,min=0.0*1e-3,max=100.00*1e-3,scale=1e-3,
               unit="ms"),"parameters")
        self.setattr_argument("interaction_time", NumberValue(15.0*1e-6,min=0.0*1e-6,max=10000.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("field_strength", NumberValue(0.3,min=0.0,max=5.0,scale=1),"parameters")
    def get_scan_points(self):
        return self.pulse_phase  
    
    def prepare(self):
    #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms(N=50)
        self.MOTs.prepare_coils()
        self.Bragg.prepare_aoms()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model = RabiModel(self)
        self.register_model(self.model, measurement=True, fit=True)
        
    @kernel
    def before_scan(self):
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        self.Bragg.init_aoms(on=True)
        
        self.MOTs.set_current_dir(0)
        delay(10*ms)
        
        self.Bragg.AOMs_off(['Bragg1', 'Bragg2'])
        
        delay(10*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(100*ms)
        
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump", "Probe"])
        delay(2000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump", "Probe"])
        self.MOTs.atom_source_off()
        
    @kernel
    def measure(self, point):
        phase = point
        
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(100*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        self.Bragg.set_AOM_phase('Bragg1', 110*MHz, 0.0, self.t0, 0)
        self.Bragg.set_AOM_phase('Bragg1', 110*MHz, 0.0, self.t0, 1)
        # self.Bragg.set_AOM_phase('Bragg1', 110*MHz, 0.0, self.t0, 2)
        # 
        self.Bragg.set_AOM_phase('Bragg2', 110.043*MHz, 0.0, self.t0, 0)
        self.Bragg.set_AOM_phase('Bragg2', 110.043*MHz, phase, self.t0, 1)
        # self.Bragg.set_AOM_phase('Bragg2', 110.128*MHz, phase, self.t0, 2)
        
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, self.t0, 0)
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, self.t0, 1)
        # self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, self.t0, 2)
        
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Homodyne, 0.0, self.t0, 0)
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Homodyne, 0.0, self.t0, 1)
        # self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Homodyne, 0.0, self.t0, 2)
        
        
        self.Bragg.switch_profile(0)
        
    
            
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(15*ms)
        self.MOTs.rMOT_pulse()
        with parallel:
            delay(self.dipole_load_time)
            # with sequential:
                # self.MOTs.set_current_dir(1) # XXX let MOT field go to zero and switch H-bridge, 5ms       
                # self.MOTs.set_current(self.field_strength)
        self.Bragg.set_AOM_attens([("Dipole",30.0 ), ("Homodyne",30.0)])
        self.Bragg.set_AOM_scales([("Dipole",0.2 ), ("Homodyne",0.2)])
        self.Bragg.AOMs_off(['Homodyne'])
        
        # with parallel:
        #     self.Bragg.switch_profile(1)
        #     delay(1*us)  # offset by half a micro second
        
        
        self.Bragg.bragg_pulse(4.5*us)
        delay(self.interaction_time)
        self.Bragg.bragg_pulse(9*us)
        with parallel:
            delay(self.interaction_time)
            self.Bragg.switch_profile(1)
        self.Bragg.bragg_pulse(4.5*us)
        
        
        delay(self.drift_time)

        self.MOTs.take_MOT_image(self.Camera)
        self.Bragg.set_AOM_attens([("Dipole",4.0 ), ("Homodyne",self.Bragg.atten_Homodyne)])
        self.Bragg.set_AOM_scales([("Dipole",0.8 ), ("Homodyne",self.Bragg.scale_Homodyne)])
        self.Bragg.AOMs_on(['Homodyne'])
        

        delay(50*ms)
        self.Camera.process_image(bg_sub=True)
        delay(400*ms)
        self.core.wait_until_mu(now_mu())
        delay(200*ms)
        self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D', "Probe"])
        delay(200*ms)

        
        
        
        return 0
    
    @kernel
    def after_scan(self):
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.atom_source_on()

    
        
