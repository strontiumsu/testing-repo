# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 14:21:08 2023

@author: E. Porter
"""


from artiq.experiment import EnvExperiment, kernel, ms, delay, NumberValue

# imports
from CoolingClass import _Cooling
from CameraClass import _Camera


class TrapLoadingOpt_exp(EnvExperiment):
    """
    TrapLoadingOpt

    pseudo code:
        takes in starting point for bias coils with non zero output signal
        scans one direction (perp to cavity axis) and measures loading to the dipole trap
        fits and finds peak, sets this value as fixed
        scans second direction per to cavity axis
        fits and find second peak

        outputs optimal value for voltage in these two directions

        could use the NIST scan framework if we wanted to get fancy with it
        I havent used it before to run two seperate scans but this definitely can be done

        might be nice to use the autotracking built in the scan framework as well

    """



    def build(self):
        self.setattr_device("core")
        self.MOTs = _Cooling
        self.Camera = _Camera

        for direc in ['X','Y','Z']:
            self.setattr_argument(f"Bias_{direc}_start", NumberValue(0,min=-5,max=5,scale=1,
                      unit="V"),"parameters")









    def prepare(self):
        self.MOTs.prepare_aoms()



    @kernel
    def run(self):
        self.startup() # general start up procedure for cooling based exps





    @kernel
    def startup(self):
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)

        delay(50*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(200*ms)

    @kernel
    def measure(self):
        """
        measures the success of the loading of the dipole.
        Not sure if this should take a photo, measure fluorescence,
        or some other metric that might be more useful.
        """
