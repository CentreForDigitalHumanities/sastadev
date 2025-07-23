''''
The module top3000.py creates 3 dictionaries on the basis of the input file Woordenlijsten Current.xlsx in the
subfolder *top3000*:

* semlexicon: Dict[Tuple[str, DCOIPt], List[str]] stores the semantic properties of a (lemma, pt) tuple
* trlexicon: Dict[Tuple[str, DCOIPt], List[str]] stores the transitivity properties of a (lemma, pt) tuple
* genlexicon: Dict[Tuple[str, DCOIPt], List[str]] stores whether  (lemma, pt) tuple has a genitive form (List of yes|no)

It provides functions to determine these properties for a node:

* .. autofunction:: ishuman
* .. autofunction:: isanimate
* .. autofunction:: transitive
* .. autofunction:: intransitive
* .. autofunction:: pseudotr

The top3000 lexicon file has been derived from words as listed in various resources relate to N-CDI,
in particular a top 3000 words by Schlichting. It has the following columns:

* **OrigWord** original word as it occurs in the documents
* **Word** cleaned word
* **check** check whether word is found in Origword
* **Collocate**: word or words that cooccur with the word
* **Context**: contyext as specified in the original files
* **POS**: DCOI pt or cat code
* **semtype**: semantic type, partially from the original files, so far only human, animate are used
* **Regio**: to indicated BElgium-specific words
* **trans**: transitivity: tr, intr or tr/intr, tr/intr. Alpino does not retain the valence of a verb but adpats it to the context.
* **hasgen**: has a genitive form, for nouns only: yes or no
* **Top1000**: belongs to the Top 1000 words according to Schlichting (yes, no)
* **Top3000**	N-CDI jong kk: (also) occurs in the N-CDI file for jonge kinderen (yes, no)

The information needs extension and there are more files with relevant data.
'''

import os
from typing import Dict, List, Tuple

from sastadev.conf import settings
from sastadev.namepartlexicon import namepart_isa_namepart
from sastadev.sastatypes import DCOIPt, SynTree
from sastadev.stringfunctions import remove_underscore
from sastadev.treebankfunctions import getattval
from sastadev.xlsx import getxlsxdata


def ishuman(node: SynTree) -> bool:
    '''
    The function ishuman determines whether the node node is human
    '''
    lemma = getattval(node, 'lemma')
    pt = getattval(node, 'pt')
    vwtype = getattval(node, 'vwtype')
    result = (lemma, pt) in semlexicon and 'human' in semlexicon[(lemma, pt)]
    result = result or (vwtype == 'pers' and lemma != 'het')
    result = result or namepart_isa_namepart(lemma)
    return result


def isanimate(node: SynTree) -> bool:
    '''
    The function isanimate determines whether the nde node is animate
    '''

    lemma = getattval(node, 'lemma')
    pt = getattval(node, 'pt')
    result = (lemma, pt) in semlexicon and 'animate' in semlexicon[(lemma, pt)]
    return result


def transitivity(node: SynTree, tr: str) -> bool:
    '''
    The function transitivity determines whether the string tr occurs in trlexicon for (lemma, pt) of the node
    '''
    rawlemma = getattval(node, 'lemma')
    lemma = remove_underscore(rawlemma)
    pt = getattval(node, 'pt')
    result = (lemma, pt) in semlexicon and tr in trlexicon[(lemma, pt)]
    return result


def transitive(node: SynTree) -> bool:
    '''
    The function transitive determines whether node is transitive
    '''
    return transitivity(node, 'tr')


def pseudotr(node: SynTree) -> bool:
    '''
    The function pseudotr determines whether node is pseudotransitive
    '''
    return transitivity(node, 'tr/intr')


def intransitive(node: SynTree) -> bool:
    '''
    The function intransitve determines whether node is intransitive
    '''
    return transitivity(node, 'intr')


semicolon = ';'

filename = os.path.join(settings.SD_DIR, 'data', 'top3000', 'Woordenlijsten Current.xlsx')


lexiconheader, lexicondata = getxlsxdata(filename)

semlexicon: Dict[Tuple[str, DCOIPt], List[str]] = {}
trlexicon: Dict[Tuple[str, DCOIPt], List[str]] = {}
genlexicon: Dict[Tuple[str, DCOIPt], List[str]] = {}

for row in lexicondata:
    lemma = row[1].strip()
    pt = row[5]
    rawsems = row[6].split(semicolon)
    sems = [el.strip() for el in rawsems]
    semlexicon[(lemma, pt)] = sems

    rawtrs = row[8].split(semicolon)
    trs = [el.strip() for el in rawtrs]
    trlexicon[(lemma, pt)] = trs

    rawgens = row[9].split(semicolon)
    gens = [el.strip() for el in rawgens]
    genlexicon[(lemma, pt)] = gens
