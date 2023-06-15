# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 16:39:41 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 15:48:49 2022

@author: sr

Functions:

Controls some aspects of the HCDL lock setup    
Sets the parameters of the HCDL MTS AOM and double-pass AOM before the HDCL setup

"""

from artiq.experiment import *
import numpy as np     

from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING

class _ThreePhoton689(EnvExperiment):
      
    
    def build(self):
        
        self.setattr_device("urukul0_cpld")
        
        # Offset AOM
        self.setattr_argument("switch1_689_3nu_frequency",NumberValue(80.000*1e6,scale=1e6,unit='MHz',ndecimals=5),"Three_photon") 
        self.setattr_argument("switch1_689_3nu_DDS_amplitude_scale",NumberValue(0.8),"Three_photon")
        self.setattr_argument("switch1_689_3nu_DDS_attenuation",NumberValue(4.0),"Three_photon")
     
    
        # 679 DP AOM
        
        self.setattr_argument("switch2_689_3nu_frequency",NumberValue(80.000*1e6,scale=1e6,unit='MHz',ndecimals=5),"Three_photon") 
        self.setattr_argument("switch2_689_3nu_DDS_amplitude_scale",NumberValue(0.8),"Three_photon")
        self.setattr_argument("switch2_689_3nu_DDS_attenuation",NumberValue(9.0),"Three_photon")
        
        # 679 switch AOM
        self.setattr_argument("switch3_689_3nu_frequency",NumberValue(80.000*1e6,scale=1e6,unit='MHz',ndecimals=5),"Three_photon") # ramp duration
        self.setattr_argument("switch3_689_3nu_DDS_amplitude_scale",NumberValue(0.8),"Three_photon")
        self.setattr_argument("switch3_689_3nu_DDS_attenuation",NumberValue(9.0),"Three_photon")

        # 689 DP AOM
        
        self.setattr_argument("DP_689_AOM_frequency",NumberValue(80.000*1e6,scale=1e6,unit='MHz'),"Three_photon") # ramp duration
        self.setattr_argument("DP_689_AOM_DDS_amplitude_scale",NumberValue(0.8),"Three_photon")
        self.setattr_argument("DP_689_AOM_DDS_attenuation",NumberValue(4.0),"Three_photon")
        

        self.urukul_hmc_ref_switch1_689_3nu = self.get_device("urukul0_ch0")
        self.urukul_hmc_ref_switch2_689_3nu = self.get_device("urukul0_ch1")
        self.urukul_hmc_ref_switch3_689_3nu = self.get_device("urukul0_ch2")
        self.urukul_hmc_ref_DP_689_AOM = self.get_device("urukul0_ch3")
        
        self.urukul_meas = [self.get_device("urukul0_ch0"),self.get_device("urukul0_ch1"),self.get_device("urukul0_ch2"),self.get_device("urukul0_ch3")]

        
    def set_atten(self):
        
        self.switch1_689_3nu_dds_scale=self.switch1_689_3nu_DDS_amplitude_scale
        self.switch1_689_3nu_iatten=self.switch1_689_3nu_DDS_attenuation
        
        self.switch2_689_3nu_dds_scale=self.switch2_689_3nu_DDS_amplitude_scale
        self.switch2_689_3nu_iatten=self.switch2_689_3nu_DDS_attenuation
        
        self.switch3_689_3nu_dds_scale=self.switch3_689_3nu_DDS_amplitude_scale
        self.switch3_689_3nu_iatten=self.switch3_689_3nu_DDS_attenuation
        
        self.DP_689_AOM_dds_scale=self.DP_689_AOM_DDS_amplitude_scale
        self.DP_689_AOM_iatten=self.DP_689_AOM_DDS_attenuation
      
    @kernel    
    def init_aoms(self):
        
        delay(1*ms)
        self.urukul0_cpld.init()
        
        self.urukul_hmc_ref_switch1_689_3nu.init()
        self.urukul_hmc_ref_switch1_689_3nu.set_mu(0x40000000, asf=self.urukul_hmc_ref_switch1_689_3nu.amplitude_to_asf(self.switch1_689_3nu_dds_scale))
        self.urukul_hmc_ref_switch1_689_3nu.set_att(self.switch1_689_3nu_iatten)
        self.urukul_hmc_ref_switch1_689_3nu.sw.on()
            
        self.urukul_hmc_ref_switch2_689_3nu.init()
        self.urukul_hmc_ref_switch2_689_3nu.set_mu(0x40000000, asf=self.urukul_hmc_ref_switch2_689_3nu.amplitude_to_asf(self.switch2_689_3nu_dds_scale))
        self.urukul_hmc_ref_switch2_689_3nu.set_att(self.switch2_689_3nu_iatten)
        self.urukul_hmc_ref_switch2_689_3nu.sw.on()
            
        self.urukul_hmc_ref_switch3_689_3nu.init()
        self.urukul_hmc_ref_switch3_689_3nu.set_mu(0x40000000, asf=self.urukul_hmc_ref_switch3_689_3nu.amplitude_to_asf(self.switch3_689_3nu_dds_scale))
        self.urukul_hmc_ref_switch3_689_3nu.set_att(self.switch3_689_3nu_iatten)
        self.urukul_hmc_ref_switch3_689_3nu.sw.on()
        
        self.urukul_hmc_ref_DP_689_AOM.init()
        self.urukul_hmc_ref_DP_689_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_DP_689_AOM.amplitude_to_asf(self.DP_689_AOM_dds_scale))
        self.urukul_hmc_ref_DP_689_AOM.set_att(self.DP_689_AOM_iatten)
        self.urukul_hmc_ref_DP_689_AOM.sw.on()
        
        
        self.set_switch1_689_3nu_frequency()
        self.set_switch2_689_3nu_frequency()
        self.set_switch3_689_3nu_frequency()
        self.set_DP_689_frequency()
        
    @kernel    
    def init_aoms_phase(self,t):
        
        delay(1*ms)
        self.urukul0_cpld.init()

        self.urukul_hmc_ref_switch1_689_3nu.init()
        self.urukul_hmc_ref_switch1_689_3nu.set_mu(0x40000000, asf=self.urukul_hmc_ref_switch1_689_3nu.amplitude_to_asf(self.switch1_689_3nu_dds_scale))
        self.urukul_hmc_ref_switch1_689_3nu.set_att(self.switch1_689_3nu_iatten)
        self.urukul_hmc_ref_switch1_689_3nu.set(self.switch1_689_3nu_frequency,phase=0.0, ref_time_mu=t)
            
        self.urukul_hmc_ref_switch2_689_3nu.init()
        self.urukul_hmc_ref_switch2_689_3nu.set_mu(0x40000000, asf=self.urukul_hmc_ref_switch2_689_3nu.amplitude_to_asf(self.switch2_689_3nu_dds_scale))
        self.urukul_hmc_ref_switch2_689_3nu.set_att(self.switch2_689_3nu_iatten)
        self.urukul_hmc_ref_switch2_689_3nu.set(self.switch2_689_3nu_frequency,phase=0.0, ref_time_mu=t)
            
        self.urukul_hmc_ref_switch3_689_3nu.init()
        self.urukul_hmc_ref_switch3_689_3nu.set_mu(0x40000000, asf=self.urukul_hmc_ref_switch3_689_3nu.amplitude_to_asf(self.switch3_689_3nu_dds_scale))
        self.urukul_hmc_ref_switch3_689_3nu.set_att(self.switch3_689_3nu_iatten)
        self.urukul_hmc_ref_switch3_689_3nu.set(self.switch3_689_3nu_frequency,phase=0.0, ref_time_mu=t)
        #self.urukul_hmc_ref_switch3_689_3nu.sw.on()
        
    @kernel    
    def set_switch1_phase_freq_profile(self,freq,ph,t,prof=0):
        self.urukul_meas[0].set(freq, phase=ph,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = prof)
    @kernel    
    def set_switch2_phase_freq_profile(self,freq,ph,t,prof=0):
        self.urukul_meas[1].set(freq,phase=ph,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = prof)
    @kernel    
    def set_switch3_phase_freq_profile(self,freq,ph,t,prof=0):
        self.urukul_meas[2].set(freq,phase=ph,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = prof)
          
    @kernel 
    def set_switch1_689_3nu_frequency(self): 
        
        fswitch1 = self.switch1_689_3nu_frequency
        urukul_ch =self.urukul_meas[0]
        dds_ftw_switch1_689_3nu=self.urukul_meas[0].frequency_to_ftw(fswitch1)
        urukul_ch.set_mu(dds_ftw_switch1_689_3nu, asf=urukul_ch.amplitude_to_asf(self.switch1_689_3nu_DDS_amplitude_scale))   
        
    @kernel 
    def set_switch1_689_3nu_freq(self,f): 
        
        fswitch1 = f
        urukul_ch =self.urukul_meas[0]
        dds_ftw_switch1_689_3nu=self.urukul_meas[0].frequency_to_ftw(fswitch1)
        urukul_ch.set_mu(dds_ftw_switch1_689_3nu, asf=urukul_ch.amplitude_to_asf(self.switch1_689_3nu_DDS_amplitude_scale))        
    
    @kernel 
    def set_switch1_phase(self,ph,t):
        self.urukul_meas[0].set(self.switch1_689_3nu_frequency,phase=ph, ref_time_mu=t)
        
    @kernel 
    def set_switch1_phase_freq(self,freq,ph,t):
        self.urukul_meas[0].set(freq,phase=ph, ref_time_mu=t)
        
    @kernel 
    def set_switch1_phase_freq_mu(self,freq,ph,t):
        dds_ftw_switch1_689_3nu=self.urukul_meas[0].frequency_to_ftw(freq)
        phpow = self.urukul_meas[0].turns_to_pow(ph)
        self.urukul_meas[0].set_mu(dds_ftw_switch1_689_3nu, pow_ = phpow, 
                                   asf=self.urukul_meas[0].amplitude_to_asf(self.switch1_689_3nu_DDS_amplitude_scale),
                                   ref_time_mu = t) 
        
        #self.urukul_meas[0].set(freq,phase=ph, ref_time_mu=t)
        
    @kernel 
    def switch1_on(self):
        self.urukul_meas[0].sw.on() 

    @kernel
    def switch1_off(self):
        self.urukul_meas[0].sw.off()   
        
    @kernel 
    def switch_profile(self,prof=0):
        self.urukul_meas[0].cpld.set_profile(prof)
        
    @kernel 
    def set_switch2_689_3nu_frequency(self): 
        
        fswitch2 = self.switch2_689_3nu_frequency
        urukul_ch =self.urukul_meas[1]
        dds_ftw_switch2_689_3nu=self.urukul_meas[1].frequency_to_ftw(fswitch2)
        urukul_ch.set_mu(dds_ftw_switch2_689_3nu, asf=urukul_ch.amplitude_to_asf(self.switch2_689_3nu_DDS_amplitude_scale))   
        
        
    @kernel 
    def set_switch2_689_3nu_freq(self,f): 
        
        fswitch2 = f
        urukul_ch =self.urukul_meas[1]
        dds_ftw_switch2_689_3nu=self.urukul_meas[1].frequency_to_ftw(fswitch2)
        urukul_ch.set_mu(dds_ftw_switch2_689_3nu, asf=urukul_ch.amplitude_to_asf(self.switch2_689_3nu_DDS_amplitude_scale))      
    
    @kernel 
    def set_switch2_phase(self,ph,t):
        self.urukul_meas[1].set(self.switch2_689_3nu_frequency,phase=ph, ref_time_mu=t)
    
    @kernel 
    def set_switch2_phase_freq(self,freq,ph,t):
        self.urukul_meas[1].set(freq,phase=ph, ref_time_mu=t)
        
    @kernel 
    def set_switch2_phase_profile(self,ph,t,prof=0):
        self.urukul_meas[1].set(self.switch2_689_3nu_frequency,phase=ph,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = prof)
        #self.urukul_meas[1].set(self.switch2_689_3nu_frequency,phase=ph, ref_time_mu=t)
    
    @kernel 
    def switch2_on(self):
        self.urukul_meas[1].sw.on() 

    @kernel
    def switch2_off(self):
        self.urukul_meas[1].sw.off() 
 
        
    @kernel 
    def set_switch3_689_3nu_frequency(self): 
        
        fswitch3 = self.switch3_689_3nu_frequency
        urukul_ch =self.urukul_meas[2]
        dds_ftw_switch3_689_3nu=self.urukul_meas[2].frequency_to_ftw(fswitch3)
        urukul_ch.set_mu(dds_ftw_switch3_689_3nu, asf=urukul_ch.amplitude_to_asf(self.switch3_689_3nu_DDS_amplitude_scale))      
        
 
     
    @kernel 
    def set_switch3_689_3nu_freq(self,f): 
        
        fswitch3 = f
        urukul_ch =self.urukul_meas[2]
        dds_ftw_switch3_689_3nu=self.urukul_meas[2].frequency_to_ftw(fswitch3)
        urukul_ch.set_mu(dds_ftw_switch3_689_3nu, asf=urukul_ch.amplitude_to_asf(self.switch3_689_3nu_DDS_amplitude_scale))       
        
    @kernel 
    def set_switch3_phase(self,ph,t):
        self.urukul_meas[2].set(self.switch3_689_3nu_frequency,phase=ph, ref_time_mu=t)
    
    @kernel 
    def set_switch3_phase_freq(self,freq,ph,t):
        self.urukul_meas[2].set(freq,phase=ph, ref_time_mu=t)
        
    @kernel 
    def set_switch3_phase_profile(self,ph,t,prof=0):
        self.urukul_meas[2].set(self.switch3_689_3nu_frequency,phase=ph,phase_mode = PHASE_MODE_TRACKING, ref_time_mu=t, profile = prof)
    
    @kernel 
    def switch3_on(self):
        self.urukul_meas[2].sw.on() 

    @kernel
    def switch3_off(self):
        self.urukul_meas[2].sw.off() 
        
    @kernel
    def set_phase_mode(self, mode):
        self.urukul_meas[0].set_phase_mode(mode)
        self.urukul_meas[1].set_phase_mode(mode)
        self.urukul_meas[2].set_phase_mode(mode)
        
        
    @kernel 
    def set_DP_689_frequency(self): 
        
        f_689_DP = self.DP_689_AOM_frequency
        urukul_ch =self.urukul_meas[3]
        dds_ftw_f_689_DP=self.urukul_meas[3].frequency_to_ftw(f_689_DP)
        urukul_ch.set_mu(dds_ftw_f_689_DP, asf=urukul_ch.amplitude_to_asf(self.DP_689_AOM_dds_scale))
    