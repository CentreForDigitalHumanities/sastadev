import os
from collections import defaultdict
from typing import Dict, List, Tuple

from spellchecker import SpellChecker

from sastadev.conf import settings
from sastadev.lexicon import spellingadditions
from sastadev.readcsv import readcsv

comma = ','
hyphen = '-'

trg = 'TRG'
oth = 'OTH'

FrqDict = Dict[str, int]

spell = SpellChecker(language='nl')
# the words in the dictionary that have not been found in the corpus have been assigned freqency 50
# and the following probability:
nonoccurrenceprobability = 1.3132493418801947e-07

# we use this as threshold;only words with a probability higher than this one are considered as candidates
okthreshold = nonoccurrenceprobability

# function to read the childes frequency dict in, for targets and others and combine them also
def getchildesfrq() -> Tuple[FrqDict, FrqDict, FrqDict]:
    trgfrqdict = defaultdict(int)
    othfrqdict = defaultdict(int)
    allfrqdict = defaultdict(int)
    childesfrqfilename = 'knownwordsfrq.txt'
    childeslexiconfolder = os.path.join(settings.SD_DIR, 'data/childeslexicon')
    childesfrqfullname = os.path.join(childeslexiconfolder, childesfrqfilename)
    idata = readcsv(childesfrqfullname)
    for _, row in idata:
        role = row[0]
        word = row[1]
        frq = int(row[2])
        if role == trg:
            trgfrqdict[word] += frq
        elif role == oth:
            othfrqdict[word] += frq
        else:
            pass
        allfrqdict[word] += frq
    return trgfrqdict, othfrqdict, allfrqdict

# function to read the stored corrections into a dictionary

def getstoredcorrections(correctionsfullname) -> Dict[str, List[Tuple[str, int]]]:
    correctionsdict = {}

    idata = readcsv(correctionsfullname)
    for i, row in idata:
        word = row[0]
        correctionsstr = row[1]
        correctionstrings = correctionsstr.split(comma)
        rawcorrections = [tuple(pairstr.split(hyphen)) for pairstr in correctionstrings]
        corrections = [(w, int(pen)) for  (w, pen) in rawcorrections]
        correctionsdict[word] = corrections

    return correctionsdict


def getpenalty(score, total):
    result = 101 + 100 - int(score/total*100)
    return result

#  a function for spelling correction

def children_correctspelling(word: str, correctionsdict, max = None, threshold=okthreshold) -> List[Tuple[str, int]]:
    if word in correctionsdict:
        return correctionsdict[word]
    else:
        corrections = spell.candidates(word)
    if corrections is not None:
        pairs = [(corr, spell.word_usage_frequency(corr)) for corr in corrections]
    else:
        corrections = []


    trgfrqs = [trgfrqdict[corr] if corr in trgfrqdict else 0 for corr in corrections]
    allfrqs = [allfrqdict[corr] if corr in allfrqdict else 0 for corr in corrections]
    probs = [spell.word_usage_frequency(corr) for corr in corrections]

    corrscores = zip(trgfrqs, allfrqs, probs)
    corrtuples = zip(corrections, corrscores)

    sortedcorrtuples = sorted(corrtuples, key=lambda x: x[1], reverse=True)


    # filter candidates that do not occur in trgfrq and allfrq and have too low a probability
    selectedsortedcorrtuples = [ct for ct in sortedcorrtuples if ct[1][0] != 0 or
                                ct[1][1] != 0 or ct[1][2] > threshold or ct[0] in spellingadditions]

    trgfrqsum = sum(corrtuple[1][0] for corrtuple in selectedsortedcorrtuples)
    allfrqsum = sum(corrtuple[1][1] for corrtuple in selectedsortedcorrtuples)
    probsum = sum(corrtuple[1][2] for corrtuple in selectedsortedcorrtuples)
    if trgfrqsum != 0:
        result = [(corr, getpenalty(score[0], trgfrqsum)) for (corr, score) in selectedsortedcorrtuples]
    elif allfrqsum != 0:
        result = [(corr, getpenalty(score[1], allfrqsum)) for (corr, score) in selectedsortedcorrtuples]
    elif probsum != 0:
        result = [(corr, getpenalty(score[2], probsum)) for (corr, score) in selectedsortedcorrtuples]
    else:
        result = []

    if max is not None:
        result = result[:max]


    # store the result in the dictionary; write dictionary to file

    return result


def adult_correctspelling(word: str, correctionsdict,max = None, threshold=okthreshold) -> List[Tuple[str, int]]:
    if word in correctionsdict:
        return correctionsdict[word]
    else:
        corrections = spell.candidates(word)
    if corrections is not None:
        corrtuples = [(corr, spell.word_usage_frequency(corr)) for corr in corrections]
    else:
        corrtuples = []

    sortedcorrtuples = sorted(corrtuples, key=lambda x: x[1], reverse=True)
    allfrqsum = sum(corrtuple[1]for corrtuple in sortedcorrtuples)

    result = [(corr, getpenalty(score, allfrqsum)) for (corr, score) in sortedcorrtuples]

    if max is not None:
        result = result[:max]

    # store the result in the dictionary; write dictionary to file

    return result


def tryme():
    words = ['kantie', 'opbijten', 'oprijten', 'opgereten', 'peelkaal' , ' beete' , 'kamm', 'daaistoel', 'oelen', 'tein']
    words = ['poppe']
    for word in words:
        result = children_correctspelling(word, children_correctionsdict, max=5)
        print(f'{word}: {result}' )

    words = ['motariek', 'silase']
    for word in words:
        result = adult_correctspelling(word, adult_correctionsdict, max=5)
        print(f'{word}: {result}' )





# read the childes frequency dict in, for targets and others and combine them also
trgfrqdict, othfrqdict, allfrqdict = getchildesfrq()

# read the stored corrections for children into a dictionary
children_correctionsfilename = 'children_storedcorrections.txt'
correctionspath = os.path.join(settings.SD_DIR, 'data/storedcorrections')
children_correctionsfullname = os.path.join(correctionspath, children_correctionsfilename)
children_correctionsdict = getstoredcorrections(
    children_correctionsfullname) if os.path.isfile(children_correctionsfullname) else {}

# read the stored corrections for adults into a dictionary
adult_correctionsfilename = 'adult_storedcorrections.txt'
correctionspath = os.path.join(settings.SD_DIR, 'data/storedcorrections')
adult_correctionsfullname = os.path.join(correctionspath, adult_correctionsfilename)
adult_correctionsdict = getstoredcorrections(
    adult_correctionsfullname) if os.path.isfile(adult_correctionsfullname) else {}



if __name__ == '__main__':
    tryme()