"""
    ----- MUSE Script -----

This script creates or update a database, using Pony as ORM (Object Relational Mapper), 
storing the data of MUSE WFM and NFM files (reduced and raw) and data from the output files 
of PampelMuse (prm and psf .fits). The script also group the exposures by target.

Place: ESO - Paranal Observatory
Author: Axel Iván Reyes Orellana
Contact: axel.reyes@sansano.usm.cl
Year: 2020
Telescope: UT4
Instrument: MUSE
Documentation url: https://github.com/AxlKings/AOMUSE

"""

from astropy.io import fits
import numpy as np
import os
import glob
import json
from pony.orm import *

# Create a database object from Pony
db = Database()

# The classes have to inherit db.Entity from Pony
class Target(db.Entity):

#   ----- Attributes -----

    targetName = Required(str, unique = True) # Required: Cannot be None
    
#   ----- Relations -----

    exposures = Set('Exposure') # One target contains a set of exposures


class Exposure(db.Entity):

#   ----- Attributes -----

    insMode = Required(str)
    analysisFile = Required(str, unique=True) # Unique: Other exposure cannot have the same analysis file name
    rawFile = Optional(str, unique=True) # Optional: Can be None
    data = Optional(Json)
    psfParams = Optional(Json)
    sources = Optional(Json)
    
#   ----- Relations -----
    
    target = Required('Target') # One exposure belongs to a target


@db_session # Decorator from Pony to make that the function will be into a db session, thus the database can be modified
def museScript():
    """
    This function read 4 files (prm, psf, reduced and raw) to store the information of each exposure in a database.

    For the prm file reads the PSFPARS extension and stores it in the 'psfParams' field of the exposure.
    For the psf file reads the 'PM_X' extensions, where X is the id of the source, and stores it in the 
    'sources' field of the exposure.
    For the reduced file reads the PRIMARY header.
    And for the raw file, reads the 24 CHAN extensions, SGS_DATA, AG_DATA, ASM_DATA, SPARTA_ATM_DATA 
    and SPARTA_CN2_DATA. The information of this last 2 files is stored in the 'data' field of the exposure.

    Also, from the primary header it stores the target and instrument mode of the exposure in their own fields
    to make it easier the analysis from differents targets and instrument modes.
    """
    rootDir = input("Enter the root directory: ") # rootDir: directory where are the 3 folders (single, raw and analysis)
    singleDir = rootDir + '/single/' # Reduced files
    rawDir = rootDir + '/raw/' # Raw files
    analysisDir = rootDir + '/analysis/' # Prm and psf files

    # ----- Analysis Folder -----

    os.chdir(analysisDir) # The script starts with the analysis files (psf and prm files)    
    for analysisFileName in glob.glob('*.prm*.fits'):   
        if(Exposure.exists(analysisFile = analysisFileName)): # If the exposure already exists, then skip it
            continue
        data = {} # Dictionary to store the extensions of the reduced and raw files    
        psfParams = {} # Dictionary to store the extensions of the prm files
        sources = {} # Dictionary to store the extensions (each source) of the psf files

        # PRM File
        try:
            with fits.open(analysisFileName) as hduList:
                analysisSplit = analysisFileName.split('.prm') # split to get the single file name
                singleFileName = analysisSplit[0] + analysisSplit[1]
                psfFile = analysisFileName.replace('prm', 'psf') # replace to get the psf file name
                try:
                    params = hduList['PSFPARS'].data # If the prm file does not have the PSFPARS extension, skip 
                except KeyError:
                    continue
                try:
                    for i in range(len(params['name'])): # The column 'name' is a list with the parameter names
                        parameter = params['name'][i] 
                        value = params['polyfit'][i].tolist() # The column 'polyfit' is a list of lists
                        psfParams[parameter] = value # Store the polyfit of the PSF parameters
                    prmStep = hduList['SPECTRA'].header['CDELT3']
                    prmRestw = hduList['SPECTRA'].header['CRVAL3']               
                    prmData = np.arange(hduList['SPECTRA'].header['NAXIS3'])    # Calculate the wavelength
                    prmWavelength = (prmRestw + (prmData * prmStep))*10**9
                    psfParams['wavelength'] = prmWavelength.tolist()    
                except:
                    print("Error: cannot read the PSF parameters")
        except FileNotFoundError:
            print(f"The file {analysisFileName} does not exist\n") # If the prm file does not exists, skip
            continue 

        # PSF File
        try:
            with fits.open(psfFile) as hduList:
                for tupla in hduList.info(False): # Iterate in the list of the extensions
                    if('PM_' in tupla[1]): # Looking for the 'PM_X' extensions, where X is the id of the source
                        sourceID = tupla[1]
                        sourceData = {} # Dictionary that will store the data of the source
                        table = hduList[sourceID].data # Access to the source extension
                        i = 0
                        for column in table.columns: # Iterate in the list of columns  
                            sourceData[column] = table[column].tolist() # Store the column with its list of values
                            i += 1
                        sources[sourceID] = sourceData # Store the source data
        except FileNotFoundError:
            print(f"The file {psfFile} does not exist\n") # If the psf file does not exists, skip
            continue

    # ----- Single Folder -----

        # Reduced File
        try:
            os.chdir(singleDir) # Move to the single folder
            with fits.open(singleFileName) as hduList:
                header = hduList[0].header
                try:
                    targName = header['HIERARCH ESO OBS TARG NAME'] # Obtain the target name
                except KeyError:
                    print("The header HIERARCH ESO OBS TARG NAME does not exist")  
                if(Target.exists(targetName=targName)): # If the target already exists in the database, get it from the db
                    target = Target.get(targetName = targName)
                else:
                    target = Target(targetName = targName) # Else, create the target
                try:
                    rawFileName = header['PROV1']+'.fz' # Get the raw file name
                except KeyError:
                    print("The header PROV1 does not exist")  
                try:
                    insMode = header['HIERARCH ESO INS MODE'] # Get the instrument mode
                except KeyError:
                    print("The header HIERARCH ESO INS MODE does not exist")
                primary = dict(header) # Transform the primary header from the reduced file into a dictionary
                try:
                   del primary['COMMENT'] # and then delete the COMMENT key, because it does not have the JSON format and
                except KeyError:          # throws an error when saving it in the database
                   pass
                data['PRIMARY'] = primary # Store the primary header in the data dictionary
        except FileNotFoundError:
                print("The file {singleFileName} does not exist\n") # If the reduced file does not exists, skip
                continue  

    # ----- Raw Folder -----

        # Raw File
        try:
            os.chdir(rawDir) # Move to the raw folder
            flag = False # Flag not relevant, just to print the \n before a missed extension
            with fits.open(rawFileName) as hduList: 
                try:
                    for tupla in hduList.info(False): # Iterate in the list of the extensions
                        if('CHAN' in tupla[1]): # Looking for the CHAN extensions
                            data[tupla[1]] = dict(hduList[tupla[1]].header)
                except:
                    print("Error: channel header not found")              
                try:
                    sgsData = {} # Dictionary that will store the data
                    table = hduList['SGS_DATA'].data 
                    for column in table.columns: # Iterate in the list of columns
                        sgsData[column] = table[column].tolist() # Store the column with its list of values
                    data['SGS_DATA'] = sgsData
                except KeyError:
                    data['SGS_DATA'] = None # If the extension does not exists, stores it anyway as None
                    flag = True # Flag, not important, for the \n print
                    print("SGS_DATA not found in", singleFileName)
                try:
                    agData = {}
                    table = hduList['AG_DATA'].data
                    for column in table.columns: # Iterate in the list of columns
                        agData[column] = table[column].tolist() # Store the column with its list of values
                    data['AG_DATA'] = agData    
                except KeyError:
                    data['AG_DATA'] = None # If the extension does not exists, stores it anyway as None
                    flag = True # Flag, not important, for the \n print
                    print("AG_DATA not found in", singleFileName)
                try:
                    asmData = {}
                    table = hduList['ASM_DATA'].data
                    for column in table.columns: # Iterate in the list of columns
                        asmData[column] = table[column].tolist() # Store the column with its list of values
                    data['ASM_DATA'] = asmData      
                except KeyError:
                    data['ASM_DATA'] = None # If the extension does not exists, stores it anyway as None
                    flag = True # Flag, not important, for the \n print
                    print("ASM_DATA not found in", singleFileName)             
                try:
                    spartaAtmData = {}
                    table = hduList['SPARTA_ATM_DATA'].data
                    for column in table.columns: # Iterate in the list of columns
                        spartaAtmData[column] = table[column].tolist() # Store the column with its list of values
                    data['SPARTA_ATM_DATA'] = spartaAtmData
                except KeyError:
                    data['SPARTA_ATM_DATA'] = None # If the extension does not exists, stores it anyway as None
                    flag = True # Flag, not important, for the \n print
                    print("SPARTA_ATM_DATA not found in", singleFileName)
                try:
                    spartaCn2Data = {}
                    table = hduList['SPARTA_CN2_DATA'].data
                    for column in table.columns: # Iterate in the list of columns
                        spartaCn2Data[column] = table[column].tolist() # Store the column with its list of values
                    data['SPARTA_CN2_DATA'] = spartaCn2Data
                except KeyError:
                    data['SPARTA_CN2_DATA'] = None # If the extension does not exists, stores it anyway as None
                    flag = True # Flag, not important, for the \n print
                    print("SPARTA_CN2_DATA not found in", singleFileName)        
                if(flag):
                    print("") # The \n print
        except FileNotFoundError:
            print("The file {rawFileName} does not exist\n") # If the raw file does not exists, skip
            continue 

        # ----- Storing -----
        
        data = json.dumps(data) # Transform the data dictionary into a JSON
        psfParams = json.dumps(psfParams) # Transform the PSF parameters dictionary into a JSON
        sources = json.dumps(sources) # Transform the sources dictionary into a JSON
        Exposure(
            target = target, insMode = insMode, 
            analysisFile = analysisFileName, rawFile = rawFileName,
            data = data, psfParams = psfParams, sources = sources) # Create the exposure object (Pony automatically will store it into the database)
        os.chdir(analysisDir) # Move to the analysis folder for the next iteration

# ----- Main -----

db.bind(provider='mysql', host='127.0.0.1', user='user', passwd='pass', db='dbname') # Establish the conection with the database
db.generate_mapping(create_tables=True) # Map the classes with the database tables and create the tables if they dont exist

museScript()