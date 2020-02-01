# AOMUSE
AO Muse Project
> Axel Iván Reyes Orellana

Project to improve AO Muse performance.

### Requirements
For the execute of the scripts its neccesary:
- [MariaDB](https://mariadb.org/)
- [Connector/ODBC](https://downloads.mariadb.org/connector-odbc/)

It also uses the next libraries: 
- [PonyORM](https://ponyorm.org/)
- [NumPy](https://numpy.org/)
- [Pandas](https://pandas.pydata.org/)
- [AstroPy](https://www.astropy.org/)
- [Glob](https://docs.python.org/3/library/glob.html)
- [OS](https://docs.python.org/3/library/os.html)
- [Json](https://docs.python.org/3/library/json.html)

### Before execute
Before execute its neccesary to make an empty mariaDB database. You will need the name of the DB, username and password for the connection.

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
CREATE USER '//user_name//'@'localhost' IDENTIFIED BY '//password//';
```
And finally grant privileges to the database user:
```sql
GRANT ALL PRIVILEGES ON //database_name//.* TO '//username//'@'localhost';
```

### Execute the scripts

### museScript.py
First, you have to modify the next line at the end of the script with your database information:
```
db.bind(provider = 'mysql', host = '127.0.0.1', user = '//username//', passwd = '//password//', db = '//database_name//')
``` 
To execute museScript.py its neccesary to  have three folders in the same directory with the reduced, analysis, and raw files named 'single', 'analysis' and 'raw' respectively. At the moment to execute the script, you have to give as input the root directory where are the folders, or you can press enter if the script its already in the root directory.
The script will automatically read the files, create the classes respectively and PonyORM will map those to the MariaDB database.

### museRead.py
First, you have to modify the next line at the end of the script with your database information:
```
db.bind(provider = 'mysql', host = '127.0.0.1', user = '//username//', passwd = '//password//', db = '//database_name//')
``` 
When you execute the script, it will ask you a serie of inputs where these have the following structure:
``` 
//Number of the option//      # 1.- Exposures of one target 2.- All exposures 3.- Exit
//Target name//               # Only if you chose the option 1
//Extension name//
//Keyword of the extension//
    .
    .                         # You can ask for several keywords of a extension until you type 'stop'
    .
//Keyword of the extension//
STOP                          # Stop giving keywords 
//ExtensionName// || STOP      # You can ask for more extensions and repeat the process or type 'stop'
``` 
For example:
``` 
2                    #Number of the option
PRIMMARY             #Extension name     
ESO TEL AMBI TAU0    #Keyword of the extension
ESO TEL AMBI WINDSP  #Keyword of the extension
STOP                 #Stop giving keywords
CHAN01               #Extension Name
ESO DET OUT4 RON     #Keyword of the extension
STOP                 #Stop giving keywords
SGS_DATA             #Extension Name
OBJ1_FLUX            #Keyword of the extension
STOP                 #Stop giving keywords
STOP                 #Stop giving extensions
``` 

You can copy and paste the input in the terminal and the script will recognize the structure and make the queries correctly to the MariaDB database, or you can go step by step.
For now, this script makes a pandas DataFrame and print it with the asked values (or the average if those are a list of values) and with the PSF parameters as default.

### museDelete.py
First, you have to modify the next line at the end of the script with your database information:
```
db.bind(provider = 'mysql', host = '127.0.0.1', user = '//username//', passwd = '//password//', db = '//database_name//')
``` 
This script will drop all the tables of your database. 


If there is an error with the scripts or with the README like a misspelling or something, do not be afraid to send me an email to axel.reyes@sansano.usm.cl and thanks in advance.

