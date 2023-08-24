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
from ThreePhotonClass import _ThreePhoton
from repository.models.scan_models import RabiModel

class ThreePhoton698_Rabi_Scan(Scan1D, TimeFreqScan, EnvExperiment):
    
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
            'ndecimals':3},
            frequency_center={'default':84*MHz},
            pulse_time= {'default':0*us},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "No Fits"}
        
            )
        self.setattr_argument('ScanBeam', EnumerationValue(['1', '2', '3']), "Params")
        self.setattr_argument('Shelf', BooleanValue(True), "Detection")
        self.t0 = np.int64(0)
        self.ind = 1
        self.setattr_argument("No_Scan",BooleanValue(False),"Params")
        self.setattr_argument("No_Scan_Val",NumberValue(0*1e-6,min=0.0*1e-6,max=100.00*1e-6,scale = 1e-6,
                      unit="us"),"Params")

        
        
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms(N=45)
        self.MOTs.prepare_coils()
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
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        self.ThPh.init_aoms(on=False)  # initializes whiling keeping them off
        delay(10*ms)
        
        self.MOTs.set_current_dir(0)
        delay(10*ms)
        
        self.MOTs.ttl1.off() #close shutter
        delay(5*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump"])
        delay(1000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump"])
        self.MOTs.atom_source_off()     
        
        

 
                   

    @kernel
    def measure(self, time, frequency):
        pulse_time = time 
        bottom_voltage = (frequency - 72100000)/50000
        print(bottom_voltage)
        if self.No_Scan: pulse_time = self.No_Scan_Val 
        #prepare
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(100*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        
        # set freqs/phases
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1 , 0.0, self.t0, 0)            
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2 , 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3 , 0.0, self.t0, 0)
        if self.scan == 'frequency':            
            self.ThPh.set_AOM_phase('Beam' + self.ScanBeam, frequency, 0.0, self.t0, 0)
        # perform experiment
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(15*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT
        self.MOTs.AOMs_on(['3P0_repump', '3P2_repump']) #make sure all atoms go to ground state
        self.MOTs.set_current_dir(1) # XXX let MOT field go to zero and switch H-bridge, 5ms
        self.MOTs.set_current(3.0)
        delay(5*ms)
        self.MOTs.AOMs_off(['3P0_repump', '3P2_repump']) 
        
        delay(8*ms) # wait for field to ramp up
        
        ### NEW 3-photon pulse
        #self.ThPh.threePhoton_pulse(pulse_time) #drive 3P0
        #self.MOTs.ttl1.on() #open shutter
        #delay(2*ms)
        self.MOTs.freq_ramp(bottom_voltage) #ramp freq
        #self.MOTs.ttl1.off() #close shutter
        #delay(5*ms)
        ###################
        if self.Shelf:
            self.ThPh.AOMs_on(['688_shelf'])
            delay(5*ms)
            self.ThPh.AOMs_off(['688_shelf'])
        self.MOTs.blow_away(0.5*ms) #blow away undriven atoms
        
        self.MOTs.AOMs_on(['3P0_repump', '3P2_repump'])
        delay(0.2*ms)
        # image
        self.MOTs.take_MOT_image(self.Camera)
        delay(15*ms)
        self.MOTs.ttl1.off() # close push pulse shutter
        # turn off coils and reset
        self.MOTs.set_current(0.0)
        delay(5*ms)
        self.MOTs.set_current_dir(0)
        delay(5*ms)
        
        #process and output
        self.MOTs.atom_source_on() # just keeps AOMs warm
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm
        self.MOTs.AOMs_on(['Probe']) # just keeps AOMs warm
        self.Camera.process_image(save=True, name='', bg_sub=True)
        self.ind += 1

        delay(100*ms)
        
        return self.Camera.get_count_stats()

    
    def after_fit(self, fit_name, valid, saved, model):
        self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=True)
        # A = self.get_dataset('current_scan.fits.params.A')
        # f = self.get_dataset('current_scan.fits.params.f')
        # y0 = self.get_dataset('current_scan.fits.params.y0')
        # tau = self.get_dataset('current_scan.fits.params.tau')
        # phi = self.get_dataset('current_scan.fits.params.phi')
        # x = list(self.times)
        # x = np.linspace(x[0], x[-1], 5)
        # y = [model.fit_function.value(xi, A, f, tau, phi, y0) for xi in x]
        # self.set_dataset('current_scan.plots.myfitline', y, broadcast=True)
