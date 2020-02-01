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


db.bind(provider = 'mysql', host = '127.0.0.1', user = 'aomuse', passwd = '#aomuse2020', db = 'aomuse')
db.generate_mapping(create_tables = True)
db.drop_all_tables(with_all_data = True)

