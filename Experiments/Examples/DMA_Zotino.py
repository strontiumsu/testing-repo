# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 22:42:28 2022

@author: sr
"""

from artiq.experiment import *
import time

class DMA_zotino(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("zotino0") 
        self.dac=self.get_device("zotino0")
        #self.dac=self.zotino0 
        self.setattr_argument("fdepth1", NumberValue(5,min=0.0,max=7),"rMOT")
        self.setattr_argument("fdepth2", NumberValue(1,min=0.0,max=7),"rMOT")
        self.setattr_argument("fsingle", NumberValue(0.5,min=0.0,max=7.0),"rMOT")
        self.setattr_argument("fsaw", NumberValue(25*1e3,min=0.0,max=40*1e3,
                      unit="kHz"),"rMOT")
        self.setattr_argument("tbroad",NumberValue(100*1e-3,min=0.0*1e-3,max=200*1e-3,scale = 1e-3,
                      unit="ms"),"rMOT") # Pulse amplitude  
        self.setattr_argument("nstages", NumberValue(2,min=0,max=7),"rMOT")
        
    def prepare(self):
        self.nsteps = 16
        self.nsaw = round(self.fsaw*self.tbroad)
        self.tdelay = 1/(16*self.fsaw)
        
        self.vbottom1 = self.fdepth1*(0.1/1.4)
        self.vbottom2 = self.fdepth2*(0.1/1.4)
        self.vsingle = -self.fsingle*(0.1/1.4)

    @kernel
    def record(self):
        with self.core_dma.record("broad1"):
            for i in range(0,self.nsteps,1):
                delay(self.tdelay*s)
                self.dac.set_dac([-self.vbottom1+self.vbottom1*i/(self.nsteps-1)],[7])
                #if (i == self.nsteps -1):
                #    delay(self.tdelay*s)
                #    self.dac.set_dac([self.vsingle],[7])
            self.dac.set_dac_mu([0],[7])
            
        with self.core_dma.record("broad2"):
            for i in range(0,self.nsteps,1):
                delay(self.tdelay*s)
                self.dac.set_dac([-self.vbottom2+self.vbottom2*i/(self.nsteps-1)],[7])
                #if (i == self.nsteps -1):
                #    delay(self.tdelay*s)
                #    self.dac.set_dac([self.vsingle],[7])
            self.dac.set_dac_mu([0],[7])
            
        with self.core_dma.record("single"):
            delay(self.tdelay*s)
            self.dac.set_dac([self.vsingle],[7])
            #self.dac.set_dac_mu([0],[7])

    @kernel
    def run(self):
        self.core.reset()
        self.dac.init()
        #timeee = self.core.get_rtio_counter_mu()
        #nowtime = now_mu()
        self.record()
        #print(self.core.mu_to_seconds(self.core.get_rtio_counter_mu() - timeee))
        #print(self.core.mu_to_seconds(now_mu() - nowtime))
        
        
        pulses_handle1 = self.core_dma.get_handle("broad1")
        pulses_handle2 = self.core_dma.get_handle("broad2")
        pulses_handle3 = self.core_dma.get_handle("single")
        self.core.break_realtime()
        
        while True:
            for i in range(self.nsaw):
                self.core_dma.playback_handle(pulses_handle1)
            for i in range(self.nsaw):
                self.core_dma.playback_handle(pulses_handle2)
            self.core_dma.playback_handle(pulses_handle3)
            delay(.5*s)
            #self.dac.set_dac([1],[7])
            #delay(0.5*s)