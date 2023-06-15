# # -*- coding: utf-8 -*-
# """
# Created on Wed Mar 15 16:01:28 2023

# @author: E. Porter
# """

from scan_framework import Scan2D, TimeScan
from artiq.experiment import *
import numpy as np
import time

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from ThreePhotonClass import _ThreePhoton
from PicomotorClass import _Picomotor
from repository.models.scan_models import LinearModel, PicoModel
from CameraClass import _Camera


class angle_optimization(Scan2D, EnvExperiment):
    
    
    def build(self, **kwargs):
#         # required initializations
        
        super().build(**kwargs)
        
#         # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.ThPh = _ThreePhoton(self)
        self.Camera = _Camera(self)
        self.Pico = _Picomotor(self)

        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.setattr_argument('motor1_steps', Scannable(
            default=RangeScan(
                start=-5000,
                stop=5000,
                npoints=20
            ),
            scale=1,
            ndecimals=0,
            global_step=1
        ), group='Scan Range')
        self.setattr_argument('motor2_steps', Scannable(
            default=RangeScan(
                start=-5000,
                stop=5000,
                npoints=50
            ),
            scale=1 ,
            ndecimals=0,
            global_step=1
        ), group='Scan Range')


        # scan arguments
        self.scan_arguments(nbins={'default':1000},
                            nrepeats={'default':1},
                            npasses={'default':1},
                            fit_options={'default':"Fit and Save"})
        
        self.setattr_argument("Time",NumberValue(0*1e-6,min=0.0*1e-6,max=100.00*1e-6,scale = 1e-6,
                      unit="us"),"Params")
        self.setattr_argument('ScanBeam', EnumerationValue(['1', '2', '3']), "Params")
        self.setattr_argument('MotorShift',NumberValue(0,min=0,max=10000),"Params")
        self.setattr_argument('Shelf', BooleanValue(True), "Detection")
        self.t0 = np.int64(0)
        self.ind = 1

    def get_scan_points(self):
        return [self.motor1_steps, self.motor2_steps]
    
    @kernel
    def set_scan_point(self, i_point, point):
        x_pos = point[0]
        y_pos = point[1]+i_point[0]*self.MotorShift
        #print(y_pos)
        

        # set the trap frequency at the start of the tickle sub-scan
        self.Pico.set_position(1, int(x_pos))
        self.Pico.set_position(2, int(y_pos))
        delay(500*ms)
    
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.ThPh.prepare_aoms()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model1 = LinearModel(self)  # change model
        self.model2 = PicoModel(self)   # change model
        self.register_model(self.model1, dimension=0, fit=True, set=True)
        self.register_model(self.model2, dimension=1, fit=True, set=True, measurement=True)
        self.Pico.set_home(1)
        self.Pico.set_home(2)  # change how this works so we keep our home consistent
        
    @kernel
    def before_scan(self):
        # runs before experiment take place
        
        #initialize devices on host
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        self.ThPh.init_aoms(on=False)  # initializes whiling keeping them off
        
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.AOMs_on(['3D', '2D', 'Zeeman', "3P0_repump", "3P2_repump"])
        delay(500*ms)
        
        
        
    @kernel
    def after_scan(self):
        self.Pico.set_position(1, 0)
        self.Pico.set_position(2, 0)
    
    @kernel    
    def measure(self, point):
        pulse_time = self.Time
        #prepare
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        
        # set freqs/phases
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1 , 0.0, self.t0, 0)            
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2 , 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3 , 0.0, self.t0, 0)
       
        # perform experiment
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(5*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT        
        self.ThPh.set_field()        
        self.ThPh.threePhoton_pulse(pulse_time)
        
    
        # image
        if self.Shelf:
            self.MOTs.shelf()
        self.MOTs.push()
        self.MOTs.take_MOT_image(self.Camera)
        
        
    
        #process and output
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm
        delay(50*ms)
        self.Camera.process_image(save=True, name=self.ind, bg_sub=True)
        self.ind += 1
        delay(400*ms)        
        return self.Camera.get_push_stats()
    
    
    def calculate_dim0(self, dim1_model):
        param = dim1_model.fit.params.x0
        # weight final fit by error in this dimension 1 fit param
        error = dim1_model.fit.errs.x0_err
        return param, error

