# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 12:02:13 2023

@author: E. Porter
"""

#%% Misc. Imports
import numpy as np
import time
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from scipy.optimize import curve_fit
from scan_framework import Scan2D
from artiq.experiment import *

from CoolingClass import _Cooling
from CameraClass import _Camera
from ThreePhotonClass import _ThreePhoton
from PicomotorClass import _Picomotor


from repository.models.scan_models import PicoAngleModel, PicoScanModel

from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING






class ThreePhoton689_Picomotor_Optimization(Scan2D, EnvExperiment):
    

    def build(self, **kwargs):
        
        super().build(**kwargs)
        

        self.Pico = _Picomotor(self)
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.ThPh = _ThreePhoton(self)

        self.setattr_argument('Shelf', BooleanValue(True), "Detection")
        self.setattr_argument("Rabi_t_pi", NumberValue(0.25*1e-6,min=0.0,max=20.00*1e-6,scale = 1e-6,
                                unit="us"),"Params")
        self.setattr_argument("delay",NumberValue(0.1*1e-6,min=0.0,max=50*1e-6,scale = 1e-6,
                      unit="us"),"Params")
        self.setattr_argument("heat_time",NumberValue(1*1e-6,min=0.0,max=100*1e-6,scale = 1e-6,
                      unit="us"),"Params")
        self.setattr_argument("threshold",NumberValue(0.5,min=0.0,max=1.0,scale = 1),"Params")
        self.setattr_argument('phase', Scannable(default=RangeScan(start=0.0, stop=2.0, npoints=21),
              scale=1,ndecimals=2,unit="Turns", global_step=0.01), group='Params')
        self.setattr_argument("freq_1Photon",NumberValue(84*1e6, min=80*1e6, max=90*1e6, scale=1*1e6, 
                                                          unit='MHz'),"1Photon")
        self.setattr_argument("beam_1Photon",EnumerationValue(['Beam1','Beam2','Beam3']),"1Photon")
        self.setattr_argument("pulse_1Photon",NumberValue(0.1*1e-6,min=0.0,max=50*1e-6,scale = 1e-6,
                      unit="us"),"1Photon")
        

        self.t0 = np.int64(0)  # for phase syncronization
        self.scan0 = 0 # for outputting data indices
        self.scan1 = 0
        

        self.enable_pausing = True
        self.enable_auto_tracking = False
        self.enable_profiling = False
        
        self.setattr_argument('pm1_pos', Scannable(default=RangeScan(start=0,stop=10000,npoints=20),
            scale=1,ndecimals=0,global_step=100), group='Scan Settings')
        self.setattr_argument('pm2_pos', Scannable(default=RangeScan(start=0,stop=10000,npoints=20), 
            scale=1,ndecimals=0,global_step=100), group='Scan Settings')
        
        self.scan_arguments(nbins={'default':1000},
                            nrepeats={'default':1},
                            npasses={'default':1},
                            fit_options={'default':"Fit and Save"})
        
           
    def get_scan_points(self):
        return [self.pm1_pos, self.pm2_pos]
    
    @kernel
    def set_scan_point(self, i_point, point):
        pm1, pm2 = point[0], point[1]
        #pm2 += pm1*2.5
        self.Pico.set_position(1, int(pm1))
        self.Pico.set_position(2, int(pm2))
        self.core.break_realtime()
        
        

    def prepare(self):
        self.phases = list(self.phase)
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        self.ThPh.prepare_aoms()
        self.Pico.set_home(1)
        self.Pico.set_home(2)
        # register model with scan framework
        self.enable_histograms = True
        self.ScanModel = PicoScanModel(self)
        self.AngleModel = PicoAngleModel(self)
        self.register_model(self.AngleModel, dimension=0, fit=True, set=True)
        self.register_model(self.ScanModel, dimension=1, fit=True, set=True, measurement=True)
        self.set_dataset("phase_measure", np.full(len(self.phases), np.nan), broadcast=True)
        for i in range(len(self.pm1_pos)):
            self.set_dataset(f"contrast{i}", np.full(len(self.pm2_pos), np.nan), broadcast=True)
        self.set_dataset("max_contrast", np.full(len(self.pm1_pos), np.nan), broadcast=True)
        self.scan0 = 0
        self.scan1 = 0
        self.scan1_length = len(self.pm2_pos)
    
    @kernel
    def before_scan(self):
        self.core.reset()
        
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)
        self.ThPh.init_aoms(on=False)  
        self.ThPh.set_phase_mode(PHASE_MODE_TRACKING)
        
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.AOMs_on(['3D', '2D', 'Zeeman', "3P0_repump", "3P2_repump"])
        delay(1000*ms)   

    

    @kernel
    def measure(self, point):
        # ignore point, was handled in set_scan_point method
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(200*ms)
        
        
        val = self.measure_1photon_excitation()
        
        self.core.break_realtime()
        delay(10*ms)
        
        if val < self.threshold:
            ratio = 0 # checks to see if beam close to aligned
        else:
            contrast_cold = self.measure_contrast(heat = False)
            delay(200*ms)
            contrast_hot = self.measure_contrast(heat = True)
            ratio = int(1e6*(contrast_hot/contrast_cold))
            if ratio > 1.25e6:
                ratio = 0
            
        self.write_contrast(ratio, self.scan1, self.scan0)
        self.scan1 +=1
        
        if self.scan1 % self.scan1_length == 0:
            self.write_max_contrast(self.scan0)
            self.scan1 = 0
            self.scan0 +=1
 
        return ratio
        
        
   
    @kernel
    def measure_contrast(self, heat) -> TFloat:
        outp = [0.0]*len(self.phases)
        i= 0
        self.erase_phase()
        for ph in self.phases:
            delay(200*ms)
            val =self.measure_3photon_excitation(ph, heat)
            outp[i] = val
            self.write_phase(val, i)
            i += 1
            
        self.core.wait_until_mu(now_mu())
        delay(10*ms)
        
        contrast = self.fit_contrast(outp)
        print(outp)
        print(contrast)
        self.core.break_realtime()
        delay(10*ms)
        return contrast
    
    def write_phase(self, val, i):
        self.mutate_dataset("phase_measure", i, val) 
        
    def erase_phase(self):
        self.set_dataset("phase_measure", np.full(len(self.phases), np.nan), broadcast=True) 
        
    def write_contrast(self, val, i, j):
        self.mutate_dataset(f"contrast{j}", i, val) 
        
    def erase_contrast(self):
        self.set_dataset("contrast", np.full(len(self.pm2_pos), np.nan), broadcast=True) 
        
    def write_max_contrast(self, i):
        ma = np.max(self.get_dataset(f"contrast{self.scan0}"))
        self.mutate_dataset("max_contrast", i, ma) 
        
    @kernel
    def measure_1photon_excitation(self) -> TFloat:
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        self.ThPh.set_AOM_phase('Beam1', self.freq_1Photon, 0.0, self.t0, 0)
        self.ThPh.switch_profile(0) 
        delay(50*ms)
        self.ThPh.AOMs_off(self.ThPh.AOMs)
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(50*ms)
        

        self.MOTs.rMOT_pulse()  # generates the red MOT 
        self.ThPh.set_field()  
        self.ThPh.onePhoton_pulse(self.pulse_1Photon, self.beam_1Photon)
        # image
        if self.Shelf:
            self.MOTs.shelf()
        self.MOTs.push()
        self.MOTs.take_MOT_image(self.Camera)
        
        
    
        #process and output
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm
        self.Camera.process_image(save=True, name='', bg_sub=True)
        delay(100*ms)        
        return self.Camera.get_push_stats()*1e-6
    
    @kernel
    def measure_3photon_excitation(self, phase, heat) -> TFloat:
        self.core.wait_until_mu(now_mu())
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, phase, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 1)
            # make this more compact 
        self.ThPh.switch_profile(0) 
        
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(5*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT 
        with parallel:
            if heat:
                self.MOTs.set_AOM_freqs([('3D', self.MOTs.f_MOT3D_detect)])
                self.MOTs.set_AOM_attens([('3D', 6.0)]) 
            self.ThPh.set_field()  
        if heat:
            with sequential:                   
                self.MOTs.AOMs_on(['3D'])
                delay(self.heat_time)
                self.MOTs.AOMs_off(['3D'])
        self.ThPh.threePhoton_pulse(self.Rabi_t_pi)
        
        
        self.ThPh.switch_profile(1)
        delay(self.delay)  # offset by half a micro second

        self.ThPh.threePhoton_pulse(self.Rabi_t_pi)
        
        # image
        if self.Shelf:
            self.MOTs.shelf()
        self.MOTs.push()
        self.MOTs.take_MOT_image(self.Camera)
        
        
    
        #process and output
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm
        self.Camera.process_image(bg_sub=True)
        delay(100*ms) 
        val = self.Camera.get_push_stats()
        delay(10*ms)
        return val*1e-6
    
    def calculate_dim0(self, dim1_model):
        param = dim1_model.fit.params.A
        error = dim1_model.fit.errs.A_err
        return param, error
    
    def fit_contrast(self, inp) -> TFloat:
        x = self.phases
        y = inp
        popt, pcov = curve_fit(sine_fit, x, y, p0 = (0.1, 0), bounds=([0,0],[1,2*np.pi]))
        return popt[0]
        
def sine_fit(x, A, phi):
    return A*np.sin(2*np.pi*x+phi)
        

        

# # TODO
# # output all data to the namespace so we can analyze it later
# ensure the model scaling is appropriate
# to the math for determining how much to move motor 2 each time
# add a little more intelligence into the scan to make the speed better
# verifying the timing of everything is correct by sanity checking all values
       
        

        
        




