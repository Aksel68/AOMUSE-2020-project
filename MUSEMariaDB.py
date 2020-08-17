from pathlib import Path
import time
import os
from astropy.io import fits
from tqdm import tqdm
import numpy as np
import json
from pony.orm import *

provider = "mysql"
host = "127.0.0.1"
user = "username"
passwd = "password"
database_name = "DB_name"
rootDir = "/home/dir/to/data"

# FITS filenames to be ignored
ignore_list = ['PIXTABLE', 'MASTER', 'LINES', 'SKY', "STD_", "TRACE"]

##############################
# Actual script operations start from here, there should be no reason to edit these.
# HERE BE DRAGONS
##############################

db = Database()

# Target class describes an entry to the Target table in the database
# The classes have to inherit db.Entity from Pony
class Target(db.Entity):
    #   ----- Attributes -----

    target_name = Required(str, unique=True)  # Required: Cannot be None

    #   ----- Relations -----

    exposures = Set('Exposure')  # One target contains a set of exposures

# Exposure table class
class Exposure(db.Entity):
    #   ----- Attributes -----

    observation_time = Required(str, unique=True)
    insMode = Required(str)
    datacube_header = Optional(LongStr)
    raw_exposure_header = Optional(LongStr)
    raman_image_header = Optional(LongStr)
    psf_params = Optional(LongStr)
    sources = Optional(LongStr)

    #   ----- Relations -----

    target = Required('Target')  # One exposure belongs to a target


def fetch_data(header, keyword):
    try:
        return header[keyword]
    except KeyError:
        print('Keyword ' + keyword + ' not found.')


@db_session  # Decorator from Pony to make the function into a db session, thus the database can be modified
def museScript():
    """
    This function read 5 files (prm, psf, reduced, raman and raw) to store the information of each exposure in a database.

    For the prm file reads the PSFPARS extension and stores it in the 'psfParams' field of the exposure.
    For the psf file reads the 'PM_X' extensions, where X is the id of the source, and stores it in the
    'sources' field of the exposure.
    With other files the scripts takes the headers and saves them as json-like LongStr
    Also, from the primary header it stores the target and instrument mode of the exposure in their own fields    to make it easier the analysis from differents targets and instrument modes.
    """

    start = time.time()
    all_raw_files = []
    all_datacube_files = []
    all_raman_files = []
    all_prm_files = []
    all_psf_files = []

    skip_number = 0

    # FITS file scan and identification
    print("Generating list of fits files...")
    fits_list = list(Path(rootDir).rglob('*.fits'))

    print("Starting fits...")
    time.sleep(0.1)  # Makes the terminal output pretty
    for filepath in tqdm(fits_list):
        if any(ignored_word in filepath.parts[-1] for ignored_word in ignore_list):
            skip_number += 1
            continue
        try:
            header = fits.getheader(filepath)
        except:
            continue  # Probably a directory, move on
        try:
            if 'HIERARCH ESO DPR TYPE' in header and header['HIERARCH ESO DPR TYPE'] == "SKY":
                continue  # Sky observation, ignore
            if 'HIERARCH ESO DPR CATG' in header and header['HIERARCH ESO DPR CATG'] == "SCIENCE":
                all_raw_files.append(filepath)
                continue
            if 'HIERARCH ESO PRO CATG' in header and header['HIERARCH ESO PRO CATG'] == "DATACUBE_FINAL":
                if 'PROV2' in header:
                    continue  # This file is a combined cube, we ignore them
                all_datacube_files.append(filepath)
                continue
            if 'HIERARCH ESO PRO CATG' in header and header['HIERARCH ESO PRO CATG'] == "RAMAN_IMAGES":
                all_raman_files.append(filepath)
                continue
        except KeyError:
            pass  # File in question is not a proper ESO FITS product
        if ".prm" in filepath.parts[-1]:
            all_prm_files.append(filepath)
        if ".psf" in filepath.parts[-1]:
            all_psf_files.append(filepath)
        #TODO Add a check for the upcoming psf-per-wavelength files

    # FITS FZ file scan and identification
    # Sometimes raw products are compressed so we doublecheck them for raw files
    print("Generating list of fz files...")
    fits_list = list(Path(rootDir).rglob('*.fits.fz'))

    print("Starting fz...")
    time.sleep(0.1)  # Makes the terminal output pretty
    for filepath in tqdm(fits_list):
        header = fits.getheader(filepath)
        if 'HIERARCH ESO DPR TYPE' in header and header['HIERARCH ESO DPR TYPE'] == "SKY":
            continue  # Sky observation, ignore
        if 'HIERARCH ESO DPR CATG' in header and header['HIERARCH ESO DPR CATG'] == 'SCIENCE':
            all_raw_files.append(filepath)
    end = time.time()
    print('{:.3f}'.format(end-start) + " seconds to finish file search")
    print('{:d}'.format(len(all_raw_files)) + " raw science exposures found")
    print('{:d}'.format(len(all_datacube_files)) + " reduced datacubes found")
    print('{:d}'.format(len(all_raman_files)) + " raman files found")
    print('{:d}'.format(len(all_prm_files)) + " PRM files found")
    print('{:d}'.format(len(all_psf_files)) + " PSF files found")
    print('{:d}'.format(skip_number) + " files skipped")

    # Datacube extraction
    unique_observations = []
    reduced_cube_entries = []

    print("Parsing through found datacubes...")
    for reduced_cube_filename in all_datacube_files:

        cube_parameters = {}
        header = fits.getheader(reduced_cube_filename)

        try:
            target = header['OBJECT']  # Obtain the target name
        except KeyError:
            print("The header OBJECT does not exist")
        if Target.exists(target_name=target):  # If the target already exists in the database, get it from the db
            cube_parameters['target'] = Target.get(target_name=target)
        else:
            cube_parameters['target'] = Target(target_name=target)  # Else, create the target

        try:
            cube_parameters['observation_time'] = fetch_data(header, 'DATE-OBS')
            if not cube_parameters['observation_time'] in unique_observations:
                unique_observations.append(cube_parameters['observation_time'])
        except KeyError:
            print("The header DATE-OBS does not exist")

        cube_parameters['instrument_mode'] = fetch_data(header, 'HIERARCH ESO INS MODE')
        cube_parameters['header'] = dict(header)
        try:
            del cube_parameters['header']['COMMENT']  # and then delete the COMMENT key, because it does not have the JSON format and
        except KeyError:  # throws an error when saving it in the database
            pass

        reduced_cube_entries.append(cube_parameters)

    # PSF extraction
    psf_entries = []

    print("Parsing through found prm files...")
    for prm_file in all_prm_files:
        # PRM File
        observation_info = {}
        psfParams = {}  # Dictionary to store the extensions of the prm files
        sources = {}  # Dictionary to store the extensions (each source) of the psf files
        try:
            with fits.open(prm_file) as hduList:
                prm_filepath, prm_filename = os.path.split(prm_file)  # split to get the single file name
                # Notice that single file has the same root name that prm file
                expected_cube_name = prm_filename.replace('.prm', '')
                corresponding_cube_fullpath = prm_filepath + "/" + expected_cube_name
                expected_psf_name = prm_filename.replace('.prm', '.psf')
                corresponding_psf_fullpath = prm_filepath + "/" + expected_psf_name

                observation_info['observation_time'] = 'n/a'
                observation_info['target'] = 'n/a'
                observation_info['instrument_mode'] = 'n/a'
                # Check if the datacube is in the same directory, otherwise look elsewhere for it
                if Path(corresponding_cube_fullpath).exists():
                    observation_info['observation_time'] = fits.getheader(corresponding_cube_fullpath)['DATE-OBS']
                    observation_info['target'] = Target.get(target_name=fits.getheader(corresponding_cube_fullpath)['OBJECT'])
                    observation_info['instrument_mode'] = fits.getheader(corresponding_cube_fullpath)['HIERARCH ESO INS MODE']
                else:
                    for datacube_file in all_datacube_files:
                        if datacube_file.name == expected_cube_name:
                            observation_info['observation_time'] = fits.getheader(datacube_file)['DATE-OBS']
                            observation_info['target'] = Target.get(target_name = fits.getheader(datacube_file)['OBJECT'])
                            observation_info['instrument_mode'] = fits.getheader(datacube_file)['HIERARCH ESO INS MODE']
                            break

                if observation_info['target'] == 'n/a':
                    # PSF without target or observation parameters is kind of useless, skip these
                    print("Couldn't find a match for a prm file " + prm_filename + ".")
                    continue

                try:
                    params = hduList['PSFPARS'].data  # If the prm file does not have the PSFPARS extension, skip
                except KeyError:
                    continue
                try:
                    for i in range(len(params['name'])):  # The column 'name' is a list with the parameter names
                        parameter = params['name'][i]
                        value = params['polyfit'][i].tolist()  # The column 'polyfit' is a list of lists
                        psfParams[parameter] = value  # Store the polyfit of the PSF parameters
                    prmStep = hduList['SPECTRA'].header['CDELT3']
                    prmRestw = hduList['SPECTRA'].header['CRVAL3']
                    prmData = np.arange(hduList['SPECTRA'].header['NAXIS3'])  # Calculate the wavelength
                    prmWavelength = (prmRestw + (prmData * prmStep)) * 10 ** 9
                    psfParams['wavelength'] = prmWavelength.tolist()
                except:
                    print("Error: cannot read the PSF parameters")
        except FileNotFoundError:
            print(f"The file {prm_filename} does not exist\n")  # If the prm file does not exists, skip
            continue

            # PSF File
        try:
            with fits.open(corresponding_psf_fullpath) as hduList:
                for tupla in hduList.info(False):  # Iterate in the list of the extensions
                    if ('PM_' in tupla[1]):  # Looking for the 'PM_X' extensions, where X is the id of the source
                        sourceID = tupla[1]
                        sourceData = {}  # Dictionary that will store the data of the source
                        table = hduList[sourceID].data  # Access to the source extension
                        i = 0
                        for column in table.columns.names:  # Iterate in the list of column names
                            sourceData[column] = table[column].tolist()  # Store the column with its list of values
                            i += 1
                        sources[sourceID] = sourceData  # Store the source data
        except FileNotFoundError:
            print(f"The file {corresponding_psf_fullpath} does not exist\n")  # If the psf file does not exists, skip
            continue

        psf_entries.append((observation_info.copy(), psfParams.copy(), sources.copy()))

    # Raw exposure extraction

    raw_fits_entries = []
    for raw_filename in all_raw_files:

        raw_parameters = {}
        header = fits.getheader(raw_filename)

        try:
            target = fetch_data(header, 'OBJECT')  # Obtain the target name
        except KeyError:
            print("The header OBJECT does not exist")
        if Target.exists(target_name=target):  # If the target already exists in the database, get it from the db
            raw_parameters['target'] = Target.get(target_name=target)
        else:
            raw_parameters['target'] = Target(target_name=target)  # Else, create the target

        try:
            raw_parameters['observation_time'] = header['DATE-OBS']
            if not raw_parameters['observation_time'] in unique_observations:
                unique_observations.append(raw_parameters['observation_time'])
        except KeyError:
            print("The header DATE-OBS does not exist")

        raw_parameters['instrument_mode'] = fetch_data(header, 'HIERARCH ESO INS MODE')
        raw_parameters['header'] = dict(header)
        try:
            del raw_parameters['header']['COMMENT']  # and then delete the COMMENT key, because it does not have the JSON format and
        except KeyError:  # throws an error when saving it in the database
            pass
        try:
            del raw_parameters['header']['']  # and then delete the '' key, because it does not have the JSON format and
        except KeyError:  # throws an error when saving it in the database
            pass

        raw_fits_entries.append(raw_parameters)

    # Raman file extraction
    raman_fits_entries = []
    for raman_filename in all_raman_files:

        raman_parameters = {}
        header = fits.getheader(raman_filename)

        try:
            target = header['OBJECT']  # Obtain the target name
        except KeyError:
            print("The header OBJECT does not exist")
        if Target.exists(target_name=target):  # If the target already exists in the database, get it from the db
            raman_parameters['target'] = Target.get(target_name=target)
        else:
            raman_parameters['target'] = Target(target_name=target)  # Else, create the target

        try:
            raman_parameters['observation_time'] = fetch_data(header, 'DATE-OBS')
            if not raman_parameters['observation_time'] in unique_observations:
                unique_observations.append(raman_parameters['observation_time'])
        except KeyError:
            print("The header DATE-OBS does not exist")

        raman_parameters['instrument_mode'] = fetch_data(header, 'HIERARCH ESO INS MODE')
        raman_parameters['header'] = dict(header)
        try:
            del raman_parameters['header']['COMMENT']  # and then delete the COMMENT key, because it does not have the JSON format and
        except KeyError:  # throws an error when saving it in the database
            pass

        raman_fits_entries.append(raman_parameters)

    # Identification and linking of previous files to a same exposure
    new_entries = 0
    modified_entries = 0
    for observation_key in unique_observations:
        observation_dictionary = {}
        for reduced_cube_entry in reduced_cube_entries:
            if observation_key in reduced_cube_entry['observation_time']:
                observation_dictionary['target'] = reduced_cube_entry['target']
                observation_dictionary['observation_time'] = reduced_cube_entry['observation_time']
                observation_dictionary['insMode'] = reduced_cube_entry['instrument_mode']
                observation_dictionary['datacube_header'] = reduced_cube_entry['header']
                reduced_cube_entries.remove(reduced_cube_entry)
                break
        for raw_fits_entry in raw_fits_entries:
            if observation_key in raw_fits_entry['observation_time']:
                observation_dictionary['target'] = raw_fits_entry['target']
                observation_dictionary['observation_time'] = raw_fits_entry['observation_time']
                observation_dictionary['insMode'] = raw_fits_entry['instrument_mode']
                observation_dictionary['raw_exposure_header'] = raw_fits_entry['header']
                raw_fits_entries.remove(raw_fits_entry)
                break
        for raman_fits_entry in raman_fits_entries:
            if observation_key in raman_fits_entry['observation_time']:
                observation_dictionary['target'] = raman_fits_entry['target']
                observation_dictionary['observation_time'] = raman_fits_entry['observation_time']
                observation_dictionary['insMode'] = raman_fits_entry['instrument_mode']
                observation_dictionary['raman_image_header'] = raman_fits_entry['header']
                raman_fits_entries.remove(raman_fits_entry)
                break
        for psf_entry in psf_entries:
            if observation_key in psf_entry[0]['observation_time']:
                observation_dictionary['target'] = psf_entry[0]['target']
                observation_dictionary['observation_time'] = psf_entry[0]['observation_time']
                observation_dictionary['insMode'] = psf_entry[0]['instrument_mode']
                observation_dictionary['psf_params'] = psf_entry[1]
                observation_dictionary['sources'] = psf_entry[2]
                psf_entries.remove(psf_entry)
                break

        # Modify headers into more JSON-like format
        if 'psf_params' in observation_dictionary:
            observation_dictionary['psf_params'] = json.dumps(observation_dictionary['psf_params'])
        if 'sources' in observation_dictionary:
            observation_dictionary['sources'] = json.dumps(observation_dictionary['sources'])
        if 'raman_image_header' in observation_dictionary:
            observation_dictionary['raman_image_header'] = json.dumps(observation_dictionary['raman_image_header'])
        if 'raw_exposure_header' in observation_dictionary:
            observation_dictionary['raw_exposure_header'] = json.dumps(observation_dictionary['raw_exposure_header'])
        if 'datacube_header' in observation_dictionary:
            observation_dictionary['datacube_header'] = json.dumps(observation_dictionary['datacube_header'])

        # Check if exposure exists, create a new exposure if not and modify existing one if needed
        if not Exposure.exists(observation_time=observation_dictionary['observation_time']):
            Exposure(**observation_dictionary)
            new_entries += 1
        else:
            entry_is_modified = False
            modified_entry_dictionary = {}
            database_entry = Exposure.get(observation_time=observation_dictionary['observation_time'])
            for column, value in observation_dictionary.items():
                # Ignore columns that shouldn't change for an observation
                if (column == 'observation_time' or
                        column == 'target' or
                        column == 'insMode'):
                    continue
                database_value = getattr(database_entry, column)
                if not value == database_value:
                    modified_entry_dictionary[column] = value
                    entry_is_modified = True
            if entry_is_modified:
                database_entry.set(**modified_entry_dictionary)
                modified_entries += 1

    print('Finished updating the database, ' + '{:d}'.format(new_entries) + " new entries and "
          + '{:d}'.format(modified_entries) + " modified entries.")


# Main part starts here
db.bind(provider="mysql", host="127.0.0.1", user=user, passwd=passwd, db=database_name)
db.generate_mapping(check_tables=False, create_tables=True)

museScript()
