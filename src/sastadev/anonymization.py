'''
reimplements SASTA anonymization json data
See https://github.com/UUDigitalHumanitieslab/sasta/blob/develop/backend/anonymization.json


'''

import json
import os.path
import re

from sastadev.conf import settings

vertbar = '|'


anonymisationfile = os.path.join(settings.SD_DIR, 'data', 'anonymization.json')

with open(anonymisationfile) as json_file:
    anonymisationlist = json.load(json_file)

anonymisationdict = {key: dct["common"]
                     for dct in anonymisationlist for key in dct["codes"]}

#: The constant *sasta_pseudonyms* list the strings that replace names for
#: pseudonymisation purposes.
sasta_pseudonyms = [key for key in anonymisationdict]

#: The constant *pseudonym_patternlist* contains regular expressions for pseudonyms
#: based on elements from the *sasta_pseudonyms* (pseudonym + number).
pseudonym_patternlist = [r'^{}\d?$'.format(el) for el in sasta_pseudonyms]
pseudonym_pattern = vertbar.join(pseudonym_patternlist)
pseudonymre = re.compile(pseudonym_pattern)

def getname(rawcode: str) -> str:
    code = rawcode.upper()    # the code must be in all uppercase otherwise we do too much
    if code == '':
        return rawcode
    if code[-1] in '01234':
        prefix = code[:-1]
        suffix = code[-1]
        suffixint = int(suffix)
    else:
        return rawcode
    if prefix in anonymisationdict:
        result = anonymisationdict[prefix][suffixint]
    else:
        result = rawcode
    return result
