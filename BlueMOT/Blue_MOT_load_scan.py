# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 12:20:34 2023

@author: sr
"""


# imports
from scan_framework import Scan1D, TimeScan
from artiq.experiment import EnvExperiment, delay, ms, us, NumberValue, BooleanValue, kernel, parallel,RTIOUnderflow
import numpy as np

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from DetectionClass import _Detection
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689


## add custom model to the repository.models folder
from repository.models.scan_models import LoadingModel


class Blue_MOT_load_scan(Scan1D, TimeScan, EnvExperiment):

    def build(self, **kwargs):
        
        # calls core and scheduler initialization
        super().build(**kwargs)
        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking = False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks
        
        self.Detect=_Detection(self)
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
                
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
        
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
            
        self.setattr_argument("Detection_attenuation",NumberValue(6.0,min=0.0,max=30.0,scale = 1,
                      unit="dBm"),"Detection")
        
               
        ## < TIME/FREQ SCAN > ##
        
        self.scan_arguments(times = {'start':0.0*1e-3,
            'stop':500*1e-3,
            'npoints':20,
            'unit':"ms",
            'scale':ms,
            'global_step':1*us,
            'ndecimals':2},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "Fit and Save"}
            )
        
        
        
        ## < OPTIONAL PARAMETER GUESSES > ##
        
        # self.setattr_argument('guess_NAME', FitGuess(
        #     fit_param='PARAM',
        #     default=DEFAULT,
        #     scale=SCALE,
        #     unit="UNIT",
        #     use=True, #ask, True, or False
        #     step=1
        # ))
        
    
    
    def prepare(self):

        self.MC.Blackman_pulse_profile()
        self.BB.set_atten()
        self.BR.set_atten()
        self.Detect.camera_init()

        self.enable_histograms = True  
        self.model = LoadingModel(self)
        # # self.model.mirror = False  # uncomment to stop mirroring to current_scan
        self.register_model(self.model, measurement=True, fit=True)
        
        

        

    
    @kernel
    def measure(self, point):
        
        self.Detect.arm()
        delay(100*ms)

        ###########################
        self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)  # Set 3D MOT frequency for loading
        delay(1*ms)
        self.BR.repumpers_on() # turn on repumpers
        delay(1*ms)
        self.MC.Blackman_ramp_up()
        delay(1*ms)
        self.BB.Zeeman_on()
        delay(1*ms)
        self.BB.MOT2D_on() # Turn on atom beam
        delay(1*ms)
        self.BB.MOT_on()
        
        delay(point)  # Delay
        
        with parallel:
            self.BB.Zeeman_off()
            self.BB.MOT2D_off() # turn off atom beam
            self.BB.MOT_off() #turn off 3D 
            self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect) # switch to detection frequency
            self.MC.Set_current(0.0) #ramp down Blue mot coils 
  
        # IMAGING SEQUENCE
        #self.BR.repumpers_on() # turn on repumpers
        self.Detect.trigger_camera()  # Trigger 
        self.BB.MOT_on()
        delay(self.Detection_pulse_time)
        self.BB.MOT_off()
        delay(self.Detect.Exposure_Time)
        self.BR.repumpers_off() # turn off repumpers
        ###########################
        self.MC.Set_current(0.0)
        
        self.Detect.acquire()                                # Acquire images
        delay(100*ms)
        val = self.Detect.transfer_image_background_subtracted(0)
        delay(100*ms)
        self.Detect.disarm() 
        delay(500*ms)
        return int(val) if int(val) > 0 else 0
       
        
        
        
    @kernel
    def before_scan(self):
        self.core.reset()   
                                                   
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.BR.init_aoms()
        
        self.Detect.prep_datasets(np.full(1, np.nan))
        delay(3000*ms)
        
        self.Detect.arm()
        delay(500*ms)
        self.BB.MOT2D_off()  # turn off 2D MOT beam
        delay(1*ms)
        self.BB.Zeeman_off()
        delay(1*ms)
        
        self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for imaging
        delay(10*ms)
        self.BR.repumpers_on() # turn on repumpers
        self.Detect.trigger_camera()    # Trigger camera
        self.BB.MOT_on() #turn on mot for background image
        delay(self.Detection_pulse_time)
        self.BB.MOT_off()
        delay(self.Detect.Exposure_Time)
        self.BR.repumpers_off() # turn off repumpers
        self.Detect.acquire()     # Acquire images
        delay(100*ms)
        self.Detect.transfer_background_image(0)
        delay(300*ms)
        #prepare for detection image
       


        
    @kernel
    def after_scan(self):
        delay(200*ms)
        self.MC.Zero_current()

      

        
    
    
