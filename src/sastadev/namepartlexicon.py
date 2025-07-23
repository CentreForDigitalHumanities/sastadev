'''


The namepartlexicon module:

* reads in the data from the file names/nameparts/namepartslexicon.csv
* stores it in the namepartlexicon  dictionary (Dict[str, int]) with its frequency
* provides  functions for checking membership of the namepartlexicon:



.. autofunction:: sastadev.namepartlexicon.namepart_isa_namepart
.. autofunction:: sastadev.namepartlexicon.namepart_isa_namepart_uc

'''

import csv
import os
from typing import Dict

from sastadev.conf import settings

tab: str = '\t'
namepartlexicon: Dict[str, int] = {}


def namepart_isa_namepart(word: str) -> bool:
    '''
    The function namepart_isa_namepart checks whether the string *word* occurs in the namepartlexicon dictionary.

    '''
    return word in namepartlexicon


def namepart_isa_namepart_uc(word: str) -> bool:
    '''
    The function namepart_isa_namepart_uc checks whether the string *word* with its initial character in upper case
    occurs in the namepartlexicon dictionary.

    '''
    if word is None or word == '':
        result = False
    else:
        uc = word[0].isupper()
        found = word in namepartlexicon
        result = uc and found
    return result


namepartfilename = os.path.join(settings.SD_DIR, 'data', 'names', 'nameparts', 'namepartlexicon.csv')
with open(namepartfilename, 'r', encoding='utf8') as namepartfile:
    csvreader = csv.reader(namepartfile, delimiter=tab)
    for row in csvreader:
        namepart = row[0]
        frq = int(row[1])
        namepartlexicon[namepart] = frq
