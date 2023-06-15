# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 14:31:54 2022

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, BooleanValue, kernel, Scannable, RangeScan, NoScan, NumberValue, delay, ms
import numpy as np    
from MOTCoilsClass import _MOTCoils
from DetectionClass import _Detection
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689


class Blue_MOT_Data_Collection(EnvExperiment):
    
    def build(self): 
        
        # initialize classes and hardware
        self.setattr_device("core")
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
        self.Detect=_Detection(self)
        
        # intialize sampler
        self.setattr_device("sampler0")
        self.adc_0=self.get_device("sampler0")

        # arguments
        self.setattr_argument("repumper_3P0_on",BooleanValue(True),"Repumpers")
        self.setattr_argument("repumper_3P2_on",BooleanValue(True),"Repumpers")
        self.setattr_argument("push_beam",BooleanValue(False),"Loading")  # dont think i need this
        
        # parameters to sweep over
        self.setattr_argument("Mot_frequency", Scannable(default=[RangeScan(85*1e6, 
                     100*1e6,10, randomize=False), NoScan(97*1e6)], scale=1e6),"Params")
        self.setattr_argument("Mot_attenuation",
            Scannable(default=[RangeScan(3.0,15.0,10, randomize=False),NoScan(6.0)],scale=1,
                      unit="dBm"),"Params")
        self.setattr_argument("Data_points",NumberValue(10,min=1,max=1000, scale=1), "Params")
        
        # Detection/PD settings
        self.setattr_argument("Detection_pulse_time",NumberValue(0.1*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        self.setattr_argument("PD_delay",NumberValue(1*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"PD")
        self.setattr_argument("samples",NumberValue(10,min=1.0,max=100,scale = 1),"PD")
        
        
        
# 
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()  # what default values does this use, does it do anything other than setting a variable
        self.BR.set_atten()
        # Initialize camera
        self.Detect.camera_init()
        self.y=np.full(int(self.Data_points), np.nan)
        self.freqs = self.Mot_frequency.sequence 
        self.attens = self.Mot_attenuation.sequence

    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        self.BB.init_aoms()  # Initialize AOMs  # does this turn them on or just prepare them
        self.BR.init_aoms()
        self.adc_0.init()
        
        
        self.set_dataset('V', self.y, broadcast = True)
        self.set_dataset('Power', self.y, broadcast = True)
        
        
        self.Detect.prep_datasets(self.y)
        self.set_dataset('freq_data', self.y, broadcast = True)
        self.set_dataset('atten_data', self.y, broadcast = True)
        
        delay(100*ms)
        self.BB.MOT2D_off()  # turn off 2D MOT beam
        delay(1*ms)
        self.BB.Zeeman_off()
        delay(1*ms)
        self.BB.Probe_AOM_off()
        self.BR.Hp688_aom_off()
        delay(1*ms)
        delay(1000*ms)
        jj = -1
        for freq in self.freqs:
            for atten in self.attens:
                jj +=1
                # randomly select freq, atten in range
                # freq_num, atten_num = np.random.randint(0,100, 2)
    
    
                
                self.mutate_dataset("freq_data", jj, freq)
                
                self.mutate_dataset("atten_data", jj, atten)
                delay(100*ms)
                self.BB.reinit_MOT3DDP_aom(atten, freq)
                delay(100*ms)
                self.BR.repumpers_on()
                delay(1*ms)
                self.MC.Blackman_ramp_up()
                delay(1*ms)
                self.BB.Zeeman_on()
                delay(1*ms)
                self.BB.MOT2D_on()
                delay(1*ms)
                self.BB.MOT_on()
                
                self.Detect.arm()
                delay(1500*ms)
                
                v, p =  self.sample_ADC()
                self.mutate_dataset("V", jj, v)
                self.mutate_dataset("Power", jj, p)
                delay(5*ms)
                
                self.Detect.trigger_camera()
                delay(self.Detect.Exposure_Time)
                self.BB.MOT_off()
                self.BR.repumpers_off()
                delay(1*ms)
                self.MC.Set_current(0.0)
                self.Detect.acquire()
                delay(100*ms)
                self.Detect.transfer_image(jj)
                delay(100*ms)
                self.Detect.disarm()
                self.mutate_dataset('detection.index', jj, jj)
            
        delay(500*ms)
        self.MC.Zero_current()
            
    @kernel 
    def sample_ADC(self):
        res = 0.
        res2 = 0.
        CHANNELS = 8
        dat=[0.1 for _ in range(CHANNELS)]
        for jj in range(int(self.samples)):
            self.adc_0.sample(dat)
            res += float(dat[0])
            res2 += float(dat[6])
            delay(self.PD_delay)
        return res/self.samples, res2/self.samples     
        
    def analyze(self):
        pass