
from artiq.experiment import *
import numpy as np


class KernelTimingTest(EnvExperiment):
    
    def build(self, **kwargs):
        
        self.setattr_device("core")
        self.setattr_device("scheduler")


        self.test_vals = np.array([1,10,5,7,6,2,8], dtype=np.int32)
     
        
    def prepare(self):
        pass
             
    
    def run(self):
        self.start_exp()  
        print(self.test_vals)
        
        self.run_exp()
        print(self.test_vals)
        
        self.sort_list()   
        print(self.test_vals)

       
    def sort_list(self):
        self.test_vals = self.test_vals[np.argsort(self.test_vals)]
    
    @kernel 
    def start_exp(self):
        self.core.reset()
        
    @kernel
    def run_exp(self):
        self.test_vals[0] = 100

