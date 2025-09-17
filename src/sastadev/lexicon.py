'''
The lexicon module is the interface to the lexicon.
It is intended to abstract from the concrete lexicon used.

Currently we especially use the CELEX lexicon.
This module also contains some special word lists. Perhaps we should set up a special Exception List module
for this purpose.


'''
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

from sastadev import celexlexicon, treebankfunctions
from sastadev.conf import settings
from sastadev.methods import MethodName, stap, tarsp
from sastadev.namepartlexicon import (namepart_isa_namepart,
                                      namepart_isa_namepart_uc)
from sastadev.readcsv import readcsv
from sastadev.sastatypes import CELEX_INFL, DCOITuple, Lemma, SynTree, WordInfo
from sastadev.stringfunctions import ispunctuation, strip_accents

alpinoparse = settings.PARSE_FUNC
space = ' '

celex = 'celex'
alpino = 'alpino'

# the CHAT codes xxx and yyy must be recognised as valid codes and as valid words in some cases
chatspecials = ['xxx', 'yyy']


lexicon = celex



#Alpino often analyses certain words as tsw though they should be analysed as nouns
tswnouns = ['baby', 'jongen', 'juf', 'juffrouw', 'mam', 'mama', 'mamma', 'meisje', 'mens', 'meneer', 'mevrouw',
            'pap', 'papa', 'pappa', 'stouterd', 'opa', 'oma']

de = '1'
het = '2'
# List of de-determiners, List of corresponding het-determiners, and implicitly by this a mapping between the two
dets = {}
dets[de] = ['de', 'die', 'deze', 'onze', 'welke', 'iedere', 'elke', 'zulke']
dets[het] = ['het', 'dat', 'dit', 'ons', 'welk', 'ieder', 'elk', 'zulk']

possessive_determiners = ['mijn' , "m'n", "jouw", "je", "uw", "zijn", "z'n", "haar", "d'r",
                          "ons", "onze", "jullie", "hun"]
definite_determiners = ['de', 'het', 'deze', 'die', 'dit', 'dat']

valid_ambiguous_words = ['zijn', 'wel', 'niet', 'effe', 'mij', 'drinken', 'dees', 'hun', 'vin', 'pot', 'jou', 'ken']

rpronoun_lemmas = ['daar', 'er', 'ergens', 'hier', 'nergens', 'overal', 'waar']

alt_pt_ww_n_pairdict = {'eten': 'voedsel'}

def initializelexicon(lexiconfilename) -> set:
    lexicon = set()
    fptuples = readcsv(lexiconfilename, header=False)
    for _, fp in fptuples:
        strippedwords = [el.strip() for el in fp]
        if len(strippedwords) == 1:
            lexicon.add(strippedwords[0])
        else:
            lexitem = tuple(strippedwords)
            lexicon.add(lexitem)
    return lexicon

def initializelexicondict(lexiconfilename) -> Dict[str,str]:
    lexicon = {}
    fptuples = readcsv(lexiconfilename, header=False)
    for _, fp in fptuples:
        strippedword = fp[0].strip()
        strippedreplacement = fp[1].strip()
        lexicon[strippedword] = strippedreplacement
    return lexicon


def geninitializelexicondict(lexiconfilename, key: int, header=True) -> Dict[str, List[str]]:
    lexicon = {}
    fptuples = readcsv(lexiconfilename, header=header)
    for _, fp in fptuples:
        strippedkey = fp[key].strip()
        strippedentry = [el.strip() for el in fp]
        lexicon[strippedkey] = strippedentry
    return lexicon


def initializelexicondefdict(lexiconfilename) -> Dict[str,List[str]]:
    lexicon = defaultdict(list)
    fptuples = readcsv(lexiconfilename, header=False)
    for _, fp in fptuples:
        strippedword = fp[0].strip()
        strippedreplacement = fp[1].strip()
        lexicon[strippedword].append(strippedreplacement)
    return lexicon

def isa_namepart(word: str) -> bool:
    '''
    is the word a name part
    :param word:
    :return:
    '''
    return namepart_isa_namepart(word)


def isa_namepart_uc(word: str) -> bool:
    '''
    is the word in upper case a name part
    :param word:
    :return:
    '''
    return namepart_isa_namepart_uc(word)


def lookup(dct: Dict[str, Any], key: str) -> str:
    '''
    looks up key in dct, if so it returns dct[key] else ''
    :param dct:
    :param key:
    :return:
    '''
    result = dct[key] if key in dct else ''
    return result


def pvinfl2dcoi(word: str, infl: CELEX_INFL, lemma: Lemma) -> Optional[DCOITuple]:
    '''
    encodes the CELEX code infl for word (which must be a pv) as a DCOI Tuple
    at least if the CELEX lexicon is used, else None
    :param word:
    :param infl:
    :param lemma:
    :return:
    '''
    if lexicon == celex:
        results = celexlexicon.celexpv2dcoi(word, infl, lemma)
        wvorm = lookup(results, 'wvorm')
        pvtijd = lookup(results, 'pvtijd')
        pvagr = lookup(results, 'pvagr')
        positie = lookup(results, 'positie')
        buiging = lookup(results, 'buiging')
        dcoi_infl = []
        atts = [wvorm, pvtijd, pvagr, positie, buiging]
        for att in atts:
            if att != '':
                dcoi_infl.append(att)
        result = tuple(dcoi_infl)
    else:
        result = None
    return result


def isa_vd(word) -> bool:
    return celexlexicon.isa_vd(word)

def isa_inf(word) -> bool:
    return celexlexicon.isa_inf(word)


def getwordposinfo(word: str, pos: str) -> List[WordInfo]:
    '''
    yields the list of WordInfo for word str with part of speech code pos by looking it up in the lexicon in use
    :param word:
    :param pos:
    :return:
    '''
    results = []
    if lexicon == celex:
        results = celexlexicon.getwordposinfo(word, pos)
        if results == []:
            cleanword = strip_accents(word)
            results = celexlexicon.getwordposinfo(cleanword, pos)
    return results


def getwordinfo(word: str) -> List[WordInfo]:
    '''
    yields the list of WordInfo for word str  by looking it up in the lexicon in use
    :param word:
    :return:
    '''
    results = []
    if lexicon == celex:
        results = celexlexicon.getwordinfo(word)
        if results == []:
            cleanword = strip_accents(word)
            results = celexlexicon.getwordinfo(cleanword)
    return results


def informlexicon(word: str) -> bool:
    '''
    checks whether word is in the  word form lexicon
    :param word:
    :return:
    '''
    allwords = word.split(space)
    result = True
    for aword in allwords:
        if lexicon == 'celex':
            wordfound = celexlexicon.incelexdmw(aword)
            if not wordfound:
                cleanword = strip_accents(aword)
                wordfound = celexlexicon.incelexdmw(cleanword)
            result = result and wordfound
        elif lexicon == 'alpino':
            result = False
        else:
            result = False
    return result


def informlexiconpos(word: str, pos: str) -> bool:
    '''
    checks whether word with part of speech code pos is in the word form lexicon
    :param word:
    :param pos:
    :return:
    '''

    allwords = word.split(space)
    result = True
    for aword in allwords:
        if lexicon == 'celex':
            wordfound = celexlexicon.incelexdmwpos(aword, pos)
            if not wordfound:
                cleanword = strip_accents(aword)
                wordfound = celexlexicon.incelexdmwpos(cleanword, pos)
            result = result and wordfound
        elif lexicon == 'alpino':
            result = False
        else:
            result = False
    return result

def issuperadjective(wrd: str) -> bool:
    lcwrd = wrd.lower()
    stem = lcwrd[5:]
    result = lcwrd.startswith('super') and informlexiconpos(stem, 'adj')
    return result



def chatspecial(word: str) -> bool:
    result = word in chatspecials
    return result


def known_word(word: str, includealpinonouncompound=True) -> bool:
    '''
    a word is considered to be a known_word if it occurs in the word form lexicon,
    if it is a name part, or if it is a chatspecial item, or in a lexicon with additional words,
    or  a compound noun recognised as such by Alpino (the latter unless excluded)
    but not in the nonwordslexicon
    :param word:
    :return:
    '''
    result = informlexicon(word) or isa_namepart(word) or \
             chatspecial(word) or word in additionalwordslexicon or \
             isallersuperlative(word) or issuperadjective(word)
    if includealpinonouncompound:
        result = result or isalpinonouncompound(word)
    result = result and word not in nonwordslexicon
    return result


comma = ','
compoundsep = '_'

def validword(wrd: str, methodname: MethodName, includealpinonouncompound=True) -> bool:
    result = wrd == '' or known_word(wrd, includealpinonouncompound=includealpinonouncompound)
    if methodname in {tarsp, stap}:
        result = result and not nochildword(wrd)
    return result

def validnotalpinocompoundword(wrd: str, methodname: MethodName) -> bool:
    result = validword(wrd, methodname, includealpinonouncompound=False)
    return result


def nochildword(wrd: str) -> bool:
    result = wrd in nochildwords
    return result

def isalpinonouncompound(wrd: str) -> bool:
    if ispunctuation(wrd):
        return False
    fullstr = f'geen {wrd}'  # geen makes it a noun and can combine with uter and neuter, count and mass, sg and plural
    tree = alpinoparse(fullstr)
    # find the noun
    if tree is None:
        settings.LOGGER.error(f'Parsing {fullstr} failed')
        return False
    nounnode = treebankfunctions.find1(tree, './/node[@pt="n"]')
    if nounnode is None:
        # settings.LOGGER.error(f'No noun found in {fullstr} parse')
        return False
    nounwrd = treebankfunctions.getattval(nounnode, 'word')
    if nounwrd != wrd:
        settings.LOGGER.error(f'Wrong noun ({nounwrd}) found in {fullstr} parse')
        return False
    nounlemma = treebankfunctions.getattval(nounnode, 'lemma')
    if compoundsep in nounlemma:
        parts = nounlemma.split(compoundsep)
        unknownparts = [part for part in parts if not known_word(part) and part != "DIM"]
        result = unknownparts == []
        if not result:
            settings.LOGGER.error(f'Unknown words ({comma.join(unknownparts)}) found in {fullstr} parse')
            return False
        return True
    else:
        return False


def isallersuperlative(wrd:str) -> bool:
    result = wrd.startswith('aller') and (wrd.endswith('st') or wrd.endswith('ste')) and informlexicon(wrd[5:])
    return result

def getinflforms(thesubj: SynTree, thepv: SynTree, inversion: bool) -> List[str]:
    '''
    yields the list of  finite verb word forms that
    -agrees with the subject node (thesubj),
    -has the same lemma as the word form in the pv node
    -is compatible with whether there is inversion or not
    :param thesubj:
    :param thepv:
    :param inversion:
    :return:
    '''
    if lexicon == 'celex':
        pt = treebankfunctions.getattval(thepv, 'pt')
        pos = celexlexicon.pos2posnum[pt]
        infl = celexlexicon.dcoiphi2celexpv(thesubj, thepv, inversion)
        lemma = treebankfunctions.getattval(thepv, 'lemma')
        results = celexlexicon.getinflforms(lemma, pos, infl)
    else:
        results = []
    return results


def alldutchwords(correct: str) -> bool:
    newcorrect = correct
    words = newcorrect.split()
    result = all([isvalidtoken(word) for word in words])
    return result

# def allenglishwords(correct:str) -> bool:
#     newcorrect = correct
#     words = newcorrect.split()
#     result = all([word in englishlexicon for word in words])
#     result = result and len(words) > 1
#     return result


def isvalidtoken(wrd:str) -> bool:
    result = known_word(wrd) or ispunctuation(wrd)
    return result


nochildwordsfilename = 'nochildwords.txt'
nochildwordsfolder = 'data/nochildwords'
nochildwordsfullname = os.path.join(settings.SD_DIR, nochildwordsfolder, nochildwordsfilename)
nochildwords = initializelexicon(nochildwordsfullname)

lexiconfoldername = 'data/wordsunknowntoalpino'
wordsunknowntoalpinofilename = 'wordsunknowntoalpino.txt'
wordsunknowntoalpinofullname = os.path.join(settings.SD_DIR, lexiconfoldername, wordsunknowntoalpinofilename)
wordsunknowntoalpinolexicondict = initializelexicondefdict(wordsunknowntoalpinofullname)

lexiconfoldername = 'data/filledpauseslexicon'

filledpausesfilename = 'filledpauseslexicon.txt'
filledpausesfullname = os.path.join(settings.SD_DIR, lexiconfoldername, filledpausesfilename)
filledpauseslexicon = initializelexicon(filledpausesfullname)

nomlulexiconfilename = 'notanalyzewords.txt'
nomlulexiconfullname = os.path.join(settings.SD_DIR, lexiconfoldername, nomlulexiconfilename)
nomlulexicon = initializelexicon(nomlulexiconfullname)

vuwordslexiconfilename = 'vuwordslexicon.txt'
vuwordslexiconfullname = os.path.join(settings.SD_DIR, lexiconfoldername, vuwordslexiconfilename)
vuwordslexicon = initializelexicondict(vuwordslexiconfullname)

additionalwordsfilename = 'additionalwordslexicon.txt'
additionalwordsfullname = os.path.join(settings.SD_DIR, lexiconfoldername, additionalwordsfilename)
additionalwordslexicon = initializelexicon(additionalwordsfullname)

nonwordsfilename = 'nonwordslexicon.txt'
nonwordsfullname = os.path.join(settings.SD_DIR, lexiconfoldername, nonwordsfilename)
nonwordslexicon = initializelexicon(nonwordsfullname)

spellingadditionsfilename  = 'spellingadditions.txt'
spellingadditionsfullname = os.path.join(settings.SD_DIR, lexiconfoldername, spellingadditionsfilename)
spellingadditions = initializelexicon(spellingadditionsfullname)

wrongposwordslexiconfilename = 'wrongposwordslexicon.txt'
wrongposwordslexiconfullname = os.path.join(settings.SD_DIR, lexiconfoldername, wrongposwordslexiconfilename)
wrongposwordslexicon = initializelexicon(wrongposwordslexiconfullname)

# validnouns is intended for nous  that Alpino assigns frame (both,both, both) but that are valid Dutch words
validnouns = {'knijper', 'roosvicee'}

lexiconfoldername = 'data/wordsunknowntoalpino'
lemmalexiconfilename = 'lemmalexicon.txt'
lemmalexiconfulname = os.path.join(settings.SD_DIR, lexiconfoldername, lemmalexiconfilename)
lemmalexicon = initializelexicondict(lemmalexiconfulname)

lexiconfoldername = 'data/wordsunknowntoalpino'
cardinallexiconfilename = 'cardinalnumerals.tsv'
cardinallexiconfullname = os.path.join(settings.SD_DIR, lexiconfoldername, cardinallexiconfilename)
cardinallexicon = geninitializelexicondict(cardinallexiconfullname, 0)


interjections = ['ja', 'nee', 'kijk', 'oh', 'he', 'hoor', 'hè', 'o', 'hee', 'mama', 'okee', 'hé', 'ah', 'oeh', 'au',
                 'oja', 'joh', 'jee', 'mam', 'bah', 'jawel', 'mamma', 'ho', 'boem', 'ha', 'sorry',
                 'ooh', 'daag', 'haha', 'nou', 'papa', 'pappa', 'toe', 'maar', 'oei', 'aah', 'hallo', 'dankjewel',
                 'oeps', 'oo', 'toch', 'wauw', 'goh', 'aha', 'vooruit', 'dan', 'tjonge',
                 'hèhè', 'jaja', 'hoi', 'waar', 'bb', 'help', 'meneer', 'hi', 'ach', 'ee', 'hup', 'oooh', 'heh', 'm',
                 'ma', 'sst', 'och', 'tja', 'lieverd', 'hahaha', 'hoera', 'pap',
                 'echt', 'lalala', 'hopla', 'da', 'pff', 'hai', 'jongens', 'juffrouw', 'jeetje', 'tot', 'ziens', 'hihi',
                 'jonge', 'ohh', 'poeh', 'oef',
                 'meisje', 'aaah', 'auw', 'meid', 'niet', 'poe', 'en', 'schat', 'wel', 'ai', 'goed', 'xxxx', 'dat',
                 'doei', 'tjongejonge', 'ooooh', 'hoewel', 'of',
                 'oke', 'neenee', 'pfff', 'mens', 'ps', 'oow', 'fff', 'juf', 'mevrouw', 'baby', 'dankuwel', 'waw',
                 'welterusten', 'sehhahahaha', 'hihihi', 'aaaah', 'wee', 'shit',
                 'pa', 'grr', 'weltrusten', 'pats', 'weh', 'stouterd', 'dag', 'joepie', 'neej', 'hoho', 'rara',
                 'joehoe', 'schatje', 'hierzo', 'pffff', 'ahh', 'ahah', 'tjee',
                 'liefje', 'pf', 'ahaha', 'hoppa', 'ahahaha', 'verdorie', 'ssst', 'foei', 'gossie', 'ok', 'joe', 'tsja',
                 'gatverdamme', 'grrr', 'welnee', 'god', 'tjeetje', 'doeg',
                 'wah', 'getver', 'ohja', 'hej', 'zak', 'alhoewel', 'neen', 'goedzo', 'ahahah', 'allee', 'jo', 'jongen',
                 'pardon', 'hihihihi', 'floep', 'lieve', 'gatver', 'kut', 'bro',
                 'mja', 'tsjonge', 'hohoho', 'klopt', 'man', 'jezus', 'truste', 'ppf', 'goedemorgen', 'domoor',
                 'aaaaah', 'okeee', 'yes', 'ahahahaha', 'zo', 'huh']
fillers = ['eh', 'ehm', 'ah', 'boe', 'hm', 'hmm',
           'uh', 'uhm', 'ggg', 'mmm', 'ja', 'nee', 'veh']
allfillers = fillers + ['&-' + filler for filler in fillers] + \
    interjections + ['&-' + intj for intj in interjections]

tsw_non_words = ['ee']

modalverbs = ['hoeven', 'moeten', 'mogen', 'kunnen', 'willen', 'zullen']

preferably_intransitive_verbs = ['gaan', 'slapen', 'rekenen'] + modalverbs

kijkvuadverbs = ['eens', 'dan', 'hier', 'zo']

chatcodes = ["xxx", "xx", "yyy", "yy"]


junk = 0

# to have a breakpoint after the last lexicon read
