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
  Only the primary dictionary has single values, the others dictionaries has list of values because the were tables.
  ### PSF Parameters Field
    The PSF Parameters field is a dictionary has the four following PSF parameters list of values:
      - Theta
      - Ellipticity
      - FWHM
      - Beta
  For example:
  ``` 
  psfParams = json.loads(exposure.psfParams) # Transform the JSON into a dictionary
  theta = psfParams['theta'] 
  e = psfParams['e'] # Ellipticity
  FWHM = psfParams['fwhm']
  beta = psfParams['beta']
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
  snr = sources['snr'] 
  flux = sources['flux'] # Ellipticity
  FWHM = sources['fwhm']
  beta = sources['beta']
  ```
  ### Some important keywords 
## PonyORM

  ### Create
  ### Read
  ### Update
  ### Delete
If there is an error with the scripts or with the README, like a misspelling or something, do not be afraid to send me an email to axel.reyes@sansano.usm.cl and I will try to fix it as soon as posible. Thank you in advance.

