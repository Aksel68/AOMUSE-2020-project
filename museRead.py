from astropy.io import fits
import numpy as np
import pandas as pd
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
def getInput(expo):
    flag = True 
    inputs = {}
    while(flag):
        try:
            extensionName = input("Enter the extension or type 'stop': ").upper()
            if(extensionName == 'STOP'):
                break
            data = json.loads(expo.data)
            extension = data[extensionName]
        except KeyError:
            print("Extension ", extensionName, " not found")
            continue
        flag2 = True
        keys = []
        while(flag2):    
            try:
                key = input("Enter the keyword or type 'stop': ").upper()
                if(key == 'STOP'):
                    flag2 = False
                else:
                    verify = extension[key]
                    keys.append(key)
            except KeyError:
                print("Key ", key," not found")
                continue     
        inputs[extensionName] = keys  
    return inputs


@db_session
def getValues(expo, inputs, output):    
    #print(inputs)
    for extensionName, keys in inputs.items():     
        data = json.loads(expo.data)
        extension = data[extensionName]
        #print(keys)
        for key in keys:
            value = extension[key]
            if(type(value) is list):
                value = np.array(value)
                avg = np.mean(value)
                try:
                    output[key].append(avg)
                except:
                    output[key] = [avg]
            else:
                try:
                    output[key].append(value)
                except:
                    output[key] = [value]
    params = json.loads(expo.psfParams)
    stars = json.loads(expo.stars)
    #print(output)
    for key, value in params.items():
        value = np.array(value)
        avg = np.mean(value)
        try:
            output[key].append(avg)
        except:
            output[key] = [avg]
    """ 
    for i in stars.items():
        print(i)
        for key, value in i[1].items():
            value = np.array(value)
            avg = np.mean(value)
            try:
                output[key].append(avg)
            except:
                output[key] = [avg]
        break
    """
    return output



@db_session
def readDB():    
    flag = True
    while(flag):
        opt = input("Press the number of the option:\n1.- Exposures of one target\n2.- All exposures\n3.- Exit\n")
        if(opt == '1'):
            flag = True
            while(flag):
                targ = input("Enter the target name or type 'exit': ").upper()
                if(targ == 'EXIT'):
                    exit()
                target = Target.get(targetName = targ)
                if(target == None):
                    print("Target", targ, "not found")
                else:
                    flag = False
            cont = 0
            output = {}
            for expo in select(e for e in Exposure if e in target.exposures):  
                if(cont == 0):
                    inputs = getInput(expo)
                    getValues(expo, inputs, output)
                    cont += 1
                else:
                    getValues(expo, inputs, output)
                
            df = pd.DataFrame(output)
            print(df)

        elif(opt == '2'):
            cont = 0
            output = {}
            for expo in select(e for e in Exposure):  
                if(cont == 0):
                    inputs = getInput(expo)
                    getValues(expo, inputs, output)
                    cont += 1
                else:
                    getValues(expo, inputs, output)
            df = pd.DataFrame(output)
            print(df)
                

        elif(opt == '3'):
            flag = False

        else:
            print("Enter a valid option")

# ----- Main -----

db.bind(provider='mysql', host='127.0.0.1', user='user', passwd='pass', db='db')
db.generate_mapping(create_tables = True)

readDB()

