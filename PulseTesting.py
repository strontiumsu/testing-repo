from artiq.experiment import *
import time
import numpy as np

class PulseTesting(EnvExperiment):
    
    def build(self):
        self.setattr_device('core')
        self.setattr_device('ttl4')
        self.setattr_argument("pulse_seperation", NumberValue(2e-3,min=0.1e-3,max=4000e-3, unit=
        'ms'),"Params")
        self.setattr_argument("on_time", NumberValue(1e-3,min=0.1e-3,max=10e-3, unit=
        'ms'),"Params")

    @kernel
    def run(self):
        self.core.reset()
        self.ttl4.output()

        
        
        for i in range(10000):
            self.ttl4.pulse(self.on_time)
            delay(self.pulse_seperation)

