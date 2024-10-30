# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 14:52:33 2023

@author: E. Porter
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")

from artiq.experiment import EnvExperiment, kernel, delay, ms
from CameraClass import _Camera
import numpy as np




class NewCameraTest(EnvExperiment):

    def build(self):



        self.setattr_device('core')
        self.Camera = _Camera(self)



    def prepare(self):
        self.Camera.camera_init()

    @kernel
    def run(self):
        self.core.reset()

        self.Camera.arm()
        delay(175*ms)
        self.Camera.take_background()
        delay(200*ms)
        for i in range(10):
            self.Camera.arm()
            delay(175*ms)
            self.Camera.take_picture(bg_sub=True)
            delay(500*ms)
