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

class HCDL(EnvExperiment):
      
    
    def build(self):
        
        self.setattr_device("urukul0_cpld")
        
        # Offset AOM
        self.setattr_argument("Offset_AOM_frequency",NumberValue(240*1e6,scale=1e6,unit='MHz'),"Offset_AOM") 
        self.setattr_argument("Offset_AOM_DDS_amplitude_scale",NumberValue(0.8),"Offset_AOM")
        self.setattr_argument("Offset_AOM_DDS_attenuation",NumberValue(4.0),"Offset_AOM")
     
    
        # DP Probe AOMs
        
        self.setattr_argument("DP_AOM_frequency",NumberValue(200*1e6,scale=1e6,unit='MHz'),"MTS_DP_AOM") 
        self.setattr_argument("DP_AOM_DDS_amplitude_scale",NumberValue(0.8),"MTS_DP_AOM")
        self.setattr_argument("DP_AOM_DDS_attenuation",NumberValue(5.0),"MTS_DP_AOM")
        
        # MTS AOM
        self.setattr_argument("Pump_AOM_frequency",NumberValue(80*1e6,scale=1e6,unit='MHz'),"MTS_Pump_AOM") # ramp duration
        self.setattr_argument("Pump_AOM_DDS_amplitude_scale",NumberValue(0.8),"MTS_Pump_AOM")
        self.setattr_argument("Pump_AOM_Urukul_attenuation",NumberValue(4),"MTS_Pump_AOM")
        
        
        # 679switch AOM
        self.setattr_argument("switch679_AOM_frequency",NumberValue(200*1e6,scale=1e6,unit='MHz'),"switch679_AOM") # ramp duration
        self.setattr_argument("switch679_AOM_DDS_amplitude_scale",NumberValue(0.8),"switch679_AOM")
        self.setattr_argument("switch679_AOM_Urukul_attenuation",NumberValue(4),"switch679_AOM")

        self.urukul_hmc_ref_Offset_AOM = self.get_device("urukul0_ch0")
        self.urukul_hmc_ref_DP_AOM = self.get_device("urukul0_ch1")
        self.urukul_hmc_ref_Pump_AOM = self.get_device("urukul0_ch2")
        self.urukul_hmc_ref_switch679_AOM = self.get_device("urukul0_ch3")
        
        self.urukul_meas = [self.get_device("urukul0_ch0"),self.get_device("urukul0_ch2"),self.get_device("urukul0_ch1"),self.get_device("urukul0_ch3")]

        
    def set_atten(self):
        
        self.Offset_AOM_dds_scale=self.Offset_AOM_DDS_amplitude_scale
        self.DP_AOM_dds_scale=self.DP_AOM_DDS_amplitude_scale
        self.Pump_AOM_dds_scale=self.Pump_AOM_DDS_amplitude_scale
        self.switch679_AOM_dds_scale=self.switch679_AOM_DDS_amplitude_scale
        
        self.Offset_AOM_iatten=self.Offset_AOM_DDS_attenuation
        self.DP_AOM_iatten=self.DP_AOM_DDS_attenuation
        self.Pump_AOM_iatten=self.Pump_AOM_Urukul_attenuation
        self.switch679_AOM_iatten=self.switch679_AOM_Urukul_attenuation
      
    @kernel    
    def init_aoms(self):
        
        delay(1*ms)
        self.urukul0_cpld.init()
        
        self.urukul_hmc_ref_Offset_AOM.init()
        self.urukul_hmc_ref_Offset_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_Offset_AOM.amplitude_to_asf(self.Offset_AOM_dds_scale))
        self.urukul_hmc_ref_Offset_AOM.set_att(self.Offset_AOM_iatten)
        self.urukul_hmc_ref_Offset_AOM.sw.on()
            
        self.urukul_hmc_ref_DP_AOM.init()
        self.urukul_hmc_ref_DP_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_DP_AOM.amplitude_to_asf(self.DP_AOM_dds_scale))
        self.urukul_hmc_ref_DP_AOM.set_att(self.DP_AOM_iatten)
        self.urukul_hmc_ref_DP_AOM.sw.on()
            
        self.urukul_hmc_ref_Pump_AOM.init()
        self.urukul_hmc_ref_Pump_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_Pump_AOM.amplitude_to_asf(self.Pump_AOM_dds_scale))
        self.urukul_hmc_ref_Pump_AOM.set_att(self.Pump_AOM_iatten)
        self.urukul_hmc_ref_Pump_AOM.sw.on()
        
        self.urukul_hmc_ref_switch679_AOM.init()
        self.urukul_hmc_ref_switch679_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_switch679_AOM.amplitude_to_asf(self.switch679_AOM_dds_scale))
        self.urukul_hmc_ref_switch679_AOM.set_att(self.switch679_AOM_iatten)
        self.urukul_hmc_ref_switch679_AOM.sw.on()
        
        
        self.set_offset_aom_frequency()
        self.set_pump_aom_frequency()
        self.set_lock_DP_aom_frequency()
        self.set_switch679_aom_frequency()
        
       
    @kernel 
    def set_pump_aom_frequency(self): 
        
        fPump = self.Pump_AOM_frequency
        urukul_ch =self.urukul_meas[1]
        dds_ftw_Pump_AOM=self.urukul_meas[1].frequency_to_ftw(fPump)
        urukul_ch.set_mu(dds_ftw_Pump_AOM, asf=urukul_ch.amplitude_to_asf(self.Pump_AOM_DDS_amplitude_scale))
        
    @kernel 
    def set_offset_aom_frequency(self): 
        
        fOffset = self.Offset_AOM_frequency
        urukul_ch =self.urukul_meas[0]
        dds_ftw_Offset_AOM=self.urukul_meas[0].frequency_to_ftw(fOffset)
        urukul_ch.set_mu(dds_ftw_Offset_AOM, asf=urukul_ch.amplitude_to_asf(self.Offset_AOM_DDS_amplitude_scale))  
        
    @kernel 
    def set_lock_DP_aom_frequency(self): 
      
        fDP = self.DP_AOM_frequency
        urukul_ch =self.urukul_meas[2]
        dds_ftw_DP_AOM=self.urukul_meas[2].frequency_to_ftw(fDP)
        urukul_ch.set_mu(dds_ftw_DP_AOM, asf=urukul_ch.amplitude_to_asf(self.DP_AOM_DDS_amplitude_scale))    
        
    @kernel 
    def set_switch679_aom_frequency(self): 
        
        fswitch679 = self.switch679_AOM_frequency
        urukul_ch =self.urukul_meas[3]
        dds_ftw_switch679_AOM=self.urukul_meas[3].frequency_to_ftw(fswitch679)
        urukul_ch.set_mu(dds_ftw_switch679_AOM, asf=urukul_ch.amplitude_to_asf(self.switch679_AOM_DDS_amplitude_scale))
        
        
    
        
    