# -*- coding: utf-8 -*-
"""
This file is used to check the story drift and redesign by iterating through the shear wall 
database until the design exceeds D/C ratio of 70%. If none of the higher strength shear wall 
assembly does not meet the drift limit, increase the length

Developed by: Laxman Dahal, UCLA

Created on: Aug 2020, 

Last Modified: Oct 2020

"""

__author__ = 'Laxman Dahal'



import pandas as pd
import numpy as np

from ShearWallDriftCheck_perFloor import ShearWallDriftCheck

class FinalShearWallDesign():
    
    def __init__(self, caseID, BaseDirectory, direction, wallLength, counter, numFloors, wall_line_name, 
                 reDesignTag, userDefinedDetailingTag, userDefinedDriftTag, userDefinedDCTag, iterateFlag ):
        
        self.caseID = caseID
        self.BaseDirectory = BaseDirectory 
        self.direction = direction 
        self.wall_line_name = wall_line_name
        self.userDefinedDetailingTag = userDefinedDetailingTag
        self.reDesignTag = reDesignTag
        self.userDefinedDCTag = userDefinedDCTag
        
        self.numFloors = numFloors
        
        self.iterateFlag = iterateFlag
        self.counter = counter
        
        self.userDefinedDriftTag = userDefinedDriftTag 
        self.wallLength = wallLength
        self.wallLengthHistory = []
        self.driftHistory = []
        
        #instantiate all the class methods so that the attributes can be used as class variables 
        self.DesignIteration()
        self.FinalDesign()

        # self.getOpenSeesTag()
        
        
    def DesignIteration(self):
        
        temp1 = []
        temp2 = []
        d = []
        for i in range(0, self.numFloors):
            sw = ShearWallDriftCheck(self.caseID, self.BaseDirectory, self.direction, self.wallLength,
                                     self.counter, i, self.wall_line_name, self.userDefinedDetailingTag,               
                                     self.reDesignTag, self.userDefinedDriftTag, self.userDefinedDCTag, 
                                     self.iterateFlag)

            temp1.append(sw.wallName.sw_dict)
            temp2.append(sw.wallName.td_dict)
            d.append(sw.getFinalWallLength())
            
        self.finalWallLength = np.array(d)
        
        self.sw_design = pd.DataFrame(temp1)
        
        self.tiedown_design = pd.DataFrame(temp2)
        
        # self.driftRecord = pd.DataFrame(drift)
        # return self.sw_final_design
        return self.finalWallLength
        
    def FinalDesign(self):
        
        temp1 = []
        temp2 = []
        self.lenss = np.array([max(self.finalWallLength)])
        # self.lenss = np.array([25, 29, 25])
        for i in range(0, self.numFloors):
            sw = ShearWallDriftCheck(self.caseID, self.BaseDirectory, self.direction, max(self.lenss),
                                      self.counter, i, self.wall_line_name, self.userDefinedDetailingTag,               
                                      self.reDesignTag, self.userDefinedDriftTag, self.userDefinedDCTag, 
                                      self.iterateFlag)
            temp1.append(sw.wallName.sw_dict)
            temp2.append(sw.wallName.td_dict)
        self.sw_final_design = pd.DataFrame(temp1)
        
        self.tiedown_final_design = pd.DataFrame(temp2)
        
        return self.sw_final_design, self.tiedown_final_design
        
        
        
    # # #define a getter method that returns the openseestag for wall modelling in opensees
    # def getOpenSeesTag(self):
        
    #     tag = self.sw_final_design['OpenSees Tag'].values  #extracts tag as an row array 
    #     tag = tag[::-1]  #changes first row from roof to first story
    #     tag = tag.reshape((-1,1))  #converts row array to column array
    #     tag = np.repeat(tag, 2, axis = 0)  #repeat array for x, and y coordinates per Zhengxiang's code input
    #     # tag = np.tile(tag, (1,2)) #double the rows 
    #     self.tagPerWall = np.tile(tag, (1, int(self.wallName.wallsPerLine)))
    #     return self.tagPerWall
    #     # return self.tag
        
        
        
        
        
        