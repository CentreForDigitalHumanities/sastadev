'''
The CELEX lexicon consists of 3 backslash-separated value files:

* DMW (dmwcdok.txt): word forms and their properties
* DML (dmlcd.txt): lemmas and their morphological properties
* DSL (dslcd.txt): lemmas and their syntactic properties

These files can be found in the folder celexlexicondata/dutch in the code folder.

We store these in the celexlexicon module in python dictionaries:

* dmwkeydict: key = word identifier, value = whole record for this identifier
* dmldict: key = lemma identifier, value = whole record for this identifier
* dsldict: key = lemma identifier, value = whole dsl record for this identifier

We define the following indexes (as python dictionaries) for quick lookup in this module:

* dmwlemmakeyinflindex: key = (lemma identifier, infl), value = List of word form identifiers
* dmwdict: key = word form, value = list of word identifiers

This module also contains functions to map CELEX inflection codes to DCOI inflection codes, and the other way around,
as well as functions to generate inflected forms for a given lemma, pos-code and inflectional properties.

'''

import csv
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from sastadev import treebankfunctions
from sastadev.conf import settings
from sastadev.sastatypes import CELEX_INFL, SynTree, WordInfo

backslash = '\\'
celexsep = backslash

pospattern = r'^.*\[(?P<pos>.)\]$'
posre = re.compile(pospattern)


# dml columns
IdNum, Head, Inl, MorphStatus, MorphCnt, DerComp, Comp, Def, Imm, \
    ImmSubCat, ImmAllo, ImmSubst, StrucLab, StrucAllo, StrucSubst, Sepa = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15

# verbs that do not necessarily have a t suffix  in present tense singular
no_t_verbs = {'mogen', 'kunnen', 'zullen', 'willen'}

logfile = sys.stderr

# initialisation
# read the celex lexicon
inputfolder = os.path.join(settings.SD_DIR, 'data', 'celexlexicon', 'dutch')

dmwfilename = 'DMWCDOK.txt'
dmwfullname = os.path.join(inputfolder, dmwfilename)
dmwdict: Dict[str, List[str]] = {}
dmwlemmakeyinflindex: Dict[Tuple[str, str], List[str]] = defaultdict(list)
dmwkeydict = {}

# dmw columns: recid, form, lemmakey, pos, infl


with open(dmwfullname, mode='r') as infile:
    myreader = csv.reader(infile, delimiter=celexsep)
    for row in myreader:
        thekey = row[0]
        dmwkeydict[thekey] = row
        theform = row[1]
        if theform in dmwdict:
            dmwdict[theform].append(thekey)
        else:
            dmwdict[theform] = [thekey]
        lemmainflkey = (row[3], row[4])
        dmwlemmakeyinflindex[lemmainflkey].append(row[0])

dmlfilename = 'DMLCD.txt'
dmlfullname = os.path.join(inputfolder, dmlfilename)
dmldict: Dict[str, List[str]] = {}

with open(dmlfullname, mode='r') as infile:
    myreader = csv.reader(infile, delimiter=celexsep)
    for row in myreader:
        thekey = row[IdNum]
        if thekey in dmldict:
            print('Warning: Duplicate key in dmlcd: {}'.format(thekey), file=logfile)
        dmldict[thekey] = row


# The dsl.cd file contains the following fields:
dslIdNum, dslHead, dslInl, dslClassNum, dslGendNum, dslDeHetNum, dslPropNum, \
    dslAuxNum, dslSubClassVNum, dslSubCatNum, dslAdvNum, dslCardOrdNum, dslSubClassPNum = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12

posnum2pos = {'0': 'None', '1': 'n', '2': 'adj', '3': 'tw', '4': 'ww', '5': 'lid', '6': 'vnw', '7': 'bw', '8': 'vz', '9': 'vw', '10': 'tsw'}
pos2posnum = {posnum2pos[key]: key for key in posnum2pos}


dslfilename = 'DSLCD.txt'
dslfullname = os.path.join(inputfolder, dslfilename)
dsldict: Dict[str, List[str]] = {}
dsllemmaposindex: Dict[Tuple[str, str], List[str]] = defaultdict(list)


with open(dslfullname, mode='r') as infile:
    myreader = csv.reader(infile, delimiter=celexsep)
    for row in myreader:
        thekey = row[dslIdNum]
        if thekey in dsldict:
            print('Warning: Duplicate key in dslcd: {}'.format(thekey), file=logfile)
        dsldict[thekey] = row
        lemmaposkey = (row[dslHead], row[dslClassNum])
        dsllemmaposindex[lemmaposkey].append(thekey)


def dcoiphi2celexpv(thesubj: SynTree, thepv: SynTree, inversion: bool) -> str:
    '''
    :param thesubj: subject node
    :param thepv: finite verb node
    :param inversion: True or False
    :return:
    '''
    (rawperson, number, _) = treebankfunctions.getphi(thesubj)
    lemma = treebankfunctions.getlemma(thesubj)
    if lemma in ['het']:
        person = '3'
        number = 'ev'
    else:
        person = '3' if rawperson == '' else rawperson
    tense = treebankfunctions.getattval(thepv, 'pvtijd')
    pvnumber = treebankfunctions.getattval(thepv, 'pvagr')
    celexperson = person[0] if person != '' and ((number in ['ev', 'getal'] and tense == 'tgw') or (tense == '')) else ''
    if number != 'getal' and number != '':
        celexnumber = number[0]
    elif lemma in ['je']:
        celexnumber = 'e'
    elif celexperson in ['1', '2', '3']:
        celexnumber = 'e'
    elif pvnumber == 'met-t':
        celexnumber = 'e'
    elif pvnumber == '':
        celexnumber = 'm'  # assuming that we are dealing with an infinitive
    else:
        celexnumber = pvnumber[0]
    celextense = tense[0] if tense != '' else 't'  # in case a verb is analysed as inf instead of as  pv
    celexinversion = 'I' if inversion else ''
    result = celextense + celexnumber + celexperson + celexinversion
    return result


celex2dcoimap: Dict[str, Dict[str, str]] =\
    {'a': {'pvtijd': 'conj', 'pvagr': 'ev', 'wvorm': 'pv'},
     'te1': {'pvtijd': 'tgw', 'pvagr': 'ev', 'wvorm': 'pv'},
     'te2': {'pvtijd': 'tgw', 'pvagr': 'ev', 'wvorm': 'pv'},
     'te2t': {'pvtijd': 'tgw', 'pvagr': 'met-t', 'wvorm': 'pv'},
     'te3': {'pvtijd': 'tgw', 'pvagr': 'ev', 'wvorm': 'pv'},
     'te3t': {'pvtijd': 'tgw', 'pvagr': 'met-t', 'wvorm': 'pv'},
     'te2I': {'pvtijd': 'tgw', 'pvagr': 'ev', 'wvorm': 'pv'},
     'tm': {'pvtijd': 'tgw', 'pvagr': 'mv', 'wvorm': 'pv'},
     've': {'pvtijd': 'verl', 'pvagr': 'ev', 'wvorm': 'pv'},
     'vm': {'pvtijd': 'verl', 'pvagr': 'mv', 'wvorm': 'pv'},
     'i': {'wvorm': 'inf', 'positie': 'vrij', 'buiging': 'zonder'},
     'pv': {'wvorm': 'vd', 'positie': 'vrij', 'buiging': 'zonder'},
     'pvC': {'graad': 'comp', 'buiging': 'zonder', 'naamval': 'stan'},  # gecoordineerder. probably an error
     'pt': {'wvorm': 'td', 'positie': 'vrij', 'buiging': 'zonder'},
     'pvE': {'wvorm': 'vd', 'buiging': 'met-e', 'positie': 'prenom'},
     'ptE': {'wvorm': 'td', 'buiging': 'met-e', 'positie': 'prenom'},
     'pvEe': {'wvorm': 'vd', 'buiging': 'met-e', 'positie': 'nom'},  # de afgescheidene
     'ptEm': {'wvorm': 'td', 'buiging': 'met-e', 'positie': 'prenom', 'getal': 'mv-n'},
     'g': {'pvtijd': 'tgw', 'pvagr': 'ev', 'wvorm': 'pv'},          # wees
     'e': {'getal': 'ev', 'naamval': 'stan', 'graad': 'basis'},
     'm': {'getal': 'mv', 'naamval': 'stan', 'graad': 'basis'},
     'De': {'getal': 'ev', 'naamval': 'dat', 'graad': 'basis'},  # nouns maybe adapt for pronouns (aller)
     'Dm': {'getal': 'mv', 'naamval': 'stan', 'getalN': 'mv-n', 'buiging': 'met-e', 'positie': 'nom'},  # in CELEX only
     # for possesive  pronouns  mijnen hunnen  etc
     'Ge': {'getal': 'ev', 'naamval': 'gen', 'graad': 'basis'},  # aanschijns
     'Gm': {'getal': 'mv', 'naamval': 'gen', 'graad': 'basis'},  # aller
     'GP': {'buiging': 'met-s', 'positie': 'postnom', 'graad': 'basis'},  # iets moois
     'de': {'getal': 'ev', 'naamval': 'stan', 'graad': 'dim'},
     'dm': {'getal': 'mv', 'naamval': 'stan', 'graad': 'dim'},
     'P': {'graad': 'basis', 'buiging': 'zonder', 'naamval': 'stan'},
     'C': {'graad': 'comp', 'buiging': 'zonder', 'naamval': 'stan'},
     'S': {'graad': 'sup', 'buiging': 'zonder', 'naamval': 'stan'},
     'CE': {'graad': 'comp', 'buiging': 'met-e', 'naamval': 'stan'},
     'SE': {'graad': 'sup', 'buiging': 'met-e', 'naamval': 'stan'},
     'PE': {'graad': 'basis', 'buiging': 'met-e', 'naamval': 'stan'},   # but
     'PEe': {'graad': 'basis', 'buiging': 'met-e', 'naamval': 'stan'},
     'CEm': {'graad': 'comp', 'buiging': 'met-e', 'naamval': 'stan', 'getal': 'mv-n'},
     'CE': {'graad': 'comp', 'buiging': 'met-e', 'naamval': 'stan'},
     'PEm': {'graad': 'basis', 'buiging': 'met-e', 'naamval': 'stan', 'getal': 'mv-n'},
     'DPE': {'graad': 'basis', 'buiging': 'met-e', 'naamval': 'dat'},  # arren
     'X': {}

     }


def celexpv2dcoi(word: str, infl: str, lemma: str) -> Dict[str, str]:
    results: Dict[str, str] = {}
    if infl not in celex2dcoimap:
        results = {}
    elif infl in {'te2', 'te3'}:
        if lemma[-3] == 't':
            results = celex2dcoimap[infl]
        elif lemma in no_t_verbs:
            results = celex2dcoimap[infl]
        else:
            results = celex2dcoimap[infl + 't']
    else:
        results = celex2dcoimap[infl]
    return results


def celex2dcoi(word: str, infl: str, lemma: str) -> Dict[str, str]:
    if infl.endswith('s'):
        return celex2dcoi(word, infl[:-1], lemma)
    pvresults = celexpv2dcoi(word, infl, lemma)
    return pvresults

def isa_vd(word: str) -> bool:
    if word in dmwdict:
        wordkeys = dmwdict[word]
        for wordkey in wordkeys:
            props = dmwkeydict[wordkey]
            if props[4] == 'pv':
                return True
    return False

def isa_inf(word: str) -> bool:
    if word in dmwdict:
        wordkeys = dmwdict[word]
        for wordkey in wordkeys:
            props = dmwkeydict[wordkey]
            if props[4] == 'i':
                return True
    return False


def incelexdmw(str: str) -> bool:
    result = str in dmwdict
    return result


def incelexdmwpos(word: str, pos: str) -> bool:
    result = incelexdmw(word)
    poslist = getposlist(word)
    result = result and pos in poslist
    return result


def getlemmas(word: str) -> List[str]:
    '''
    yields a list of lemmas for the input string word
    :param word:
    :return:
    '''

    lemmas = []
    lemmakeys = getlemmakeys(word)
    for lemmakey in lemmakeys:
        if lemmakey is not None:
            if lemmakey in dmldict:
                lemma = dmldict[lemmakey][1]
                lemmas.append(lemma)
            else:
                lemma = None
        else:
            lemma = None
    return lemmas


def getlemmakeys(word: str) -> List[str]:
    '''
    yields a list of lemma identifiers for the input string word
    :param word:
    :return:
    '''
    lemmakeys = []
    if word in dmwdict:
        for key in dmwdict[word]:
            featurelist = dmwkeydict[key]
            lemmakey = featurelist[3]
            lemmakeys.append(lemmakey)
    else:
        lemmakeys = []
    return lemmakeys


def getdehet(lemmakey: str) -> Optional[str]:
    '''
    yields the dehet property of the lemma identifier lemmakey
    :param lemmakey:
    :return: return values are lexicon.de, lexicon.het, 'n/a' or None
    '''
    if lemmakey in dsldict:
        dehet = dsldict[lemmakey][dslDeHetNum]
    else:
        dehet = None
    if dehet == '':
        dehet = 'n/a'
    return dehet


def oldgetpos(lemmakey: str) -> Optional[str]:
    if lemmakey in dmldict:
        wordstructure = dmldict[lemmakey][StrucLab]
        m = posre.match(wordstructure)
        if m is not None:
            pos = m.group('pos')
        else:
            pos = 'None'
    else:
        pos = None
    return pos


def getpos(lemmakey: str) -> Optional[str]:
    '''
    returns the DCOI pt Part of Speech code for the lemma identifier lemmakey, or None
    :param lemmakey:
    :return:
    '''
    if lemmakey in dsldict:
        features = dsldict[lemmakey]
        posnum = features[dslClassNum]
        if posnum in posnum2pos:
            pos = posnum2pos[posnum]
        else:
            pos = 'None'
    return pos


def getposlist(word: str) -> List[str]:
    '''
    returns a list of pt Part of speech codes for the input string word
    :param word:
    :return:
    '''
    poslist = []
    lemmakeys = getlemmakeys(word)
    for lemmakey in lemmakeys:
        pos = getpos(lemmakey)
        poslist.append(pos)
    return poslist


def getinfls(word: str) -> List[CELEX_INFL]:
    '''
    returns a list of CELEX inflection codes for the input string word
    :param word:
    :return:
    '''
    infls = []
    if word in dmwdict:
        for key in dmwdict[word]:
            featurelist = dmwkeydict[key]
            infl = featurelist[4]
            infls.append(infl)
    return infls


def getwordposinfo(word: str, pos: str) -> List[WordInfo]:
    '''
    returns a list of WordInfo for the input string word with part of speech code pos
    :param word:
    :param pos:
    :return:
    '''
    cands = getwordinfo(word)
    results: List[WordInfo] = [(pt, dehet, infl, lemma) for (pt, dehet, infl, lemma) in cands if pt == pos]
    return results


def getwordinfo(word: str) -> List[WordInfo]:
    '''
    returns a lis of WordInfo for the input string word
    :param word:
    :return:
    '''
    pos_infl_lemmas: List[WordInfo] = []
    if word in dmwdict:
        for key in dmwdict[word]:
            featurelist = dmwkeydict[key]
            infl = featurelist[4]
            lemmakey = featurelist[3]
            lemma = dmldict[lemmakey][1]
            pos = getpos(lemmakey)
            dehet = getdehet(lemmakey)
            pos_infl_lemmas.append((pos, dehet, infl, lemma))
    return pos_infl_lemmas


def getinflforms(lemma: str, numClass: str, infl: str) -> List[str]:
    '''
    returns alist of inflected word forms for the input string lemma with CELEX part of speech code numClass
    and the CELEX inflectional properties infl
    :param lemma:
    :param numClass:
    :param infl:
    :return:
    '''
    results = []
    lemmakeys = dsllemmaposindex[(lemma, numClass)]
    for lemmakey in lemmakeys:
        wordkeys = dmwlemmakeyinflindex[(lemmakey, infl)]
        for wordkey in wordkeys:
            results.append(dmwkeydict[wordkey][1])
    return results
