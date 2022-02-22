# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 15:48:49 2022

@author: sr

Functions:
    
Set Zeeman slower aom amplitutde (scannable) and frequency
Set 2D mot aom
Set 3D mot aom


"""

from artiq.experiment import *
import numpy as np     

class Beamline461(EnvExperiment):
      
    
    def build(self):
        
        self.setattr_device("urukul1_cpld")
        
        
        # 3D MOT AOM  
        self.setattr_argument("MOT3DDP_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(85*1e6, 115*1e6, 1, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT3DDP")
        self.setattr_argument("MOT3DDP_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT3DDP")
        self.setattr_argument("MOT3DDP_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"MOT3DDP")
        
        # Zeeman slower AOM
        self.setattr_argument("Zeeman_AOM_frequency",
            Scannable(default=[NoScan(330*1e6), RangeScan(250*1e6, 350*1e6, 1, randomize=False)],scale=1e6,
                      unit="MHz"),"Zeeman")
        self.setattr_argument("Zeeman_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.95),"Zeeman")
        self.setattr_argument("Zeeman_Urukul_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Zeeman")
        
        self.setattr_argument("On_time",NumberValue(10.0,min=2.0,max=1000.0),"Zeeman")
        self.setattr_device("ttl6")
        
        # 2D MOT AOM
        self.setattr_argument("MOT2D_AOM_frequency",
            Scannable(default=[NoScan(200*1e6), RangeScan(200*1e6, 200*1e6, 1, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT2D")
        self.setattr_argument("MOT2D_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT2D")
        self.setattr_argument("MOT2D_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"MOT2D")
        
        # Probe DP AOM
        self.setattr_argument("ProbeDP_AOM_frequency",
            Scannable(default=[NoScan(120*1e6), RangeScan(100*1e6, 140*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"ProbeDP")

        self.setattr_argument("ProbeDP_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"ProbeDP")
        self.setattr_argument("ProbeDP_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"ProbeDP")
        
      
        
        self.urukul_hmc_ref_MOT2D = self.get_device("urukul1_ch0")
        self.urukul_hmc_ref_MOT3DDP = self.get_device("urukul1_ch1")
        self.urukul_hmc_ref_Zeeman = self.get_device("urukul1_ch2")
        self.urukul_hmc_ref_probeDP = self.get_device("urukul1_ch3")
        
        self.urukul_meas = [self.get_device("urukul1_ch0"),self.get_device("urukul1_ch1"),self.get_device("urukul1_ch2"),self.get_device("urukul1_ch3")]
        
        
    def set_atten(self):
        self.Zeeman_dds_scale=self.Zeeman_DDS_amplitude_scale
        self.MOT2D_dds_scale=self.MOT2D_DDS_amplitude_scale
        self.MOT3DDP_dds_scale=self.MOT3DDP_DDS_amplitude_scale
        self.probeDP_dds_scale=self.ProbeDP_DDS_amplitude_scale
           
        self.Zeeman_iatten=self.Zeeman_Urukul_attenuation
        self.MOT2D_iatten=self.MOT2D_Urukul_attenuation
        self.MOT3DDP_iatten=self.MOT3DDP_Urukul_attenuation
        self.probeDP_iatten=self.ProbeDP_Urukul_attenuation
        
    def init_aoms(self):
        
        delay(1*ms)
        self.urukul1_cpld.init()

            

        self.urukul_hmc_ref_MOT3DDP.init()
        self.urukul_hmc_ref_MOT3DDP.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT3DDP.amplitude_to_asf(self.MOT3DDP_dds_scale))
        self.urukul_hmc_ref_MOT3DDP.set_att(self.MOT3DDP_iatten)
        self.urukul_hmc_ref_MOT3DDP.sw.on()
            
            
        self.urukul_hmc_ref_Zeeman.init()
        self.urukul_hmc_ref_Zeeman.set_mu(0x40000000, asf=self.urukul_hmc_ref_Zeeman.amplitude_to_asf(self.Zeeman_dds_scale))
        self.urukul_hmc_ref_Zeeman.set_att(self.Zeeman_iatten)
        self.urukul_hmc_ref_Zeeman.sw.on()

            
        self.urukul_hmc_ref_MOT2D.init()
        self.urukul_hmc_ref_MOT2D.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT2D.amplitude_to_asf(self.MOT2D_dds_scale))
        self.urukul_hmc_ref_MOT2D.set_att(self.MOT2D_iatten)
        self.urukul_hmc_ref_MOT2D.sw.on()
            
            
        self.urukul_hmc_ref_probeDP.init()
        self.urukul_hmc_ref_probeDP.set_mu(0x40000000, asf=self.urukul_hmc_ref_probeDP.amplitude_to_asf(self.probeDP_dds_scale))
        self.urukul_hmc_ref_probeDP.set_att(self.probeDP_iatten)
        self.urukul_hmc_ref_probeDP.sw.on()
        
        
        fZeeman = self.Zeeman_AOM_frequency.sequence[0]
        dds_ftw_Zeeman=self.urukul_meas[2].frequency_to_ftw(fZeeman)
                
        urukul_ch =self.urukul_meas[2]

        urukul_ch.init()
        urukul_ch.set_mu(dds_ftw_Zeeman, asf=urukul_ch.amplitude_to_asf(self.Zeeman_dds_scale))
        urukul_ch.set_att(self.Zeeman_iatten)
        urukul_ch.sw.on()
                            
                
        fMOT2D = self.MOT2D_AOM_frequency.sequence[0]
        dds_ftw_MOT2D=self.urukul_meas[0].frequency_to_ftw(fMOT2D)
                
        urukul_ch =self.urukul_meas[0]

        urukul_ch.init()
        urukul_ch.set_mu(dds_ftw_MOT2D, asf=urukul_ch.amplitude_to_asf(self.MOT2D_dds_scale))
        urukul_ch.set_att(self.MOT2D_iatten)
        urukul_ch.sw.on() 
            
            
        fMOT3DDP = self.MOT3DDP_AOM_frequency.sequence[0]
        dds_ftw_MOT3DDP=self.urukul_meas[1].frequency_to_ftw(fMOT3DDP)
            
        urukul_ch =self.urukul_meas[1]

        urukul_ch.init()
        urukul_ch.set_mu(dds_ftw_MOT3DDP, asf=urukul_ch.amplitude_to_asf(self.MOT3DDP_dds_scale))
        urukul_ch.set_att(self.MOT3DDP_iatten)
        urukul_ch.sw.on()
        
    def scan_probe(nreps):
        
        delay(1*ms)
        self.urukul1_cpld.init()
        
        urukul_ch =self.urukul_meas[3]
        urukul_ch.init()
        urukul_ch.set_att(self.probeDP_iatten)
        urukul_ch.sw.on()
            
        for kk in range(nreps):
            for ii in range(len(self.ProbeDP_AOM_frequency.sequence)):
                     
                fprobeDP = self.ProbeDP_AOM_frequency.sequence[ii]
                dds_ftw_probeDP=self.urukul_meas[3].frequency_to_ftw(fprobeDP)
                delay(2*ms)
                urukul_ch.set_mu(dds_ftw_probeDP, asf=urukul_ch.amplitude_to_asf(self.probeDP_dds_scale))
        
    