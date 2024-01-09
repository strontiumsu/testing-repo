# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 19:25:14 2023

@author: sr
"""

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
from BraggClass import _Bragg
from repository.models.scan_models import RamseyPhaseModel
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING




class ThreePhoton698_Ramsey_Scan_v2(Scan1D, EnvExperiment):
    
    def build(self, **kwargs):       
        super().build(**kwargs)        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.ThPh = _ThreePhoton(self)
        self.Bragg = _Bragg(self)
        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.t0 = np.int64(0)
        self.ind = 1
        self.setattr_argument('FS', BooleanValue(True), "Ramsey")
        
        
        self.setattr_argument("Rabi_t_pi",
                              NumberValue(0.001*1e-3,min=0.0,max=20.00*1e-3,scale = 1e-3,
                               unit="ms"),"Ramsey")
        
        self.setattr_argument("wait_time",
                              NumberValue(0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                              unit="ms"),"Ramsey")
        
        self.setattr_argument('Rabi_pulse_phase', 
            Scannable(default=RangeScan(
            start=0.0,
            stop=2.0,
            npoints=20),
            scale=1,
            ndecimals=2,
            unit="Turns"), 'Ramsey')
        
        self.setattr_argument('Alignment', BooleanValue(False), "Params")
        
        self.scan_arguments(nbins={'default':1000},
                            nrepeats={'default':1},
                            npasses={'default':1},
                            fit_options={'default':"No Fits"})
        
        self.setattr_argument("heat_time",NumberValue(1*1e-6,min=0.0,max=100*1e-6,scale = 1e-6,
                      unit="us"),"Params")
        self.setattr_argument("heat",BooleanValue(False),"Params")
    
    def get_scan_points(self):
        return self.Rabi_pulse_phase
        
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Bragg.prepare_aoms()
        self.Camera.camera_init()
        self.ThPh.prepare_aoms()
        # register model with scan framework
        self.enable_histograms = True
        self.model = RamseyPhaseModel(self)
        self.register_model(self.model, measurement=True, fit=True)
        
    @kernel
    def before_scan(self):
        #initialize devices on host
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
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
    def measure(self, point):
        alignment=self.Alignment
        phase = point

        #prepare
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(100*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        
        

        # do phase stuff
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, 0.0, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, phase, self.t0, 1)
            # make this more compact 
        self.ThPh.switch_profile(0)  
        
        self.ThPh.threePhoton_pulse(10*ms)
        # perform experiment
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(15*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT
        
        self.MOTs.AOMs_on(['3P0_repump', '3P2_repump']) #make sure all atoms go to ground state
        self.MOTs.set_current_dir(1) # XXX let MOT field go to zero and switch H-bridge, 5ms
        
        h_bridge_current = 0.1 if alignment else 6.4
        self.MOTs.set_current(h_bridge_current)
        if alignment: 
            delay(20*ms)
        else:
            delay(60*ms)
        self.MOTs.AOMs_off(['3P0_repump', '3P2_repump']) 
        delay(10*ms)
       
        # Turn off dipole trap
        #XXX
        if self.FS:
           self.Bragg.set_AOM_attens([("Bragg1",20.0 ), ("Homodyne2",30.0)]) 
        
        # Turn on 689 beams first
        self.ThPh.AOMs_on(['Beam1','Beam2'])
        delay(0.03*ms)
        # Tur on 698 beam
        self.ThPh.AOMs_on(['Beam3'])
        delay(self.Rabi_t_pi)
        self.ThPh.AOMs_off(['Beam3'])
        #self.ThPh.AOMs_off(['Beam1','Beam2'])
        
        with parallel:
            self.ThPh.switch_profile(1)
            delay(self.wait_time)  # offset by half a micro second
        #self.ThPh.AOMs_on(['Beam1','Beam2'])
        #delay(0.03*ms)
        self.ThPh.AOMs_on(['Beam3'])
        delay(self.Rabi_t_pi)
        self.ThPh.AOMs_off(['Beam3'])
        
        delay(0.03*ms)
        self.ThPh.AOMs_off(['Beam1','Beam2'])
        
        if self.FS:
            self.Bragg.set_AOM_attens([("Bragg1",4.0 ), ("Homodyne2",3.0)]) 
        
        # self.ThPh.threePhoton_pulse(self.Rabi_t_pi)
        # self.ThPh.switch_profile(1)
        # delay(self.wait_time)  # offset by half a micro second
        # self.ThPh.threePhoton_pulse(self.Rabi_t_pi)
        
        # self.MOTs.push()
        # self.MOTs.take_MOT_image(self.Camera)
        # delay(5*ms)
        
        if alignment:           # aligning with 689
            self.MOTs.push()
            self.MOTs.take_MOT_image(self.Camera)
            delay(5*ms)

        delay(1*ms)
        self.MOTs.set_current(0.0)
        delay(30*ms)
        if not alignment:  # 698 beam
            self.MOTs.push()
            self.MOTs.take_MOT_image(self.Camera)  
        delay(15*ms)
        self.MOTs.set_current_dir(0)
        delay(5*ms)  
        
        #process and output
        self.MOTs.atom_source_on() # just keeps AOMs warm
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm

        self.Camera.process_image(save=True, name='', bg_sub=True)

        delay(100*ms)
        
        return self.Camera.get_push_stats()
    
    
    def after_fit(self, fit_name, valid, saved, model):
        self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=False)
     