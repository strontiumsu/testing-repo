# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 15:13:34 2024

@author: ejporter
"""


from artiq.experiment import *
import numpy as np
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from CameraClass import _Camera
from repository.models.scan_models import TemperatureModel


class BlueMOT_Optimization_exp(EnvExperiment):
    
    def build(self, **kwargs):
        
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        
        
        self.setattr_argument("max_iter", NumberValue(100,min=0, max=10000, ndecimals=0, scale=1, type="int", step=1), "Nedler-Mead")
        
        
        
        # initial values
        # self.setattr_argument("Tcap", NumberValue(1000.0*1e-3,min=0.0*1e-3,max=9000.00*1e-3,scale=1e-3,
        #               unit="ms"),"Initial Values")
        # self.setattr_argument("Tramp", NumberValue(100.0*1e-3,min=0.0*1e-3,max=9000.00*1e-3,scale=1e-3,
        #               unit="ms"),"Initial Values")
        # self.setattr_argument("Thold", NumberValue(50.0*1e-3,min=0.0*1e-3,max=9000.00*1e-3,scale=1e-3,
        #               unit="ms"),"Initial Values")
        
        # self.setattr_argument("Pcap_atten", NumberValue(6.0, min=1.0, max=30.0), "Initial Values")
        # self.setattr_argument("Phold_atten", NumberValue(10.0, min=1.0, max=30.0), "Initial Values")
        
        
        # self.setattr_argument("Bcap",NumberValue(5.0,min=0.0,max=7.0,
        #               unit="A"),"Initial Values") 
        # self.setattr_argument("Bhold",NumberValue(6.0,min=0.0,max=7.0,
        #               unit="A"),"Initial Values") 
        
        # Nelder-mead params
        self.setattr_argument("alpha", NumberValue(1.0, min=0.1, max=30.0), "Nedler-Mead")
        self.setattr_argument("gamma", NumberValue(2.0, min=0.1, max=30.0), "Nedler-Mead")
        self.setattr_argument("rho", NumberValue(0.5, min=0.1, max=30.0), "Nedler-Mead")
        self.setattr_argument("sigma", NumberValue(0.5, min=0.1, max=30.0), "Nedler-Mead")
        
        
        # Pcap, Phold, Tcap, Tramp, Thold, Bcap, Bhold
        self.param_list = np.array([6.0, 10.0, 1000.0, 10.0, 50.0, 5.0, 6.0], dtype=np.float32)
        self.simplex = self.initial_simplex(self.param_list)
        self.simplex_values = np.zeros(len(self.param_list) + 1, dtype=np.int32)
        self.centroid = np.zeros(len(self.param_list), dtype=np.float32)
        self.reflected = np.zeros(len(self.param_list), dtype=np.float32)
        self.contracted_point = np.zeros(len(self.param_list), dtype=np.float32)
        self.extended_point = np.zeros(len(self.param_list), dtype=np.float32)
        self.reflected_val = 0
        self.contracted_val = 0
        self.extended_val = 0

        
        
        
    def prepare(self):
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()

        # Initialize camera
        self.Camera.camera_init()
        
        
    def run(self):
        self.start_exp()
        
        # evaluate each starting point
        self.update_vals()  # keep everything within one kernel
              
        for it in range(self.max_iter):
            self.sort_simplex() # sorts by value at each point 
            self.centroid = np.mean(self.simplex[1:], axis=0) # excludes worst point
            self.reflected = self.centroid + self.alpha*(self.centroid-self.simplex[0])
            self.reflected_val = self.function_call(self.reflected)

            if self.simplex_values[1] < self.reflected_val <= self.simplex_values[-1]:
                self.insert_point(self.reflected_val, self.reflected)
                continue
            
            if self.reflected_val > self.simplex_values[-1]:
                self.extended_point = self.centroid+self.gamma*(self.reflected-self.centroid)
                self.extended_val = self.function_call(self.extended_point)
                
                if self.extended_val > self.reflected_val:
                    self.insert_point(self.extended_val, self.extended_point)
                    continue
                self.insert_point(self.reflected_val, self.reflected)
                continue
                    
            if self.reflected_val > self.simplex_values[0]:
                self.contracted_point = self.centroid + self.rho*(self.reflected-self.centroid)         
                self.contracted_val = self.function_call(self.contracted_point)

                if self.contracted_val > self.reflected_val:
                    self.simplex[0] = self.contracted_point
                    self.simplex_values[0] = self.contracted_val
                    self.sort_simplex()
                    continue
            else:
                self.contracted_point = self.centroid + self.rho*(self.simplex[0]-self.centroid)              
                self.contracted_val = self.function_call(self.contracted_point)
                if self.contracted_val > self.simplex_values[0]:
                    self.simplex[0] = self.contracted_point
                    self.simplex_values[0] = self.contracted_val
                    self.sort_simplex()
                    continue
                

            self.shrink_simplex()
            if self.check_convergence:
                break
        
        self.return_data()
        
        
    @kernel
    def start_exp(self):
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        delay(50*ms)
        self.Camera.arm()
        delay(100*ms)
        self.MOTs.take_MOT_image(self.Camera)
        delay(100*ms)
        self.Camera.process_background()
           
        
    @kernel
    def function_call(self, point) -> TInt32:
        # Pcap, Phold, Tcap, Tramp, Thold, Bcap, Bhold, other = point
        self.core.reset()
        self.Camera.arm()
        delay(200*ms)
        
        self.MOTs.ttl5.on()
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(["3D", "3P0_repump", "3P2_repump"])
        self.MOTs.set_current_dir(0)
        self.MOTs.Blackman_ramp_up(self.MOTs.bmot_current)
        self.MOTs.hold(1000*ms)
        
        
        #with parallel:
        self.MOTs.atom_source_off()        
        self.MOTs.AOMs_off(['3D'])
        
        delay(0.5*us)
        self.MOTs.set_current(self.MOTs.rmot_bb_current)
        self.MOTs.ttl5.off()  # switch on  broadband mode (ch1)
        
        delay(self.MOTs.rmot_bb_duration)
        
        with parallel:
            self.MOTs.AOMs_off(["3P0_repump","3P2_repump"])
            self.MOTs.linear_ramp(self.MOTs.rmot_bb_current, self.MOTs.rmot_sf_current, self.MOTs.rmot_ramp_duration, self.MOTs.Npoints)
            
        with parallel:
            self.MOTs.ttl5.on()
            self.MOTs.ttl6.on()
 
        delay(self.MOTs.rmot_sf_duration)
        self.MOTs.ttl6.off()
        self.MOTs.set_current(0.0)
        
        
        self.MOTs.take_MOT_image(self.Camera)
        delay(10*ms)
        self.Camera.process_image(bg_sub=True)
        self.core.break_realtime()
        
        return self.Camera.get_totalcount_stats()

         
    def sort_simplex(self):
        indices = np.argsort(self.simplex_values)
        self.simplex = self.simplex[indices]
        self.simplex_values = self.simplex_values[indices]


    def initial_simplex(self, start_point):
        scale = np.array([1.0, 1.0, 100.0, 10.0, 5.0, 1.0, 1.0], dtype=np.float32)
        dim = len(start_point)
        simplex = np.zeros((dim+1, dim), dtype=np.float32)
        simplex[0] = start_point
        for i in range(dim):
            move = np.zeros(dim, dtype=np.float32)
            move[i] = scale[i]
            simplex[i+1] = start_point + move
        return simplex
    

    def insert_point(self, val, point):
        ind = np.searchsorted(self.simplex_values, val)
        self.simplex = self.simplex[1:ind] + [point] + self.simplex[ind:]
        self.simplex_values = self.simplex_values[1:ind] + [val] + self.simplex_values[ind:]
        
    def shrink_simplex(self):
        for i in range(len(self.simplex-1)):
            self.simplex[i] = self.simplex[-1] + self.sigma*(self.simplex[i]-self.simplex[-1])
        self.update_vals()
        
    def check_convergence(self):
        return False
        # implemenet for convergence condition later
        # effecively just check the distance between all points in the simplex
        
    def return_data(self):
        self.set_dataset("results.best_point", self.simplex[-1])
    
    @kernel
    def update_vals(self):
        for i in range(len(self.simplex)):
            self.simplex_values[i] = self.function_call(self.simplex[i])

    
    
