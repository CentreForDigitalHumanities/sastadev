'''
The module *alpino* provides functions related to Alpino structures. In particular,
it provides the function *getdehetwordinfo*:

* obtaining grammatical information from nouns in an Alpino parse

  .. autofunction:: sastadev.alpino::getdehetwordinfo

'''
#from __future__ import annotations

import copy
from typing import List, Tuple

from sastadev import lexicon, treebankfunctions
from sastadev.conf import settings
from sastadev.sastatypes import WordInfo


wordinfo_exceptions = {'Efteling': [('n', '1', 'e', 'Efteling')], 'efteling': [('n', '1', 'e', 'Efteling')]}

def getalpinowordinfo(word: str) -> List[WordInfo]:
    '''
    The function *getalpinowordinfo* parses the input word in isolation, extracts its properties and returns some of
    the properties as a list of WordInfo objects.

    Note that it is essential to parse the word in isolation, because unknown words
    that follow a uter determiner are analysed by Alpino as a uter noun
    (e.g. in *de ponyautootje*), even if they are analysed as neuter nouns in
    isolation.

    '''
    tree = settings.PARSE_FUNC(word)
    relevantnode = treebankfunctions.find1(tree, '//node[parent::node[@cat="top"]]')
    if relevantnode is None:
        return []
    else:
        pos = treebankfunctions.getattval(relevantnode, 'pt')
        if pos == 'n':
            genus = treebankfunctions.getattval(relevantnode, 'genus')
            dehet = lexicon.het if genus == 'onz' else lexicon.de
            getal = treebankfunctions.getattval(relevantnode, 'getal')
            graad = treebankfunctions.getattval(relevantnode, 'graad')
            infl = 'd' if graad == 'dim' else ''
            infl += 'e' if getal == 'ev' else 'm'
            lemma = treebankfunctions.getattval(relevantnode, 'lemma')
            return ([(pos, dehet, infl, lemma)])
        else:
            return []

def filter_wordinfos(wordinfos: List[WordInfo], dehet=None) -> List[WordInfo]:
    # if dehet==de and any of the alternatives is a de-word but no diminutive singular, we keep only these
    filtered_wordinfos = []
    if dehet == lexicon.de:
        filtered_wordinfos = [wordinfo for wordinfo in wordinfos if wordinfo[1] == lexicon.de and wordinfo[2] != 'de']
    # if dehet==het and any of the alternatives is a het-word or a de-word and  diminutive singular, we keep only these
    if dehet == lexicon.het:
        filtered_wordinfos = [wordinfo for wordinfo in wordinfos if
                              (wordinfo[1] == lexicon.het or
                               (wordinfo[1] == lexicon.de and wordinfo[2] == 'de')) and
                              wordinfo[2] in ['e', 'de']]
    if filtered_wordinfos == []:
        filtered_wordinfos = copy.deepcopy(wordinfos)
    return filtered_wordinfos




def getdehetwordinfo(wrd: str, dehet=None) -> Tuple[List[WordInfo], str]:
    '''
    The function *getdehetwordinfo*  determines the properties of the input string *word* by first looking in the
    lexicon. It only includes properties if the word is a noun.
    If not found in the lexicon, it tries to find the properties from Alpino by means of the function
    *getalpinowordinfo*.
    It returns a tuple consisting of a list of WordInfo objects and a string indicating the source where the properties
    have been found.

    .. autofunction:: sastadev.alpino::getalpinowordinfo
    '''

    wordinfos = []
    if wrd in wordinfo_exceptions:
        wordinfos = wordinfo_exceptions[wrd]
        source = 'exceptions'

    if wordinfos == []:
        wordinfos = lexicon.getwordinfo(wrd)

    # we only want to consider nouns or words of unknown word class (such as kopje in CELEX)
    raw_wordinfos = [wordinfo for wordinfo in wordinfos if wordinfo[0] in ['n', 'None']]
    wordinfos = filter_wordinfos(raw_wordinfos, dehet=dehet)

    # if not found yet we check with Alpino
    if wordinfos != []:
        source = 'celex'
    else:
        wordinfos = getalpinowordinfo(wrd)
        source = 'alpino'
    return (wordinfos, source)
