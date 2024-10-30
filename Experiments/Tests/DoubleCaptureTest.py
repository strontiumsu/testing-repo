# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 16:58:16 2024

@author: ejporter
"""

from artiq.experiment import *

import numpy as np
from NewCamera import _Camera2


class DoubleCapture_exp(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.Camera = _Camera2(self)



    def prepare(self):
        self.Camera.camera_init(cam_range=(150,-220,150,-100))



    @kernel
    def run(self):
        self.core.reset()




        self.Camera.arm(N=10)
        delay(200*ms)
        for i in range(4):


            self.Camera.trigger_camera()
            delay(50*ms)

            if (i%2==0):
                self.Camera.trigger_camera()
                delay(50*ms)


            self.core.wait_until_mu(now_mu())
            self.Camera.process_image(bg_sub=(i%2==0))




            delay(1000*ms)




    def process(self):
        self.Camera.acquire(N=2)
        current_image = np.copy(self.Camera.cam.get_all_images()[0])
        self.Camera.set_dataset("detection.images.current_image", current_image, broadcast=True)
        print('out\n')
