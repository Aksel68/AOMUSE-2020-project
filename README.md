# AOMUSE
Muse AO Project
> Axel Iván Reyes Orellana

Project to improve Muse AO performance.
The script retrieve data from fits files (prm and psf .fits, reduced and raw), and store it into the database grouped by target.

## Contents
- [Requirements](https://github.com/AxlKings/AOMUSE-2020-project#requirements)
- [Before execute](https://github.com/AxlKings/AOMUSE-2020-project#before-execute)
- [How to run the scripts](https://github.com/AxlKings/AOMUSE-2020-project#scripts)
- [Exposure Data Structure](https://github.com/AxlKings/AOMUSE-2020-project#data-structure)

  - [Data field](https://github.com/AxlKings/AOMUSE-2020-project#data-field)
  - [PSF Parameters field](https://github.com/AxlKings/AOMUSE-2020-project#psf-parameters-field)
  - [Sources field](https://github.com/AxlKings/AOMUSE-2020-project#sources-field)
  - [Some keywords](https://github.com/AxlKings/AOMUSE-2020-project#some-important-keywords)
- [Basic PonyORM functions](https://github.com/AxlKings/AOMUSE-2020-project#ponyorm)

  - [Create](https://github.com/AxlKings/AOMUSE-2020-project#create)
  - [Read](https://github.com/AxlKings/AOMUSE-2020-project#read)
  - [Update](https://github.com/AxlKings/AOMUSE-2020-project#update)
  - [Delete](https://github.com/AxlKings/AOMUSE-2020-project#delete)
- [Create a Backup](https://github.com/AxlKings/AOMUSE-2020-project#create-a-backup)
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


*For better understanding, the terms that are enclosed in curly brackets must be replaced with their corresponding values.*
## Before execute

Before execute its necessary to make an empty mariaDB database. You will need the name of the DB, username and password for the connection.

To create the database you have to login first (you can do it as root):
```
mysql -u {user_name} -p 
```
Then you have to create an empty database:
```sql
CREATE DATABASE {database_name}; 
```
Create an user of the database:
```sql
CREATE USER '{username}'@'localhost' IDENTIFIED BY '{password}';
```
And finally grant privileges to the database user:
```sql
GRANT ALL PRIVILEGES ON {database_name}.* TO '{username}'@'localhost';
```

## Scripts

### museScript.py
First, you have to modify the next line at the end of the script with your database information:
```python
db.bind(provider = 'mysql', host = '127.0.0.1', user = '
{username}', passwd = '{password}', db = '{database_name}')
``` 
To execute museScript.py its necesary to have three folders in the same directory with the reduced, analysis, and raw files named 'single', 'analysis' and 'raw' respectively. Also, the analysis files must have the same name as the reduced file (differing by extension). At the moment to execute the script, you have to give as input the root directory where are the folders, or you can press enter if the script its already in the root directory.
The script will automatically read the files, create the objects corresponding and PonyORM will map those to the MariaDB database.


### museDelete.py
First, you have to modify the next line at the end of the script with your database information:
```python
db.bind(provider = 'mysql', host = '127.0.0.1', user = '{username}', passwd = '{password}', db = '{database_name}')
``` 
This script will drop all the tables of your database.  

## Data Structure

The following code cells define the structure of the database entities (Targets and Exposures) and how Pony map the classes with the tables.
```python
from pony.orm import *
```
```python
# Create a database object from Pony
db = Database()

# The classes inherit db.Entity from Pony
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
```

```python
#   ----- Main -----

db.bind(provider='mysql', host='127.0.0.1', user='{user}', passwd='{pass}', db='{dbname}') # Establish the conection with the database
db.generate_mapping() # Map the classes with the database tables 
```
For the exposure structure, we will see the following fields that are in JSON format. At the moment to read them in python, you have to transform it into a dictionary to access to the information.
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
```python
data_json = exposure.data # Data field in JSON format (in Python JSON is represented as string)
data = json.loads(data_json) # Transform the JSON into a dictionary
``` 
``` python
primary = data['PRIMARY'] # Primary header
ra = primary['RA'] # Right Ascension
dec = primary['DEC'] # Declination
tau0 = primary['ESO TEL AMBI TAU0'] # Coherence time
```
```python
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
``` python
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
``` python
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
Each exposure data field contains a lot of information, so the keywords that you want can be hard to find. Here are some keywords that we have used for the analysis in this project (sometimes are not all availables in an exposure):

Seeing
```python
Seeing = (data['PRIMARY']['ESO TEL AMBI FWHM START']+data['PRIMARY']['ESO TEL AMBI FWHM END'])/2 # average between two values 
```
Air Mass
```python
airMass = (data['PRIMARY']['ESO TEL AIRM START']+data['PRIMARY']['ESO TEL AIRM END'])/2 # average between two values 
```
Coherence time
```python
Tau0 = (data['PRIMARY]['ESO TEL AMBI TAU0'])
```
Date
```python
date = data['PRIMARY']['DATE-OBS'] # as string
```
Ground layer fraction
```python
glf = data['PRIMARY']['ESO OCS SGS ASM GL900 AVG']
```
Guide star flux
```python
ngsFlux = data['PRIMARY']["ESO AOS NGS1 FLUX"]
```
STREHL
```python
# Get the mean strehl for each laser
sparta = data["SPARTA_ATM_DATA"]
L1 = np.mean(sparta["LGS1_STREHL"])
L2 = np.mean(sparta["LGS2_STREHL"])
L3 = np.mean(sparta["LGS3_STREHL"])
L4 = np.mean(sparta["LGS4_STREHL"])
```
## PonyORM

### Create
To create entities for the database you only have to create the object corresponding to the class that represents the table of the database.
At the moment to create the object, you have to pass the attributes required according to the class structure.
Here are some examples of how to create objects with the previously defined class structure: 
#### Create a target named "targetName"
```python
target = Target(targetName = "testTarget") 
```
#### Create an exposure that belongs to the previous target
```python
exposure = Exposure(target = target, insMode = "testMode", analysisFile = "testAnalysis")
```
#### Optional to initialize the other attributes of the exposure
```python
exposure.rawFile = "testRaw"
```
```python
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
```python
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
```python
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
#### Create an exposure that belongs to another target
```python
exposure = Exposure(target = Target[1], insMode = "test", analysisFile = "test")
```
### Read
To read the data from the database, Pony offers different ways to do that. Here are some of them:
#### Get a target by targetName
```python
target = Target.get(targetName = "testTarget")
```
#### Get a target by id
```python
id = 1
target = Target[id]
```
#### Get an exposure by id
```python
id = 1
expo = Exposure[id]
```
#### Get an exposure by file name (for example: raw file name)
```python
exposure = Exposure.get(rawFile = "testRaw")
```
#### Get all exposures
```python
expos = select(e for e in Exposure)
len(expos)
```
#### Get all exposures as a List
```python
expos = select(e for e in Exposure)[:]
```

#### Get exposures of a target
```python
expos = select(e for e in Exposure if e in target.exposures) # Notice that the condition can be whatever 
len(expos)
```
#### Get exposures of a specific instrument mode
```python
expos = select(e for e in Exposure if e.insMode == "WFM-AO-N")
len(expos)
```
#### Get the id
```python
targetID = target.id
exposureID = exposure.id
```
#### Get the target name of a target
```python
targetName = target.targetName 
```
#### Get attributes from the exposure
```python
target = exposure.target    # Get the target object that contains the exposure
analysisFileName = exposure.analysisFile
insMode = exposure.insMode
rawFileName = exposure.rawFile
data = json.loads(exposure.data) #Transform the JSON into a dictionary
psfParams = json.loads(exposure.psfParams)
sources = json.loads(exposure.sources)
```
### Update
To update an entitie, you can modify the corresponding object field. 
#### Change the target name
```python
target.targetName = "testTarget2"
```
#### Change the target
```python
newTarget = Target[id_of_another_target]
expo = Exposure.get(analysisFile = "test")
expo.target = newTarget
```
#### Change a file name
```python
exposure.rawFile = "testRaw2"
```
#### Change data
```python
data = json.loads(exposure.data)
data["PRIMARY"]["RA"] = 200.0
exposure.data = json.dumps(data)
```
#### Change PSF Parameters
```python
psf = json.loads(exposure.psfParams)
psf["fwhm"] = [2,3,4]
exposure.psfParams = json.dumps(psf)
```
#### Change sources data
```python
sources = json.loads(exposure.sources)
sources["PM_1"]["snr"] = [2,3,4]
exposure.sources = json.dumps(sources)   
```
### Delete
#### Delete a target
```python
target = Target.get(targetName = "testTarget2")
target.delete()
```
Notice that all the exposures that belongs to the target were deleted
```python
expo = Exposure.get(analysisFile = "testAnalysis2")
expo # Check for the exposure
```
#### Delete an exposure
```python
expo = Exposure.get(analysisFile = "test")
expo.delete()
```

For more information, please read [Pony documentation](https://docs.ponyorm.org/).

## Create a backup
### Step 1.- Create an empty database:
First, log in to MySQL database server:
```
mysql -u root -p
```
Then, use CREATE DATABASE statement as follows:
```sql
> CREATE DATABASE {db_backup_name};
```
Finally, use SHOW DATABASES command to verify:
```sql
> SHOW DATABASES
```

### Step 2.- Dump database objects and data into SQL file using the mysqldump tool.
To dump the database objects and data of the original database into an SQL file located at D:\db folder, you have to use this command:
``` 
>mysqldump -u root -p {original_db_name} > d:\db\{original_db_name}.sql
```
This command instructs mysqldump to log in to the MySQL server using the root user account with a password and exports the database objects and data of the original database to d:\db\\{original_db_name}.sql. 

### Step 3.- Import the d:\db\classicmodels.sql file into classicmodels_backup database.
```
>mysql -u root -p {db_backup_name} < d:\db\{original_db_Name}.sql
```

To verify the import:
```sql
> SHOW TABLES FROM {db_backup_name};
```


If there is an error with the scripts or with the README, like a misspelling or something, do not be afraid to send me an email to axel.reyes@sansano.usm.cl and I will try to fix it as soon as posible. Thank you in advance.

