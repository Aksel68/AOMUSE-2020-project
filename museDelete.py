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


#   ----- Main -----

db.bind(provider='mysql', host='127.0.0.1', user='user', passwd='pass', db='dbname') # Establish the conection with the database
db.generate_mapping() # Map the classes with the database tables 
db.drop_all_tables(with_all_data = True) # Delete all the tables

