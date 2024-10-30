# -*- coding: utf-8 -*-
"""
Created on Tue Sep 26 12:01:02 2023

@author: sr
"""


from artiq.experiment import *


from CoolingClass import _Cooling
from CameraClass import _Camera
from ThreePhotonClass import _ThreePhoton


class TestingMogLabsOffTime(EnvExperiment):

    def build(self):
        # required initializations

        self.setattr_device("core")
        self.setattr_device("scheduler")



        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)


    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.Camera.camera_init()


    @kernel
    def run(self):
        # runs before experiment take place
        self.core.reset()
        self.MOTs.init_coils()
        delay(1000*ms)
        # self.MOTs.dac4_low()
        for _ in range(5):
            self.MOTs.dac_set(4, -1.0)
            delay(100*ms)
            self.MOTs.dac_set(4, 0.0)
            delay(100*ms)



        # self.MOTs.take_background_image_exp(self.Camera)
        #
