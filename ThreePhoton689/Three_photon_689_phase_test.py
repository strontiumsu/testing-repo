# -*- coding: utf-8 -*-
"""
Created on Mon Sep 19 18:00:51 2022

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import *
import numpy as np    
   
from ThreePhoton689Class import _ThreePhoton689 
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING

class Three_photon_689_phase_test(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl7")
        self.th_ph=_ThreePhoton689(self)
        
        
        
        self.setattr_argument("t_pulse",NumberValue(1.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale = 1e-6,
                      unit="us"),"Args")
        
        self.setattr_argument("t_wait",NumberValue(1.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale = 1e-6,
                      unit="us"),"Args")

        self.setattr_argument("phase_scan",BooleanValue(False),"Args")
        
    def prepare(self):  
        self.th_ph.set_atten()

        
    @kernel    
    def run(self):
        # general inicialization
        self.core.reset()
        self.core.break_realtime()
        self.th_ph.init_aoms()
        
        self.th_ph.urukul_meas[0].set_phase_mode(PHASE_MODE_TRACKING)
        self.th_ph.urukul_meas[1].set_phase_mode(PHASE_MODE_TRACKING)
        self.th_ph.urukul_meas[2].set_phase_mode(PHASE_MODE_TRACKING)
        
        
        self.th_ph.urukul_meas[0].sw.off()
        self.th_ph.urukul_meas[1].sw.off()
        self.th_ph.urukul_meas[2].sw.off()

        self.ttl7.off()
        
        
        nreps = 100
        for ii in range(nreps):
            
            ph = ii/nreps
            phpow = self.th_ph.urukul_meas[0].turns_to_pow(ph)
            
            t = now_mu()
            
            self.th_ph.urukul_meas[0].set(85*MHz,phase=0.0,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = 0)
            #self.th_ph.urukul_meas[0].cpld.set_profile(0)
            #self.th_ph.urukul_meas[0].cpld.io_update.pulse_mu(8)
            
            # if self.phase_scan:
            #      self.th_ph.urukul_meas[0].set(85*MHz,phase=ph,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = 1)
            # else:
            self.th_ph.urukul_meas[0].set(85*MHz,phase=0.50,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = 1)
            #self.th_ph.urukul_meas[0].cpld.set_profile(1)
            #self.th_ph.urukul_meas[0].cpld.io_update.pulse_mu(8)


            self.th_ph.urukul_meas[1].set(86*MHz,phase=0.0,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = 0)
            self.th_ph.urukul_meas[1].set(86*MHz,phase=0.0,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = 1)
            self.th_ph.urukul_meas[2].set(93*MHz,phase=0.0,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = 0)
            self.th_ph.urukul_meas[2].set(93*MHz,phase=0.0,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = 1)
            delay(1*ms)

            
            self.th_ph.urukul_meas[0].cpld.set_profile(0)
            
            with parallel:
                self.ttl7.on()
                self.th_ph.switch1_on()
                self.th_ph.switch2_on()
                self.th_ph.switch3_on()

            with parallel:
                delay(self.t_pulse)
                #self.ttl7.off()
            
            with parallel:
                self.th_ph.switch1_off()
                #self.th_ph.switch2_off()
                self.th_ph.switch3_off()
                #self.th_ph.set_switch1_phase_freq(91*MHz,ph,t)
                #self.th_ph.set_switch1_phase_freq_mu(91*MHz,ph,t)
                #self.th_ph.urukul_meas[0].set(91*MHz,phase=ph,ref_time_mu=t)
                #self.th_ph.urukul_meas[0].set_mu(ftw = self.th_ph.urukul_meas[0].frequency_to_ftw(self.th_ph.switch1_689_3nu_frequency),
                #                                 pow = 0,
                #                                 asf=self.th_ph.urukul_hmc_ref_switch1_689_3nu.amplitude_to_asf(self.th_ph.switch1_689_3nu_dds_scale),
                #                                 phase_mode=PHASE_MODE_TRACKING,ref_time=t)
                #self.th_ph.urukul_meas[0].set(91*MHz,phase=ph, ref_time_mu=t)
                #self.th_ph.urukul_meas[0].set_pow(phpow)
            #self.th_ph.urukul_meas[0].cpld.set_profile(1)
                #self.th_ph.urukul_meas[0].set_phase(ph)
                #self.th_ph.urukul_meas[1].set_phase(0.0)
                #self.th_ph.urukul_meas[2].set_phase(0.0)
            
            self.th_ph.urukul_meas[0].cpld.set_profile(1)
                
            delay(self.t_wait)
            #if ii == 2000:
            #    print(self.th_ph.urukul_meas[0].turns_to_pow(ph))
            #     print(self.th_ph.urukul_meas[0].get_phase())
            #     print(self.th_ph.urukul_meas[1].get_phase())
            #     print(self.th_ph.urukul_meas[1].get_phase())
                
            
            #delay(self.t_wait)
            #self.ttl7.off()

            with parallel:
                self.th_ph.switch1_on()
                #self.th_ph.switch2_on()
                self.th_ph.switch3_on()

            with parallel:
                delay(self.t_pulse)
                #self.ttl7.off()
            
            with parallel:
                self.th_ph.switch1_off()
                self.th_ph.switch2_off()
                self.th_ph.switch3_off()
            
            self.ttl7.off()
            delay(100*ms)
            
        self.th_ph.switch1_on()
        self.th_ph.switch2_on()
        self.th_ph.switch3_on()