# -*- coding: utf-8 -*-
"""
Created on Mon Aug 28 15:09:34 2023

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 11:17:41 2023

@author: E. Porter
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, kernel, ms,us, NumberValue, delay, parallel, now_mu,BooleanValue

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera


class Vacuum_Rabi_exp(EnvExperiment):
    """
    Vacuum_Rabi_exp
    This experiment uses the CoolingClass to control the relevant AOMs and MOT
    coils to pulse the Red MOT off and on, taking an image each time to display to the user
    at detection.images.current_image.

    parameters:
        <all parameters inherited from CoolingClass>
        <all parameters inherited from Detection2>
        pulses: number of times to pulse the red MOT
        wait_time: how long to wait between pulses

    """

    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)


        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("dipole_load_time", NumberValue(15.0*1e-3,min=1.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("scan_duration", NumberValue(15.0*1e-3,min=1.0*1e-3,max=100.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("scan_amplitude", NumberValue(1.0,min=0.1,max=1.0,scale=1,
                      unit="V"),"parameters")


    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms(int(self.pulses*1.2))
        self.MOTs.prepare_coils()

        # Initialize camera
        self.Camera.camera_init()



    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        
        delay(50*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(500*ms)

        for _ in range(int(self.pulses)):
            self.Camera.arm()
            delay(200*ms)

            self.MOTs.rMOT_pulse()
            self.MOTs.set_current_dir(1) # XXX let MOT field go to zero and switch H-bridge, 5ms
            delay(5*ms)
            self.MOTs.set_current(0.1)
            delay(self.dipole_load_time) ##load into dipole trap if desired
            
            #scan to get rabi splitting
            self.MOTs.freq_ramp(self.scan_amplitude, self.scan_duration, 100)
            
            #image cloud just for visual of atom number
            self.MOTs.take_MOT_image(self.Camera)
            delay(15*ms)
            self.MOTs.set_current(0.0)
            delay(5*ms)
            self.MOTs.set_current_dir(0)


            # process and output
            delay(50*ms)
            self.Camera.process_image(bg_sub=True)
            delay(300*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D'])


        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.AOMs_on(['Probe'])
        self.MOTs.atom_source_on()
