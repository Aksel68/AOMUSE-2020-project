# AOMUSE
AO Muse Project
> Axel Iván Reyes Orellana

Project to improve AO Muse performance.

The script retrieve data from fits files (prm and psf .fits, reduced and raw), and store it into the database grouped by target.

## Contents
- [Requirements](https://github.com/AxlKings/AOMUSE/new/development?readme=1#requirements)
- [Before execute](https://github.com/AxlKings/AOMUSE/new/development?readme=1#before-execute)
- [How to run the scripts](https://github.com/AxlKings/AOMUSE/new/development?readme=1#scripts)
- [Exposure Data Structure](https://github.com/AxlKings/AOMUSE/new/development?readme=1#data-structure)

  - [Data field](https://github.com/AxlKings/AOMUSE/new/development?readme=1#data-field)
  - [PSF Parameters field](https://github.com/AxlKings/AOMUSE/new/development?readme=1#psf-parameters-field)
  - [Sources field](https://github.com/AxlKings/AOMUSE/new/development?readme=1#sources-field)
  - [Some keywords](https://github.com/AxlKings/AOMUSE/new/development?readme=1#some-important-keywords)
- [Basic PonyORM functions](https://github.com/AxlKings/AOMUSE/new/development?readme=1#ponyorm)

  - [Create](https://github.com/AxlKings/AOMUSE/new/development?readme=1#create)
  - [Read](https://github.com/AxlKings/AOMUSE/new/development?readme=1#read)
  - [Update](https://github.com/AxlKings/AOMUSE/new/development?readme=1#update)
  - [Delete](https://github.com/AxlKings/AOMUSE/new/development?readme=1#delete)
  
## Requirements
For the execution of the script its neccesary:
- [MariaDB](https://mariadb.org/)

It also uses the next libraries: 
- [PonyORM](https://ponyorm.org/)
- [PyMySQL](https://pymysql.readthedocs.io/en/latest/)
- [NumPy](https://numpy.org/)
- [AstroPy](https://www.astropy.org/)
- [Glob](https://docs.python.org/3/library/glob.html)
- [OS](https://docs.python.org/3/library/os.html)
- [Json](https://docs.python.org/3/library/json.html)

## Before execute
Before execute its necessary to make an empty mariaDB database. You will need the name of the DB, username and password for the connection.

To create the database you have to login first (you can do it as root):
```
mysql -u //user_name// -p 
```
Then you have to create an empty database:
```sql
CREATE DATABASE //database_name//; 
```
Create an user of the database:
```sql
CREATE USER '//username//'@'localhost' IDENTIFIED BY '//password//';
```
And finally grant privileges to the database user:
```sql
GRANT ALL PRIVILEGES ON //database_name//.* TO '//username//'@'localhost';
```
## Scripts

### museScript.py
First, you have to modify the next line at the end of the script with your database information:
```
db.bind(provider = 'mysql', host = '127.0.0.1', user = '//username//', passwd = '//password//', db = '//database_name//')
``` 

To execute museScript.py its neccesary to have three folders in the same directory with the reduced, analysis, and raw files named 'single', 'analysis' and 'raw' respectively. At the moment to execute the script, you have to give as input the root directory where are the folders, or you can press enter if the script its already in the root directory.
The script will automatically read the files, create the objects corresponding and PonyORM will map those to the MariaDB database.

### museDelete.py

First, you have to modify the next line at the end of the script with your database information:
```
db.bind(provider = 'mysql', host = '127.0.0.1', user = '//username//', passwd = '//password//', db = '//database_name//')
``` 
This script will drop all the tables of your database.  

## Data Structure
All the following fields are in JSON format, so at the moment to read them in python, you have to transform it into a dictionary to access to the information.
### Data Field
The exposure Data field has the following extensions (as dictionaries):
  - PRIMARY: Primary header of the reduced file.
  - CHAN_X: CHAN extensions of the raw file, where X goes from 01 to 24.
  - SGS_DATA: SGS data extension of the raw file.
  - AG_DATA: AG data extension of the raw file.
  - ASM_DATA: ASM data extension of the raw file.
  - SPARTA_ATM_DATA: SPARTA ATM data extension of the raw file.
  - SPARTA_CN2_DATA: SPARTA Cn2 data extension of the raw file.

For example:
```
data_json = exposure.data # Data field in JSON format (in Python JSON is represented as string)
data = json.loads(data_json) # Transform the JSON into a dictionary
``` 
``` 
primary = data['PRIMARY'] # Primary header
ra = primary['RA'] # Right Ascension
dec = primary['DEC'] # Declination
tau0 = primary['ESO TEL AMBI TAU0'] # Coherence time
```
```
asmData = data['ASM_DATA']
seeing = asmData['DIMM_SEEING'] # List of seeing values
```
Only the primary dictionary has single values, the others dictionaries has list of values because they were tables.
### PSF Parameters Field
The PSF Parameters field is a dictionary has the four following PSF parameters list of values:
- Theta
- Ellipticity
- FWHM
- Beta
- Wavelength

For example:
``` 
psfParams = json.loads(exposure.psfParams) # Transform the JSON into a dictionary
theta = psfParams['theta'] 
e = psfParams['e'] # Ellipticity
FWHM = psfParams['fwhm']
beta = psfParams['beta']
wavelength = psfParams['wavelength']
```
### Sources Field 
The exposure Sources field can have several 'PM_X' extensions, where X is the source id assigned by PampelMuse. Each source has a table with the following columns:
- SNR (Signal to noise ratio)
- Flux 
- Beta
- FWHM
- xc (x coordinate in pixels)
- yc (y coordinate in pixels)

For example:
``` 
sources = json.loads(exposure.sources) # Transform the JSON into a dictionary
source = sources['PM_1'] # Choose a source (Assuming that PM_1 exists)
snr = source['snr'] 
flux = source['flux'] # Ellipticity
beta = source['beta']
FWHM = source['fwhm']
xc = source['xc']
yc = source['yc']
```
### Some important keywords 

## PonyORM

### Create
Create a target named "targetName"
```
target = Target(targetName = "testTarget") 
```
Create an exposure that belongs to the previous target
```
exposure = Exposure(target = target, insMode = "testMode", analysisFile = "testAnalysis")
```
Optional to initialize the other attributes of the exposure
```
exposure.rawFile = "testRaw"
```
```
# Creating a dummy data field 
dictionary = {}
dictionary["PRIMARY"] = {}
dictionary["PRIMARY"]["RA"] = 221.0
dictionary["PRIMARY"]["DEC"] = 19.1         
dictionary["PRIMARY"]["ESO INS MODE"] = "testMode"
dictionary["ETC"] = "etc"
data = json.dumps(dictionary) #Transform the dictionary into a JSON string
exposure.data = data
```
```
# Creating a dummy psfParams field
dictionary = {}
dictionary["beta"] = [1,2,3]
dictionary["e"] = [1,2,3]
dictionary["theta"] = [1,2,3]
dictionary["fwhm"] = [1,2,3]
dictionary["wavelength"] =  [1,2,3]
psfParams = json.dumps(dictionary)
exposure.psfParams = psfParams
``` 
```
# Creating a dummy sources field
dictionary = {
"PM_1": {
      "snr": [1,2,3], "flux": [1,2,3], "fwhm": [1,2,3], "beta": [1,2,3], "xc": [1,2,3], "yc": [1,2,3]
  },
  "PM_2": {
      "snr": [1,2,3], "flux": [1,2,3], "fwhm": [1,2,3], "beta": [1,2,3], "xc": [1,2,3], "yc": [1,2,3]
  },
  "ETC": "etc"
}
sources = json.dumps(dictionary) 
exposure.sources = sources
```
Create an exposure that belongs to another target
```
exposure = Exposure(target = Target[1], insMode = "test", analysisFile = "test")
```
### Read
Get a target by targetName
```
target = Target.get(targetName = "testTarget")
```
Get a target by id
```
id = 1
target = Target[id]
```
Get an exposure by id
```
id = 1
expo = Exposure[id]
```
Get an exposure by file name (for example: raw file name)
```
exposure = Exposure.get(rawFile = "testRaw")
```
Get all exposures
```
expos = select(e for e in Exposure)
len(expos)
```
Get all exposures as a List
```
expos = select(e for e in Exposure)[:]
```

Get exposures of a target
```
expos = select(e for e in Exposure if e in target.exposures) # Notice that the condition can be whatever 
len(expos)
```
Get exposures of a specific instrument mode
```
expos = select(e for e in Exposure if e.insMode == "WFM-AO-N")
len(expos)
```
Get the id
```
targetID = target.id
exposureID = exposure.id
```
Get the target name of a target
```
targetName = target.targetName 
```
Get attributes from the exposure
```
target = exposure.target    # Get the target object that contains the exposure
analysisFileName = exposure.analysisFile
insMode = exposure.insMode
rawFileName = exposure.rawFile
data = json.loads(exposure.data) #Transform the JSON into a dictionary
psfParams = json.loads(exposure.psfParams)
sources = json.loads(exposure.sources)
```
### Update
Change the target name
```
target.targetName = "testTarget2"
```
Change the target
```
newTarget = Target[id_of_another_target]
expo = Exposure.get(analysisFile = "test")
expo.target = newTarget
```
Change a file name
```
exposure.rawFile = "testRaw2"
```
Change data
```
data = json.loads(exposure.data)
data["PRIMARY"]["RA"] = 200.0
exposure.data = json.dumps(data)
```
Change PSF Parameters
```
psf = json.loads(exposure.psfParams)
psf["fwhm"] = [2,3,4]
exposure.psfParams = json.dumps(psf)
```
Change sources data
```
sources = json.loads(exposure.sources)
sources["PM_1"]["snr"] = [2,3,4]
exposure.sources = json.dumps(sources)   
```
### Delete
Delete a target
```
target = Target.get(targetName = "testTarget2")
target.delete()
```
Notice that all the exposures that belongs to the target were deleted
```
expo = Exposure.get(analysisFile = "testAnalysis2")
expo # Check for the exposure
```
Delete an exposure
```
expo = Exposure.get(analysisFile = "test")
expo.delete()
```
If there is an error with the scripts or with the README, like a misspelling or something, do not be afraid to send me an email to axel.reyes@sansano.usm.cl and I will try to fix it as soon as posible. Thank you in advance.
