# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 11:17:54 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 12:17:03 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
#from __future__ import print_function
#from mogdevice import MOGDevice
import time


 

class MogXRF(EnvExperiment):
    def build(self):

        self.setattr_device("ttl5")         # Camera hardware trigger
        self.setattr_device("mogdevice")
        #self.dev=self.get_device("mogdevice")  # Thorlabs camera
        
        self.setattr_argument("Tbroad",NumberValue(2.0,min=0.0,max=2.0, unit="s"),"mog")
   
        self.attenBroad = 20
        self.f1=80
        self.f2=83
        self.ftop=84
        self.fsingle=84
        self.fsaw=25*10**3
        self.Tbroad1 = 2#50*10**(-3)
        self.Tbroad2 = 2#50*10**(-3)

        self.attenSingle = -15
        self.Tsingle = 2#50*10**(-3)

        self.dt=20
        self.ntab = round(1/(self.fsaw*self.dt*10**(-9)))
        self.nloop1 = round(self.fsaw*self.Tbroad1)
        self.nloop2 = round(self.fsaw*self.Tbroad2)
        
        
    @kernel    
    def run(self):
        
        self.core.reset()
        
        mogdevice.cmd('MODE,1,TPA')         # set CH1 into table mode
        mogdevice.cmd('FREQ,1,%.2f MHz'%self.fsingle)
        dev.cmd('POW,1,%d dbm'%self.attenBroad)
        dev.cmd('TABLE,CLEAR,1') 
        dev.cmd('TABLE,XPARAM,1,FREQ,10')

        #create table entry specifying a known start condition
        dev.cmd('TABLE,APPEND,1,%.2f MHz,%.2f dbm, 0 deg, 80 ns'%(self.f1,self.attenBroad))
        # trigger the update to take effect
        dev.cmd('TABLE,APPEND,1,FREQ,%.2f MHz,0x1,UPD'%self.f1)


        # define a ramp from off f0 to f1
        dev.cmd('TABLE,RAMP,1,FREQ,%.2f MHz,%.2f MHz,%d ns,%d'%(self.f1,self.ftop,self.dt,self.ntab)) 
        # loop back to the beginning nloop times
        dev.cmd('TABLE,LOOP,1,4,2,%d'%self.nloop1) 


        #dev.cmd('TABLE,LOOP,1,-1,1,%d'%nloop)

        # define a ramp from off f0 to f1
        dev.cmd('TABLE,RAMP,1,FREQ,%.2f MHz,%.2f MHz,%d ns,%d'%(self.f2,self.ftop,self.dt,self.ntab)) 
        # loop back to the beginning nloop times
        dev.cmd('TABLE,LOOP,1,7,5,%d'%self.nloop2)


        #start loading next serial instruction
        #single frequency mode
        dev.cmd('TABLE,APPEND,1,%.2f MHz,%.2f dbm, 0 deg, 1us'%(self.fsingle,self.attenSingle))
        # trigger the update to take effect
        dev.cmd('TABLE,APPEND,1,FREQ,%.2f MHz,%.2f s,UPD'%(self.fsingleself.Tsingle))


        #create table entry specifying a known final condition, turn 

        dev.cmd('TABLE,APPEND,1,%.2f MHz,0 mW, 0 deg, 1 us'%self.fsingle)
        # trigger the update to take effect
        dev.cmd('TABLE,APPEND,1,FREQ,%.2f MHz,80 ns,UPD,OFF'%self.fsingle)



        dev.cmd('TABLE,REARM,1,ON') # ready for execution
        
