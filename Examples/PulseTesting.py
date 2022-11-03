from artiq.experiment import *
import time
import numpy as np

class PulseTesting(EnvExperiment):
    
    def build(self):
        self.setattr_device('core')
        self.setattr_device('ttl7')
        self.setattr_argument("pulse_seperation", NumberValue(2e-3,min=0.1e-3,max=4000e-3, unit=
        'ms'),"Params")
        self.setattr_argument("on_time", NumberValue(1e-3,min=0.1e-3,max=10e-3, unit=
        'ms'),"Params")

    @kernel
    def run(self):
        self.core.reset()
        self.ttl7.output()

        self.ttl7.off()
        
        for i in range(10000):
            self.ttl7.pulse(self.on_time)
            delay(self.pulse_seperation)
            

