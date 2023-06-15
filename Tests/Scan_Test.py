# # -*- coding: utf-8 -*-
# """
# Created on Wed Dec 14 12:25:08 2022

# @author: sr
# """

from scan_framework import Scan1D, TimeFreqScan, FitGuess # import scan framework library
from artiq.experiment import EnvExperiment, kernel, MHz, us, EnumerationValue
import numpy as np


from repository.models.scan_models import MyModel  # here we pre define user models

class MyScan(Scan1D, TimeFreqScan, EnvExperiment): # note python works from left to right with inheritances
    
    def build(self, **kwargs):
        # required attrs, calls the core + scheduler
        super().build(**kwargs)
        
        
        self.setattr_argument('transition', EnumerationValue(['1', '2', '3', '4', '5']))
        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.scan_arguments(frequencies={
            'start':-30*MHz,
            'stop':30*MHz,
            'npoints':50,
            'unit':"MHz",
            'scale':MHz,
            'global_step':0.1*MHz,
            'ndecimals':2},      
            
            times = {'start':0*us,
            'stop':20*us,
            'npoints':50,
            'unit':"us",
            'scale':us,
            'global_step':0.1*us,
            'ndecimals':2},
            
            frequency_center={'default':500*MHz},
            pulse_time= {'default':0*us},
            nbins = {'default':1000},
            nrepeats = {'default':5},
            npasses = {'default':1},
            fit_options = {'default': "Fit and Save"}
        
            )


        self.setattr_argument('guess_x0', FitGuess(
            fit_param='x0',
            default=500*MHz,
            scale=MHz,
            unit="MHz",
            use=True, #ask, True, or False
            step=1
        ))
   
            
        
        # source of randomness for testing
        self.rands = list(np.random.normal(1, 0.3, 10000)) # artificial noise for testing

    def prepare(self):
        # self._x_offset = 0*MHz # use to offset data by fixed amount, not reflected on plot
       
        self.model = MyModel(self, transition = int(self.transition))
        # self.model.mirror = False # turn to True to disable mirroring to current_scan namespace
        self.enable_histograms = True
        self.register_model(self.model, measurement=True, fit=True)
        
    @kernel
    def measure(self, time, frequency):

        # needs to return a integer
        
        # source of randomness if we want
        r = self.rands[0]
        self.rands = self.rands[1:]

        # experiment
        freq_dep = 50000/((500-frequency/10**6)**2+50)
        time_dep = np.cos(2*np.pi*1e5*time)
        
        return int(freq_dep*time_dep*r)
    
    def after_scan_point(self, i_point, point):
        pass
    
    @kernel
    def cleanup(self):
        pass
    
    def before_fit(self, model):
        pass
    
    
    def after_fit(self, fit_name, valid, saved, model):
        # print(model.fit)
        print(f"Fit: {fit_name}.    Fit Valid: {valid}.    Fit Saved: {saved}.")
        if valid:
            if self.model.type == 'frequency':
                print(f"center freq: {np.round(model.fit.x0*1e-6, 2)} MHz")
            if self.model.type == 'time':
                print(f"freq: {np.round(model.fit.f*1e-6, 2)} MHz")
            self.set_dataset('current_scan.plots.error', model.errors, broadcast=True, persist=True)
    
    def report_fit(self, model):
        pass
    

 
"""
Features not yet figured out:
auto_tracking
warmup points
default values
sub scans
histograms
2D scans
point calculation functions
init_datasets
"""       

