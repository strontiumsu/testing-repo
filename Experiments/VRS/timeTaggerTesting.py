# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 11:01:45 2024

@author: ejporter
"""


import sys
sys.path.append("C:\Program Files\Swabian Instruments\Time Tagger\driver\python")
import TimeTagger

from time import sleep
from artiq.experiment import *

class time_tagger_cavity_scan(EnvExperiment):
    
    def build(self):
        
        self.setattr_device("core")
        self.setattr_device("ttl1") 
        
        self.tagger = None
        self.time_stream = None
    
    
    def run(self):
        self.prepare_tagger()
        sleep(1)
        self.process_results()
        

            
    def process_results(self):
        data = self.time_stream.getData()
        print(len(data.getTimestamps()))
        TimeTagger.freeTimeTagger(self.tagger)

        
    def prepare_tagger(self):
        self.tagger = TimeTagger.createTimeTagger()
        self.tagger.setTriggerLevel(1, 0.1)
        
        
        gated_channel = TimeTagger.GatedChannel(self.tagger,2,1,-1)
        
        self.time_stream = TimeTagger.TimeTagStream(tagger=self.tagger,
                                          n_max_events=1e7,
                                          channels=[gated_channel.getChannel()])
        
        
        
       
        

        
        