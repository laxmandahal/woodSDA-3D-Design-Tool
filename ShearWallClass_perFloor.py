# -*- coding: utf-8 -*-
"""
This file is used to design shear wall for strength and compute story drift.
This file also designs diaphragms and anchorage (tie-downs)

Developed by: Laxman Dahal, UCLA

Created on: Aug 2020, 

Last Modified: Oct 2020

"""

__author__ = 'Laxman Dahal'



import numpy as np 
import pandas as pd 
import os
import re 
import sys 

from global_variables import shearwall_database
from global_variables import tiedown_database
from ShearForces import ComputeSeismicForce


class DesignShearWall():
    
    def __init__(self, caseID, BaseDirectory, direction, wallLength, counter, floorIndex, wall_line_name, 
                 userDefinedDetailingTag, reDesignTag, userDefinedDriftTag, userDefinedDCTag, iterateFlag):
        self.caseID = caseID 
        self.BaseDirectory = BaseDirectory 
        self.direction = direction 
        self.wall_line_name = wall_line_name
        self.userDefinedDetailingTag = userDefinedDetailingTag
        self.reDesignTag = reDesignTag
        self.userDefinedDriftTag = userDefinedDriftTag
        self.wallLength = wallLength
        self.userDefinedDCTag = userDefinedDCTag
        
        self.iterateFlag = iterateFlag
        self.counter = counter
        self.floorIndex = floorIndex
        
        #shear wall information
        self.tribuitaryWidth = None 
        self.tribuitaryLength = None 
        self.totalArea = None 
        self.wallsPerLine = None 
        # self.wallLength = None    
        self.Ga = None
        self.loadRatio = None
        #shear wall lineal loads
        self.loads = None 
        self.story_height = None
        self.allowableDrift = None
        self.tension_demand = None
        self.userInputFlag = None 

        ModelClass = ComputeSeismicForce(caseID, BaseDirectory,self.wallLength, self.direction,
                                         self.wall_line_name, self.reDesignTag, SeismicDesignParameterFlag = True)
        
        # self.Fx = ModelClass.SeismicDesignParameter['story_force']
        
        self.Cd = ModelClass.SeismicDesignParameter['Cd']
        self.Ie = ModelClass.SeismicDesignParameter['Ie']
        self.numFloors = ModelClass.numberOfStories
        self.baseShear = ModelClass.SeismicDesignParameter['ELF Base Shear']
        self.target_unit_shear = ModelClass.target_unit_shear[self.floorIndex]
        self.tension_demand = ModelClass.tension_demand[self.floorIndex]
        self.story_force_per_wall = ModelClass.story_force_per_wall[self.floorIndex]
        
        
        self.initial_moisture_content = None
        self.final_moisture_content = None
        self.elastic_modulus = None
        
        self.takeup_deflection = None 
        
        self.sw_dict = {}
        self.td_dict = {}
        
        self.read_sw_user_inputs()
        # self.SW_shear_demand()
        self.find_shearwall_candidate(shearwall_database)
        self.anchorage_design(tiedown_database, E = 29000)
        self.calculate_assembly_deflection()
        self.calculate_SW_deflection()
        self.calculate_story_drift()
        self.calculate_drift_limit()
        # self.increaseLength()
        self.check_Drift()
        
        self.drift_check = None
        self.counter = None
        # self.dfCheck = np.array([True, True, True])
        self.dfCheck = None
        
    def read_sw_user_inputs(self):
        """
        This method is used to read all the needed shear wall user inputs.
        The input files should be .txt files in respective directories
        
        :return: instantiates required class variables and attributes 
        """
        
        #read in the geometric properties
        os.chdir(self.BaseDirectory + '/%s_direction_wall'%self.direction + '/%s'%self.wall_line_name + '/Geometry')
        # self.wallLength = np.genfromtxt('wallLengths.txt')
        
            
        self.story_height = np.genfromtxt('storyHeights.txt')[self.floorIndex]
        self.tribuitaryWidth = np.genfromtxt('tribuitaryWidth.txt') # each column represents each SW line in X direction  
        self.tribuitaryLength = np.genfromtxt('tribuitaryLength.txt') # each column represents each SW line in Y direction 
        self.totalArea = np.genfromtxt('floorAreas.txt')  # wall stiffness of each wall segment
        self.wallsPerLine = np.genfromtxt('wallsPerLine.txt')
        self.allowableDrift = np.genfromtxt('allowableDrift.txt')
        self.loadRatio = np.genfromtxt('tribuitaryLoadRatio.txt')
        
        #read in shear wall lineal load 
        os.chdir(self.BaseDirectory + '/%s_direction_wall'%self.direction + '/%s'%self.wall_line_name + '/Loads')
        self.loads = np.genfromtxt('shearWall_load.txt')
        
        
        #reading material inputs 
        os.chdir(self.BaseDirectory + '/%s_direction_wall'%self.direction + '/%s'%self.wall_line_name + '/MaterialProperties')
        
        # self.userInputFlag = np.loadtxt('userInputFlagShearWall.txt')
        self.initial_moisture_content = np.genfromtxt('initial_moisture_content.txt').astype(float)
        self.final_moisture_content = np.genfromtxt('final_moisture_content.txt').astype(float)
        self.elastic_modulus = np.genfromtxt('wood_modulusOfElasticity.txt').astype(int)
        self.nailSpacing  = open('preferred_nail_spacing.txt').read()
        # self.nailSpacing = np.genfromtxt('preferred_nail_spacing.txt').astype(int)
        
        self.nailSize = open('preferred_nail_size.txt', 'r').read()
        self.panelThickness = open('preferred_panel_thickness.txt', 'r').read()
        self.takeup_deflection = np.genfromtxt('takeUpDeflection.txt')[self.floorIndex]
        self.chordArea = np.genfromtxt('chordArea.txt')[self.floorIndex]
        
        self.userDefinedDrift = np.loadtxt('userDefinedDriftLimit.txt')
        self.userDefinedDCRatio = np.loadtxt('userDefinedDCRatio.txt')
        self.userDefinedDCRatioFlag_TieDown = np.loadtxt('userDefinedDCRatioFlag_TieDown.txt')
        self.userDefinedDCRatio_TieDown = np.loadtxt('userDefinedDCRatio_TieDown.txt')
        
        self.Fx = np.genfromtxt('Fx_ToTestTheCode.txt')
        
    # def increaseLength(self):
        """
        This method is used to increase the lenght of the shear wall if 
        redesign tag is True
        
        returns: updated wallLenght attribute 

        """
        # if self.reDesignTag: 
        #     self.wallLength += 0.5
        # else:
        #     pass
        
        # return self.wallLength
    
            # self.wallLength = np.genfromtxt('wallLengths.txt')
            
    # def SW_shear_demand(self):
    #     """
    #     This method is used to calculate unit shear demand on shear wall in
    #     terms of klf
    #     :attribute Fx: Seismic Forces at each floor level. Unit: Kips 
    #     :attribute loadRatio: tribuitary load ratio taken by the wall 
    #     :attribute wallsPerLine: number of walls per shear wall line 
        
    #     :return: lineal shear demand on the shear wall. Unit: klf
    #     """
    #     self.story_force_per_wall = self.Fx * self.loadRatio / self.wallsPerLine
    
    #     self.target_unit_shear = np.cumsum(self.story_force_per_wall)/self.wallLength
    #     print(self.target_unit_shear)
    
    #     return self.target_unit_shear

    def find_shearwall_candidate(self, shearwall_database):
        """
        This method is used to find the most economical shear wall that satisfies the demand
        computed in method SW_shear_demand().
        :param shearwall_database: a dataframe read from shearwall_database.csv in Library folder
        :attribute target_unit_shear: unit shear deman on the shear wall. Units: klf
        :return: a pandas dataframe of shear wall design for every floor
        """
        # instantiate a dummy list for the purpose of creating a dataframe later
        d = []
        # floorindex = i 
        # length of the self.target_unit_shear gives the number of stories 
        #loop through the number of stories to design shear wall at each story individually 
            #check if user has specified D/C ratio.
            # if the D/C ratio is specified, multiply LRFD capacity with D/C ratio such that the code selects...
            #...shear wall with higher strength

        if self.userDefinedDCTag:
            df = shearwall_database[shearwall_database['LRFD(klf)']*self.userDefinedDCRatio >= self.target_unit_shear]
            #if D/C ratio is not specified, filter the database with capacity greater than the demand
        else: 
            df = shearwall_database[shearwall_database['LRFD(klf)'] >= self.target_unit_shear]
                
            #make copy of the filtered database for later use     
        df1 = shearwall_database[shearwall_database['LRFD(klf)'] >= self.target_unit_shear]
            #check if user has specified shear wall assembly detailing input 
        if self.userDefinedDetailingTag:
                # if self.userDefinedDCTag:
                #     df = shearwall_database[shearwall_database['LRFD(klf)']*self.userDefinedDCRatio >= self.target_unit_shear[i]]
                #     #if D/C ratio is not specified, filter the database with capacity greater than the demand
                # else: 
                #     df = shearwall_database[shearwall_database['LRFD(klf)'] >= self.target_unit_shear[i]]
                    
                #if all three detailing specifications (nail spacing, nail size, and panel thickness) are user input
            if (len(self.panelThickness)>= 2) & (len(self.nailSize)>= 2) & (len(self.nailSpacing) >= 1):
                #filter database that meets user input requirements
                df = df.loc[(df['panel thickness'] == '%s'%self.panelThickness) & (df['nail spacing'] == int(self.nailSpacing)) \
                            & (df['nail size'] == '%s'%self.nailSize)]
                # if only one or two (out of 3) detailing are user inputs filter the database to meet criteria
            else: 
                    # if panel thickness and nail size are user inputs
                if (len(self.panelThickness)>= 2) & (len(self.nailSize)>= 2) & (len(self.nailSpacing) < 1): 
                    df = df.loc[(df['panel thickness'] == '%s'%self.panelThickness) & (df['nail size'] == '%s'%self.nailSize)]
                        # if nail spacing and nail size are user inputs 
                if (len(self.panelThickness)< 2) & (len(self.nailSize)>= 2) & (len(self.nailSpacing) >= 1):
                    df = df.loc[(df['nail spacing'] == int(self.nailSpacing)) & (df['nail size'] == '%s'%self.nailSize)]
                        #if panel thickness and nail spacing are user inputs  
                if (len(self.panelThickness)>= 2) & (len(self.nailSize)< 2) & (len(self.nailSpacing) >= 1):
                    df = df.loc[(df['nail spacing'] == int(self.nailSpacing)) & (df['panel thickness'] == '%s'%self.panelThickness)]
                        # if only panel thickness is the user input 
                if (len(self.panelThickness)>= 2) & (len(self.nailSize)< 2) & (len(self.nailSpacing) < 1):
                    df = df.loc[df['panel thickness'] == '%s'%self.panelThickness]    
                        # if only nail size is the user input 
                if (len(self.panelThickness)< 2) & (len(self.nailSize)>= 2) & (len(self.nailSpacing) < 1):
                    df = df.loc[df['nail size'] == '%s'%self.nailSize]
                        #if only nai spacing is the user input  
                if (len(self.panelThickness)< 2) & (len(self.nailSize)< 2) & (len(self.nailSpacing) >= 1):
                    df = df.loc[df['nail spacing'] == int(self.nailSpacing)]
        else:
            pass 
            
        if (not self.userDefinedDetailingTag) & (not self.userDefinedDCTag):
            
                # self.counter = 0
            df = shearwall_database[shearwall_database['LRFD(klf)'] >= self.target_unit_shear]
            # df = shearwall_database[(shearwall_database['LRFD(klf)'] >= self.target_unit_shear) \
            #                         & (shearwall_database['LRFD(klf)'] <= self.target_unit_shear/0.6)]
                                 

            if self.iterateFlag:
                # try:
                df = shearwall_database[shearwall_database['LRFD(klf)'] >= self.target_unit_shear]
                print(self.counter)
                print(self.target_unit_shear)
                df = df.iloc[self.counter]
                df = pd.DataFrame([df])

                # except Exception as e:
                #     print(e.__doc__)
                #     if self.counter > 50:
                #         sys.exit(1)
                # # # except: 
                #     df = shearwall_database[(shearwall_database['LRFD(klf)'] >= self.target_unit_shear) \
                #                             & (shearwall_database['LRFD(klf)'] <= self.target_unit_shear/0.6)]
                    
                    
                        
                # try:
                #     # df = shearwall_database[shearwall_database['LRFD(klf)'].between(self.target_unit_shear[i], self.target_unit_shear[i]*1.05, inclusive = False)]
                #     df = shearwall_database[(shearwall_database['LRFD(klf)'] >= self.target_unit_shear[i]) \
                #                             & (shearwall_database['LRFD(klf)'] < self.target_unit_shear[i]*1.05)]
                #     df = df.sort_values(by = ['Ga(OSB)(kips/in)'], ascending = False)
                # except IndexError:
                #     df = shearwall_database[shearwall_database['LRFD(klf)'] >= self.target_unit_shear[i]]
                
            #for each loop, calculate the level,
        # level = len(self.target_unit_shear) - self.floorIndex
        level = self.numFloors - self.floorIndex
            # get the shear wall detailing at the first index
        try:
            self.sw_dict= {'Shear Wall Assembly':df['Assembly'].iloc[0], 'Ga(k/in)':df['Ga(OSB)(kips/in)'].iloc[0],
                      'level':level, 'LRFD(klf)': df['LRFD(klf)'].iloc[0], 'Drift(in)': 'NaN', 'D/C Ratio':self.target_unit_shear/df['LRFD(klf)'].iloc[0],
                      'OpenSees Tag':df['OpenSeesTag'].iloc[0]}
            #if no shear wall exists (might happen if detailing specification is desired), user the dataframe 
            #that does not filter based on detailing specificatin
        except IndexError: 
            print('No shearwall found. Please try different detailing or use default values @ level %d' %level)
            self.sw_dict= {'Shear Wall Assembly':df1['Assembly'].iloc[0], 'Ga(k/in)':df1['Ga(OSB)(kips/in)'].iloc[0],
                      'level':level, 'LRFD(klf)': df1['LRFD(klf)'].iloc[0], 'Drift(in)': 'NaN', 'D/C Ratio':self.target_unit_shear/df1['LRFD(klf)'].iloc[0],
                      'OpenSees Tag':df1['OpenSeesTag'].iloc[0]}
            
        d.append(self.sw_dict)
        #create a database
        self.sw_design = pd.DataFrame(d)
        # print(self.sw_design)
        # return self.sw_design
        return self.sw_dict

    
    def anchorage_design(self, tiedown_database, E = 29000 ): 
        """
        This method is user to design anchorage
        :param tiedown_database: database compiled based on AISC Manual Table 7-17
        :param E: Youngs Modulus of steel. Set to be 29000 as default
        :returns: dataframe of tie down design for each floor 
        """
        #calculate overturning moment due to the seismic force 
        # overturning_moment = np.cumsum(np.cumsum(self.story_force_per_wall * self.story_height))
        # #calculate counter-balancing moment due to the gravity load 
        # counter_moment = 0.72 * self.loads * self.wallLength /2 
        
        # self.tension_demand = np.cumsum(self.target_unit_shear * (self.story_height - 1))
        #instantiate a dummy list for the purpose of creating a dataframe later 
        d = []
        #loop over the number of stories as tie down is designed for each floor
        # for i in range (0, len(self.story_height)):
        #     #check if overturning moment exceeds the counter moment
        #     if overturning_moment[i] > counter_moment[i]:
                #if tie down is needed, calculate the tension demand
                # self.tension_demand = np.cumsum(self.target_unit_shear * (self.story_height - 1))
                # print(self.tension_demand[i])
                #if D/C ratio is desired for tie-down, multiply the capacity by the ratio
        if self.userDefinedDCRatioFlag_TieDown:
                    #filter the database such that only the ones that meet demand is left
            df = tiedown_database[tiedown_database['Capacity(kips)'] * self.userDefinedDCRatio_TieDown >= self.tension_demand]
        else:
                    #if no D/C ratio is specified, database is not multiplied by the anything
            df = tiedown_database[tiedown_database['Capacity(kips)'] >= self.tension_demand]
            # else: 
            # #if no tiedown is required, do nothing 
            #     df = tiedown_database[tiedown_database['Capacity(kips)'] >= 4.0] #make this a default tiedown design
                # pass
            #keep track of level for each loop
            # level = len(self.story_height) - i
            level = self.numFloors - self.floorIndex
            #calculate rod elongation due to the tension demand 
            deflection = self.tension_demand * self.story_height*12/(E * df['Ae(in^2)'].iloc[0] )
        
            self.td_dict = {'Tie-down Assembly':df['Assembly'].iloc[0], 'Rod Elongation(in)':deflection, 
                            'Capacity(kips)': df['Capacity(kips)'].iloc[0], 'level':level, 
                            'D/C Ratio': self.tension_demand / df['Capacity(kips)'].iloc[0]}
            d.append(self.td_dict)
        #create a dataframe for tiedown design 
        self.tiedown_design = pd.DataFrame(d)
        # return self.tiedown_designs
        return self.td_dict
    
    def calculate_assembly_deflection(self):
        """
        This method calculates the assembly deflection of the shear wall
        :return: total assembly delection of the shearwall, often referred to as "delta a""
        """  
        #calulate tension demand in terms of ASD
        # tension_demand = np.cumsum(self.target_unit_shear * (self.story_height -1))
        #convert ASD demand to LRFD
        LRFD_demand = self.tension_demand/0.7
        #calculate compressive force 
        compressive_force = LRFD_demand/self.chordArea 
        #calculate deflection due to sill plate crushing 
        #assumptions: 
        crushing = 1.75*(0.04 -0.02*(1-compressive_force/0.625)/0.27)
        #calculate deflection due to shrinkage of the wood due to moisture content
        # shrinkage = np.full(len(self.story_height), 0.0025 * 1.5 * \
        #                     (self.initial_moisture_content - self.final_moisture_content)) #uses 2X sill
        
        shrinkage =  0.0025*1.5*(self.initial_moisture_content - self.final_moisture_content)
    
        #get deflection due to rod elongation from previous method        
        rod_elongation = self.tiedown_design['Rod Elongation(in)'].values 
        # combine all the deflections 
        self.total_assembly_deflection = crushing + shrinkage + self.takeup_deflection + rod_elongation
    
        return self.total_assembly_deflection
    
    
    def calculate_SW_deflection(self ):
        """
        This method calculates the total shear wall deflection. 
        It considers deflection due to chord bending, shear, and rotation
        It uses 3-term deflection equation per SDPWS 2015
        
        :return: total shear wall deflection 
        """
        #get the per story shear demand (not the seismic force), for each story 
        # shear_demand = np.concatenate((np.array(self.target_unit_shear[0]).reshape(1,), \
        #                                 np.diff(self.target_unit_shear)))*1000
        shear_demand = self.story_force_per_wall * 1000 / self.wallLength
        # create a length array if self.wallLength attribute is an integer instead of an array 
        # length = np.full(shape = len(self.story_height), fill_value = self.wallLength)
        #calculate EA for simplicity
        EA = self.chordArea*self.elastic_modulus 
        #Get apparent shear stiffness from the designed shear walls for each floor 
        Ga = self.sw_design['Ga(k/in)'].values
        #calculate deflection due to chord bending
        del_bending = 8*shear_demand*np.power(self.story_height, 3) / ((EA/1000) * self.wallLength)/1000
        #calculate due to apparent shear failure ( nail slipping and shear deformation)
        del_shear = shear_demand * self.story_height/(1000 * Ga)
        #calculate deflection due to rotation
        del_rotation = self.total_assembly_deflection * self.story_height/(self.wallLength - 1)
        #create an instance of the deflecton 
        self.sw_deflection = del_bending + del_shear + del_rotation
        # print(self.sw_deflection)
        return self.sw_deflection
    
    
    def calculate_story_drift(self):
        """
        This method calculates story drift for the designed shear wall and tie down
        :return: story drift for each story. Units: inches
        """
        #calculate story drift per ASCE 07-16
        self.story_drift = self.sw_deflection * self.Cd / self.Ie
        # print(self.story_drift)
        return self.story_drift
    
    
    def calculate_drift_limit(self):
        """
        This method returns the drift limit to be considered to design the building for 
        :return: drift limit imposed by either code or the user 
        """
        #check if user has impose a drift limit 
        if self.userDefinedDriftTag:
            #if yes, return the drift limit based on user's input
            self.driftLimit = self.story_height * 12 * self.userDefinedDrift
        else: 
            #if not, return the drift limit based on code (eg: 2%)
            self.driftLimit = self.story_height * 12 * self.allowableDrift
        return self.driftLimit

    def check_Drift(self):
        # self.driftLimit = self.calculate_drift_limit()
        # self.story_drift = self.calculate_story_drift()
        
        self.drift_check = self.driftLimit >= self.story_drift
        # print(self.drift_check)
        return self.drift_check
        
        
        
    # def increaseLength(self):
    #     """
    #     This method is used to increase the lenght of the shear wall if 
    #     redesign tag is True
        
    #     returns: updated wallLenght attribute 

    #     """
    #     if self.reDesignTag: 
    #         self.wallLength += 0.5
    #     else:
    #         pass
        
    #     return self.wallLength




        
        
        
        
        
        
        
        
        
        
