from astropy.io import fits
import numpy as np
import os
import glob
import json
from pony.orm import *

db = Database()

class Target(db.Entity):

#   ----- Attributes -----

    targetName = Required(str, unique = True)
    exposures = Set('Exposure')


class Exposure(db.Entity):

#   ----- Attributes -----

    targetName = Required('Target')
    analysisFile = Required(str, unique=True)
    singleFile = Optional(str, unique=True)
    rawFile = Optional(str, unique=True)
    data = Optional(Json)
    psfParams = Optional(Json)
    stars = Optional(Json)


@db_session
def museScript():
    rootDir = input("Enter the root directory")
    singleDir = rootDir + '/single/'
    rawDir = rootDir + '/raw/'
    analysisDir = rootDir + '/analysis/'
    os.chdir(analysisDir)          
    for analysisFileName in glob.glob('*.prm*.fits'):   
        data = {}     
        psfParams = {}
        stars = {}
        try:
            with fits.open(analysisFileName) as hduList:
                analysisSplit = analysisFileName.split('.prm')
                #print(analysisSplit)
                psfFile = analysisFileName.replace('prm', 'psf')
                singleFileName = analysisSplit[0] + analysisSplit[1]
                params = hduList['PSFPARS'].data
                try:
                    for i in range(len(params['name'])):
                        key = params['name'][i]
                        value = params['polyfit'][i].tolist()
                        psfParams[key] = value
                except:
                    print("Error: cannot read the PSF parameters")
                prm_step = hduList['SPECTRA'].header['CDELT3']
                prm_restw = hduList['SPECTRA'].header['CRVAL3']
                prm_data = np.arange(hduList['SPECTRA'].header['NAXIS3'])
                prm_wavelength = (prm_restw + (prm_data * prm_step))*10**9
                psfParams['wavelength'] = prm_wavelength.tolist()
        except FileNotFoundError:
                print("The file", analysisFileName,"does not exist")
     
        try:
            with fits.open(psfFile) as hduList:
                for tuple in hduList.info(False):
                    if('PM_' in tuple[1]):
                        starID = tuple[1]
                        starData = {}
                        table = hduList[starID].data
                        while(i < len(table.columns)):
                            name = table.columns.names[i]
                            starData[name] = table[name].tolist() 
                            i += 1
                        stars[starID] = starData

        except FileNotFoundError:
            print("The file", psfFile,"does not exist")

        try:
            os.chdir(singleDir) 
            with fits.open(singleFileName) as hduList:
                header = hduList[0].header
                try:
                    targName = header['HIERARCH ESO OBS TARG NAME']
                except KeyError:
                    print("The header HIERARCH ESO OBS TARG NAME does not exist")  
                if(Target.exists(targetName=targName)):
                    target = Target.get(targetName = targName)
                else:
                    target = Target(targetName = targName)
                if(Exposure.exists(singleFile=singleFileName)):
                    continue
                expo = Exposure(targetName = target, analysisFile = analysisFileName)
                expo.singleFile = singleFileName
                expo.psfParams = json.dumps(psfParams)
                expo.stars = json.dumps(stars)
                try:
                    rawFileName = header['PROV1']+'.fz'
                    expo.rawFile = rawFileName
                except KeyError:
                    print("The header PROV1 does not exist")     
                aux = dict(header)
                try:
                   del aux['COMMENT']
                except KeyError:
                   pass
                data['PRIMMARY'] = aux #json.dumps(aux)        
        except FileNotFoundError:
                print("The file", singleFileName,"does not exist")
      
        try:
            os.chdir(rawDir)
            flag = True
            with fits.open(rawFileName) as hduList: 
                try:
                    data['CHAN01'] = dict(hduList['CHAN01'].header)
                    data['CHAN02'] = dict(hduList['CHAN02'].header)
                    data['CHAN03'] = dict(hduList['CHAN03'].header)
                    data['CHAN04'] = dict(hduList['CHAN04'].header)
                    data['CHAN05'] = dict(hduList['CHAN05'].header)
                    data['CHAN06'] = dict(hduList['CHAN06'].header)
                    data['CHAN07'] = dict(hduList['CHAN07'].header)
                    data['CHAN08'] = dict(hduList['CHAN08'].header)
                    data['CHAN09'] = dict(hduList['CHAN09'].header)
                    data['CHAN10'] = dict(hduList['CHAN10'].header)
                    data['CHAN11'] = dict(hduList['CHAN11'].header)
                    data['CHAN12'] = dict(hduList['CHAN12'].header)
                    data['CHAN13'] = dict(hduList['CHAN13'].header)
                    data['CHAN14'] = dict(hduList['CHAN14'].header)
                    data['CHAN15'] = dict(hduList['CHAN15'].header)
                    data['CHAN16'] = dict(hduList['CHAN16'].header)
                    data['CHAN17'] = dict(hduList['CHAN17'].header)
                    data['CHAN18'] = dict(hduList['CHAN18'].header)
                    data['CHAN19'] = dict(hduList['CHAN19'].header)
                    data['CHAN20'] = dict(hduList['CHAN20'].header)
                    data['CHAN21'] = dict(hduList['CHAN21'].header)
                    data['CHAN22'] = dict(hduList['CHAN22'].header)
                    data['CHAN23'] = dict(hduList['CHAN23'].header)
                    data['CHAN24'] = dict(hduList['CHAN24'].header)
                except:
                    print("Error: channel header not found")
                
                try:
                    sgsData = {}
                    i = 0
                    table = hduList['SGS_DATA'].data
                    while(i < len(table.columns)):
                        name = table.columns.names[i]
                        sgsData[name] = table[name].tolist() 
                        i += 1
                    data['SGS_DATA'] = sgsData
                except KeyError:
                    data['SGS_DATA'] = None
                    flag = False
                    print("SGS_DATA not found in", expo.singleFile)

                try:
                    agData = {}
                    i = 0
                    table = hduList['AG_DATA'].data
                    while(i < len(table.columns)):
                        name = table.columns.names[i]
                        agData[name] = table[name].tolist() 
                        i += 1
                    data['AG_DATA'] = agData    
                except KeyError:
                    data['AG_DATA'] = None
                    flag = False
                    print("AG_DATA not found in", expo.singleFile)

                try:
                    asmData = {}
                    i = 0
                    table = hduList['ASM_DATA'].data
                    while(i < len(table.columns)):
                        name = table.columns.names[i]
                        asmData[name] = table[name].tolist() 
                        i += 1
                    data['ASM_DATA'] = asmData      
                except KeyError:
                    data['ASM_DATA'] = None
                    flag = False
                    print("ASM_DATA not found in", expo.singleFile)
                
                try:
                    spartaAtmData = {}
                    i = 0
                    table = hduList['SPARTA_ATM_DATA'].data
                    while(i < len(table.columns)):
                        name = table.columns.names[i]
                        spartaAtmData[name] = table[name].tolist()
                        i += 1 
                    data['SPARTA_ATM_DATA'] = spartaAtmData
                except KeyError:
                    data['SPARTA_ATM_DATA'] = None
                    flag = False
                    print("SPARTA_ATM_DATA not found in", expo.singleFile)

                try:
                    spartaCn2Data = {}
                    i = 0
                    table = hduList['SPARTA_CN2_DATA'].data
                    while(i < len(table.columns)):
                        name = table.columns.names[i]
                        spartaCn2Data[name] = table[name].tolist() 
                        i += 1
                    data['SPARTA_CN2_DATA'] = spartaCn2Data
                except KeyError:
                    data['SPARTA_CN2_DATA'] = None
                    flag = False
                    print("SPARTA_CN2_DATA not found in", expo.singleFile)        
                if(not flag):
                    print("")
        except FileNotFoundError:
            print("The file", rawFileName,"does not exist")
        expo.data = json.dumps(data)
        os.chdir(analysisDir)  
            
        

        

# ----- Main -----

db.bind(provider='mysql', host='127.0.0.1', user='aomuse', passwd='#aomuse2020', db='aomuse')
db.generate_mapping(create_tables=True)

museScript()
        

