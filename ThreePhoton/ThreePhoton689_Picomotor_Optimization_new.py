# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 12:02:13 2023

@author: G. Panelli
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


from repository.models.scan_models import PicoAngleModel, PicoScanModel, RamseyPhaseModel

from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING






class ThreePhoton689_Picomotor_Optimization_new(Scan2D, EnvExperiment):
    

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
        self.setattr_argument("heat",BooleanValue(False),"Params")

        

        self.t0 = np.int64(0)  # for phase syncronization
        self.scan0 = 0 # for outputting data indices
        self.scan1 = 0
        self.ramsey_phase_exp = 0.0*1e-6
        self.ind=0
        

        self.enable_pausing = True
        self.enable_auto_tracking = False
        self.enable_profiling = False
        
        self.setattr_argument('pm2_pos', Scannable(default=RangeScan(start=0,stop=10000,npoints=20), 
            scale=1,ndecimals=0,global_step=100), group='Scan Settings')
        self.setattr_argument('phase', Scannable(default=RangeScan(start=0.0, stop=2.0, npoints=21),
              scale=1,ndecimals=2,unit="Turns", global_step=0.01), group='Scan Settings')
        
        self.scan_arguments(nbins={'default':1000},
                            nrepeats={'default':1},
                            npasses={'default':1},
                            fit_options={'default':"Fit and Save"})
        
           
    def get_scan_points(self):
        return [self.pm2_pos, self.phase]
    
    @kernel
    def set_scan_point(self, i_point, point):
        pm2 = point[0]
        self.ramsey_phase_exp = point[1]
        self.Pico.set_position(4, int(pm2))
        self.core.break_realtime()
        
        

    def prepare(self):
        self.phases = list(self.phase)
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        self.ThPh.prepare_aoms()
        
        self.Pico.set_home(3)
        self.Pico.set_home(4)
        # register model with scan framework
        self.enable_histograms = True
        self.model0 = PicoScanModel(self)
        self.model1 = RamseyPhaseModel(self)

        self.register_model(self.model0, dimension=0, fit=True, set=True)
        self.register_model(self.model1, dimension=1, fit=True, set=True, measurement=True)
        

    
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
        
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, self.ramsey_phase_exp, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 1)
            # make this more compact 
        self.ThPh.switch_profile(0) 
        
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
        self.ind += 1
        val = self.Camera.get_push_stats()
        self.write_val(val)
        return val
        
    
    def calculate_dim0(self, dim1_model):
        param = 2*dim1_model.fit.params.A
        # weight final fit by error in this dimension 1 fit param
        error = dim1_model.fit.errs.A_err
        self.set_dataset(f"ContrastMeasurement__{self.scan1}", param, broadcast=False)
        self.scan1 += 1
        return param, error
    
    def write_val(self, val):
        self.set_dataset(f"PhaseMeasurement_{self.scan0}_{self.scan1}", val, broadcast=False)
        self.scan0 += 1
    
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
       
        

        
        




