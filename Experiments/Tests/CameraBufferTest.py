# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 16:31:28 2023

@author: E. Porter
"""


from artiq.experiment import EnvExperiment, kernel, delay, ms, now_mu
from CameraClass import _Camera
import numpy as np
import time



class CameraBufferTest(EnvExperiment):

    def build(self):



        self.setattr_device('core')
        self.Camera = _Camera(self)
        self.N = 50


    def prepare(self):
        self.Camera.camera_init()

    @kernel
    def run(self):
        self.core.reset()

        self.Camera.arm()
        delay(175*ms)

        for _ in range(self.N):
            self.Camera.trigger_camera()
            delay(3*ms)



        self.core.break_realtime()
        self.process()

    def process(self):
        self.Camera.acquire(self.N)
        imgs = self.Camera.cam.get_all_images()
        print(len(imgs))
        self.Camera.set_dataset("detection.images.current_image", np.copy(imgs[0]), broadcast=True)
        self.Camera.disarm()
