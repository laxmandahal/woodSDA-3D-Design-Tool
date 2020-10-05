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



from ShearWallClass_perFloor import DesignShearWall
from global_variables import shearwall_database


class ShearWallDriftCheck(): 
    
    def __init__(self, caseID, BaseDirectory, direction, wallLength, counter, floorIndex, wall_line_name, 
                 reDesignTag, userDefinedDetailingTag, userDefinedDriftTag, userDefinedDCTag, iterateFlag ):
        
        self.caseID = caseID
        self.BaseDirectory = BaseDirectory 
        self.direction = direction 
        self.wall_line_name = wall_line_name
        self.wallName = wall_line_name
        self.userDefinedDetailingTag = userDefinedDetailingTag
        self.reDesignTag = reDesignTag
        self.userDefinedDCTag = userDefinedDCTag
        
        self.floorIndex = floorIndex
        
        self.iterateFlag = iterateFlag
        self.counter = counter
        
        self.userDefinedDriftTag = userDefinedDriftTag 
        self.wallLength = wallLength
        self.wallLengthHistory = []
        self.driftHistory = []
        
        #instantiate all the class methods so that the attributes can be used as class variables 
        self.driftCheckAndRedesign()
        self.getShearWallDesign()
        self.getTieDownDesign()
        self.getFinalWallLength()
        # self.getOpenSeesTag()
        
        
    def driftCheckAndRedesign(self):
        """
        This method is used to check the story drift for each floor, and redesign  
        drift does not meet the drift limit (whether it is code or user imposed)
        
        :return: final shear wall and tiedown design that meets both strength and drift criteria
        """
        #initialize the DesignShearWall class to a variable with initial redesign flag set to False
        self.wallName = DesignShearWall(self.caseID, self.BaseDirectory, self.direction, self.wallLength, self.counter,
                                   self.floorIndex, self.wall_line_name, self.userDefinedDetailingTag, self.reDesignTag, 
                                   self.userDefinedDriftTag, self.userDefinedDCTag, self.iterateFlag)
        
        #get the drift
        self.drift = self.wallName.story_drift
        #get the drift limti
        self.driftLimit = self.wallName.driftLimit
        #story drift history to keep track as to how drift changes with each redesign step 
        self.driftHistory.append(self.drift)
        #an array of Boolean. False if drift exceeds the limit 
        self.driftCheck = self.drift <= self.driftLimit
        # print(self.wallName.target_unit_shear)
        self.dfCheck = self.wallName.dfCheck
        #check if any drift is not met over the height
        while not self.driftCheck:
        # while (not self.wallName.sw_design['LRFD(klf)'].values >= self.wallName.target_unit_shear/0.7) & (not self.driftCheck):

            #add the wall length if it doesnot meet the limit 
            #NOTE: wall length is added every floor, not just the floor the drift exceeds
            
            if (self.wallName.sw_design['LRFD(klf)'].values >= self.wallName.target_unit_shear/0.7) | \
                (self.wallName.sw_design['LRFD(klf)'].values == shearwall_database['LRFD(klf)'].iloc[-1]):
                self.reDesignTag = True
                self.wallLength += 0.5
                self.counter = 0

            else:
                self.iterateFlag = True
                self.counter += 1
            
            # if self.dfCheck.all():
            #     break
            
            #keeping track of the length increase
            self.wallLengthHistory.append(self.wallName.wallLength)
            #set redesign tag to be True
            # self.reDesignTag = True
            #initialize the DesignShearWall class again, but this time with redesign Tag set to True
            self.wallName = DesignShearWall(self.caseID, self.BaseDirectory, self.direction, self.wallLength, self.counter,
                                   self.floorIndex, self.wall_line_name, self.userDefinedDetailingTag, self.reDesignTag, 
                                   self.userDefinedDriftTag, self.userDefinedDCTag, self.iterateFlag)
            #get the new drift after the redesign
            self.drift = self.wallName.story_drift
            #get the driftlimit
            self.driftLimit = self.wallName.driftLimit
            #perform drift check in terms of boolean
            self.driftCheck = self.drift <= self.driftLimit
            #keep track of the drift history 
            self.driftHistory.append(self.drift)
            #exit the loop if all driftcheck is True
            self.dfCheck = self.wallName.dfCheck
        #store the final shear wall design 
        self.shearWallDesign = self.wallName.sw_design
        self.wallName.sw_dict['Drift(in)'] = float(self.drift)
        #store the final tie down design
        self.tieDownDesign = self.wallName.tiedown_design
        
        # return self.shearWallDesign, self.tieDownDesign
        
        
    #define a getter method that returns the final shear wall design dataframe
    def getShearWallDesign(self):
        return self.shearWallDesign 
    
    #define a getter method that returns the final tie down design dataframe
    def getTieDownDesign(self):
        return self.tieDownDesign
    #define a getter method that returns the final wall length
    def getFinalWallLength(self):
        return self.wallLength
        
    # #define a getter method that returns the openseestag for wall modelling in opensees
    # def getOpenSeesTag(self):
        
    #     tag = self.wallName.sw_design['OpenSees Tag'].values  #extracts tag as an row array 
    #     tag = tag[::-1]  #changes first row from roof to first story
    #     tag = tag.reshape((-1,1))  #converts row array to column array
    #     tag = np.repeat(tag, 2, axis = 0)  #repeat array for x, and y coordinates per Zhengxiang's code input
    #     # tag = np.tile(tag, (1,2)) #double the rows 
    #     self.tagPerWall = np.tile(tag, (1, int(self.wallName.wallsPerLine)))
    #     return self.tagPerWall
    #     # return self.tag
        
        
        
        
        
        
        
        
        