# to do
from copy import deepcopy
from typing import Callable, List, Tuple

from lxml import etree

from sastadev import compounds
from sastadev.conf import settings
from sastadev.lexicon import (filledpauseslexicon, informlexicon)
from sastadev.metadata import (filled_pause, fstoken, intj, janeenou, longrep,
                               repeated, repeatedjaneenou, repeatedseqtoken,
                               shortrep, substringrep, unknownsymbol,
                               unknownword)
from sastadev.phonetics import phoneticise
from sastadev.sastatoken import Token
from sastadev.sastatypes import Nort, SynTree
from sastadev.stringfunctions import deduplicate, string2list
from sastadev.tblex import asta_recognised_wordnode
from sastadev.treebankfunctions import (all_lower_consonantsnode, find1,
                                        getattval, getnodeyield, getsentence, getxsid,
                                        lastmainclauseof, openclasspts)

nodetype = etree._Element

positionatt = 'end'

xmetaxpath = './/xmeta'

samplesizemdvalues = {repeatedjaneenou, intj,
                      shortrep,  unknownsymbol, filled_pause}   # intj really belong to samplesize:
# Voor de tussenwerpsels: in de appendix 2022 beschrijven we dat interjecties als au, goh, tjongejonge, jeetje,
# en ook geluidsnabootsingen, dat we deze niet meetellen voor samplesize.
mlumdvalues = {repeated, repeatedseqtoken, longrep, unknownword, substringrep, janeenou,
               fstoken}

filled_pause_exceptions = ['e', 'ə', 'ee', 'n', 't']

class DupInfo:
    '''
    The class *DupInfo* defines objects for storing information about duplicate and
    partially duplicate words, both for long duplications (>=50%) and for short
    duplications (<50%). In addition it contains a list of words in incomplete sentences
    '''

    def __init__(self, longdups=dict(), shortdups=dict(), icsws=[]):
        self.longdups = longdups
        self.shortdups = shortdups
        self.icsws = icsws  # nodes for words in incomplete sentences

    def __str__(self):
        result = str(self.longdups) + ';' + \
            str(self.shortdups) + str(self.icsws)
        return result

    def merge(self, dupinfo):
        '''
        The method *merge* merges two DupInfo objects by dictmerging their longdups
        dictionaries, their shortdups dictionaries, and by concatenating the lists of
        words form incomplete sentences.
        '''
        newdupinfo = deepcopy(self)
        newdupinfo.longdups = dictmerge(self.longdups, dupinfo.longdups)
        newdupinfo.shortdups = dictmerge(self.shortdups, dupinfo.shortdups)
        newdupinfo.icsws = self.icsws + dupinfo.icsws
        return newdupinfo

    def get_chaintail(self, i):
        if i in self.shortdups:
            result = self.get_chaintail(self.shortdups[i])
        elif i in self.longdups:
            result = self.get_chaintail(self.longdups[i])
        else:
            result = i
        return result


def dictmerge(dict1, dict2):
    '''
    The function *dictmerge* merges two dictionaries dict1 and dict2 into a new
    dictionary, but only for non-conflicting and non-identical key-value pairs.
    '''
    newdict = deepcopy(dict1)
    for el in dict2:
        if el in newdict:
            if newdict[el] != dict2[el]:
                settings.LOGGER.error(
                    'Conflicting values for {}: {}: {} not included'.format(
                        el, newdict[el], dict2[el]
                    )
                )
            else:
                settings.LOGGER.warning(
                    'Duplicate values for {}: {} = {}'.format(el, newdict[el], dict2[el]))
        else:
            newdict[el] = dict2[el]
    return newdict


normalisedict = {'c': 'k'}

#: The constant *unwantedtokenlist* contains symbols and symbol sequences that should
#: be ignored for the sample size
unwantedtokenlist = ['-', '--', '#', '–', '\u2013', '\u2014', '\u2015']

incomplete_zijn = '''
// node[node[ @rel = "hd" and @lemma="zijn"] and
        not (node[ @rel="predc" or @rel="vc" or @rel="ld" or ( @rel="mod" and @lemma="er") or
             node[ @rel = "mod" and node[ @rel = "hd" and (@lemma="voor")]]
           ])
         and count(. // node[ @ pt]) < 6
       ]
'''

incomplete_hebben = '''
//node[node[@rel="hd" and @lemma="hebben"] and
       (not(node[@rel="obj1" or @rel="vc" or @rel="svp"]) )
       and count(.//node[@pt]) < 6
      ]
'''

incomplete_eentw = '''
//node[node[(@rel!="det" and @rel!="hd" and @rel!="mwp" and @rel!="--") and @lemma="één"] and not(node[@lemma="er"])]
'''

#: The variable *incompletexpaths* contains Xpath queries to identify incomplete
#: phrases in an utterance. It currently contains 3 such queries:
#:
#:   * one for clauses headed by *hebben*
#:   * one for clauses headed by *zijn*
#:   * one for incomplete noun phrases just consisting of *een* (often wrongly interpreted
#:     by Alpino as a full NP consisting of the numeral *één*.)
#:
incompletexpaths = [incomplete_hebben, incomplete_zijn, incomplete_eentw]

space = ' '

janeenouset = set()
janeenouset = {'ja', 'nee', 'nou'}

janeeset = set()
janeeset = {'ja', 'nee'}


def getposition(nort):
    if nort is None:
        result = None
    elif isinstance(nort, Token):
        result = nort.pos
    elif isinstance(nort, nodetype):
        result = getattval(nort, positionatt)
    else:
        result = ('??')
    return result


def getword(nort):
    if nort is None:
        result = ''
    elif isinstance(nort, Token):
        result = nort.word
    elif isinstance(nort, nodetype):
        result = getattval(nort, 'word')
    else:
        result = '**'
    return result


def onvolledig(stree):
    results = []
    if incomplete(stree):
        results += [stree]
    return results


def incomplete(stree):
    result = False
    for query in incompletexpaths:
        if result:
            break
        else:
            allmatches = stree.xpath(query)
            matches = [m for m in allmatches if m == lastmainclauseof(stree)]
            result = matches != []
    return result


def incompletetreeleaves(stree: SynTree) -> List[SynTree]:
    '''
    The function *incompletetreeleaves returns a list of all nodes for words that are
    part of an incomplete sentence. A sentence is incomplete if it matches a query from the list of queries in the variable *incompletexpaths*.

    .. autodata:: sastadev.dedup::incompletexpaths

    '''
    results = []
    for query in incompletexpaths:
        allmatches = stree.xpath("." + query)
        matches = [m for m in allmatches if m != lastmainclauseof(stree)]
        for m in matches:
            results += getnodeyield(m)
    return results


def findcorrections(nodelist):
    wordlist = [getattval(n, 'word') for n in nodelist]
    resultlist = []
    lnodelist = len(nodelist)
    for i in range(lnodelist - 1):
        n1 = nodelist[i]
        n2 = nodelist[i + 1]
        if getattval(n1, 'pt') == getattval(n2, 'pt'):
            resultlist.append((n1, n2))
    return resultlist


def isxxx(node):
    theword = getword(node)
    result = theword.lower() in {'xxx', 'yyy', 'www'}
    return result


def isfilledpausenort(nort: Nort) -> bool:
    '''
    The function *isfilledpausenort* returns the result of the function *isfilledpause* applied to the *word* of *nort*.

      * .. autofunction:: sastadev.dedup::isfilledpause
    '''

    theword = getword(nort)
    result = isfilledpause(theword)
    return result


def getfilledpauses(nortlist: List[Nort]) -> List[Nort]:
    '''
    The function *getfilledpauses returns Norts that are in nortlist for which the
    function *isfilledpausenort* yields True.

      * .. autofunction:: sastadev.dedup::isfilledpausenort

    '''
    resultlist = [tok for tok in nortlist if isfilledpausenort(tok) and not isfilledpauseexceptionnort(tok)]
    return resultlist

def isfilledpauseexceptionnort(nort: Nort) -> bool:
    word = getword(nort)
    result = word in filled_pause_exceptions
    return result

def infilledpauses(word: str) -> bool:
    return (word in filledpauseslexicon)


def isfilledpause(word: str) -> bool:
    '''
    The function *isfilledpause* determines whether *word* is a filled pause. This is
    the case if

    * the lower case variant of *word* is contained in the *filledpauseslexicon*
    * or else if a deduplicated version of the lower case variant of *word* is contained in the *filledpauseslexicon*

    Otherwise the function returns False.

    Deduplication is achived by the function *deduplicate* from the module *stringfunctions*

    '''
    lcword = word.lower()
    if infilledpauses(lcword):
        result = True
    else:
        swords = deduplicate(lcword, infilledpauses)
        if (swords != []):
            result = True
        else:
            result = False
    return result


def getfilledpausesposlist(nortlist):
    results = []
    for token in nortlist:
        theword = getword(token)
        if isfilledpause(theword):
            thepos = getposition(token)
            results.append(thepos)
    return results


def remove_duplicates(wl):
    stop = False
    result = wl
    lwl = len(wl)
    ml = lwl // 2
    tobedeleted = []
    for curlen in range(ml, 0, -1):
        for startpos in range(0, lwl - 2 * curlen + 1, 1):
            if isduplicate(wl[startpos:startpos + curlen],
                           wl[startpos + curlen:startpos + 2 * curlen]):
                newwl = wl[:startpos] + wl[startpos + curlen:]
                result = remove_duplicates(newwl)
                stop = True
                break
        if stop:
            break
    return result


def isnortsubstring(n1, n2):
    w1 = getword(n1)
    w2 = getword(n2)
    lcw1 = w1.lower()
    lcw2 = w2.lower()
    result = lcw1 in lcw2 and len(w1) / len(w2) > 0.5
    return result


def find_substringduplicates2(wl: List[Nort]) -> Tuple[List[Nort], DupInfo]:
    '''
    The function *find_substringduplicates2* finds nodes with words that are a
    substring of the word  of the successor node, and it creates a DupInfo object that
    contains a dictionary  with <position substring word, position successor word> items.

    '''
    dupmapping = dict()
    result = []
    lwl = len(wl)
    for i in range(lwl - 1):
        curtoken = wl[i]
        nexttoken = wl[i + 1]
        curlcword = getword(curtoken).lower()
        if isnortsubstring(curtoken, nexttoken) and not (informlexicon(curlcword)):
            duppos = getposition(curtoken)
            origpos = getposition(nexttoken)
            dupmapping[duppos] = origpos
            result.append(curtoken)
    alldupinfo = DupInfo(dupmapping, dict())
    return result, alldupinfo


def find_simpleduplicates(wl):
    result, _ = find_simpleduplicates2(wl)
    return result


def find_simpleduplicates2(wl: List[Nort]) -> Tuple[List[Nort], DupInfo]:
    '''
    The function *find_simpleduplicates2* identifies each Nort that is a duplicate of
    its successor. It returns a list of these Norts and a dictionary of
    <position of the duplicate: position of its successor> items as the longdups part in
    a DupInfo object.

    '''
    dupmapping = dict()
    result = []
    lwl = len(wl)
    for i in range(lwl - 1):
        if isnortduplicate([wl[i]], [wl[i + 1]]):
            duppos = getposition(wl[i])
            origpos = getposition(wl[i + 1])
            dupmapping[duppos] = origpos
            result.append(wl[i])
    alldupinfo = DupInfo(dupmapping, dict())
    return result, alldupinfo


def getreptokenpos(nort, dupinfo):
    nortpos = getposition(nort)
    if nortpos in dupinfo:
        result = str(dupinfo[nortpos])
    else:
        result = ''
    return result


def find_duplicates(wl):
    result, _ = find_duplicates2(wl)
    return result


# applies to a sequence of Lassy word nodes or token  nodes (Nort)
def find_duplicates2(wl: List[Nort]) -> Tuple[List[Nort], DupInfo]:
    '''
    The function *find_duplicates2* identifies each Nort sequence  that is a duplicate of
    its successor Nort sequence. It returns a list of these Norts and a dictionary of  the
    position of the duplicate and the positions of its successor items as the longdups
    part in a DupInfo  object.

    '''

    dupmapping = dict()
    alldupinfo = DupInfo()
    stop = False
    result = wl
    lwl = len(wl)
    ml = lwl // 2
    result = []
    for curlen in range(ml, 1, -1):  # minimum length is 2
        # for startpos in range(0, lwl-2*curlen+1,1):
        for startpos in range(lwl - 2 * curlen, -1,
                              -1):  # find dup seqeunces starting at the rightmost position
            if isnortduplicate(wl[startpos:startpos + curlen],
                               wl[startpos + curlen:startpos + 2 * curlen]):
                result = [wl[p] for p in range(startpos, startpos + curlen)]
                for p in range(startpos, startpos + curlen):
                    duppos = getposition(wl[p])
                    origpos = getposition(wl[p + curlen])
                    dupmapping[duppos] = origpos
                    alldupinfo = DupInfo(dupmapping, dict())
                newwl = wl[:startpos] + wl[startpos + curlen:]
                restresult, restdupinfo = find_duplicates2(newwl)
                result += restresult
                alldupinfo = alldupinfo.merge(restdupinfo)

                stop = True
                break
        if stop:
            break
    return result, alldupinfo


def find_janeenouduplicates(wl):
    result, _ = find_janeenouduplicates2(wl)
    return result


def find_janeenouduplicates2(wl):
    resultlist = []
    dupmapping = dict()
    lwl = len(wl)
    for i in range(lwl - 1):
        wlip = getposition(wl[i])
        wli1p = getposition(wl[i + 1])
        wliw = getword(wl[i])
        wli1w = getword(wl[i + 1])
        lcwliw = wliw.lower()
        lcwli1w = wli1w.lower()
        if lcwliw in janeenouset and lcwliw == lcwli1w:
            resultlist.append(wl[i])
            dupmapping[wlip] = wli1p
    dupinfo = DupInfo(longdups=dupmapping, shortdups=dict())
    return resultlist, dupinfo


def normalisestring(str1: str) -> str:
    '''
    The function *normalisestring* carries out normalisation by means of the function
    *phoneticise* from the *phonetics* module:

    .. autofunction:: sastadev.phonetics::phoneticise

    '''
    result = phoneticise(str1)
    return result


def isnortduplicate(tlist1: List[Nort], tlist2: List[Nort]) -> bool:
    '''
    The function *isnortduplicate* determines whether tlist1 is a duplicate of tlist2,
    which is the case if the lists have equal length and each normalised word of
    tlist1 is equal to or a prefix of the corresponding normalised word in tlist2.

    Normalisation is carried out to be robust against certain spelling variations and
    is taken care of by the function *normalisestring*:

    *  .. autofunction:: sastadev.dedup::normalisestring

    '''
    result = True
    ltlist1 = len(tlist1)
    ltlist2 = len(tlist2)
    result = ltlist1 == ltlist2
    if result:
        for i in range(ltlist1):
            lcword1 = getword(tlist1[i]).lower()
            lcword2 = getword(tlist2[i]).lower()
            nlcword1 = normalisestring(lcword1)
            nlcword2 = normalisestring(lcword2)
            result = result and ((nlcword1 == nlcword2)
                                 or nlcword2.startswith(nlcword1))
    return result


def nextnode(node, nodes):
    for i, n in enumerate(nodes):
        if n == node:
            if i + 1 < len(nodes):
                return nodes[i + 1]
            else:
                return None


def nodesfindjaneenou(nodes):
    janees = [n for n in nodes if getattval(n, 'lemma') in {'ja', 'nee'}]
    nous = [n for n in nodes if getattval(n, 'lemma') == 'nou' and (
        getattval(n, 'rel') in {'mwp', 'tag', 'cnj'}
        or getattval(nextnode(n, nodes), 'lemma') in {'ja', 'nee'})]
    results = janees + nous
    return results


def treefindjaneenou(stree):
    janees = stree.xpath('.//node[@lemma="ja" or @lemma="nee"]')
    nous = stree.xpath(
        './/node[@lemma="nou" and (@rel="mwp" or @rel="tag" or @rel="cnj" )] ')
    results = janees + nous
    return results


def findjaneenou(nortlist):
    resultlist = findnodefromset(nortlist, janeenouset)
    return resultlist


def findjanee(nortlist):
    resultlist = findnodefromset(nortlist, janeeset)
    return resultlist


def findnodefromset(nortlist, wordset):
    resultlist = []
    for node in nortlist:
        theword = getword(node)
        lctheword = theword.lower()
        if lctheword in wordset:
            resultlist.append(node)
    return resultlist


def isduplicate(wlist1, wlist2):
    result = wlist1 == wlist2
    return result


def cleantokenlist(tokenlist, tobedeleted):
    cleanlist = [t for t in tokenlist if getposition(t) not in tobedeleted]
    cleanstrlist = [getword(t) for t in cleanlist]
    cleanstr = space.join(cleanstrlist)
    return cleanstr


def correct(stree):
    correct1xpath = './/node[@cat="top" and node[(@cat="smain" or @cat="sv1" or @cat="whq" or @cat="whsub")] and  count(node[@cat])=1]'
    correct2xpath = './/node[@cat="top" and node[@cat="du" and node[@rel="dlink" or @rel="tag"] and node[(@cat="smain" or @cat="sv1" or @cat="whq" or @cat="whsub") and @rel="nucl"] ]]'
    correct3xpath = './/node[@cat="top" and node[@cat="du" and node[@cat="conj" and count(node[(@cat="smain" or @cat="sv1" or @cat="whq"  or @cat="whsub")])>1] ]]'
    correct4xpath = './/node[@cat="top" and  node[@cat="conj" and count(node[(@cat="smain" or @cat="sv1" or @cat="whq"  or @cat="whsub")])>1] ]'
    correct5xpath = './/node[@cat="top" and  node[@cat="du" and count(node)=2 and node[@rel="dp" or @rel="tag" and @end<../node[@rel="nucl"]/@end] and node[(@cat="smain" or @cat="sv1" or @cat="whq")]] ]'
    matches1 = stree.xpath(correct1xpath)
    matches2 = stree.xpath(correct2xpath)
    matches3 = stree.xpath(correct3xpath)
    matches4 = stree.xpath(correct4xpath)
    matches5 = stree.xpath(correct5xpath)
    matches = matches1 + matches2 + matches3 + matches4 + matches5
    results = []
    for m in matches:
        if not incomplete(m):
            results.append(m)
    return results


def mlux(stree: SynTree) -> List[SynTree]:
    '''
    The function *mlux* determines which nodes for word in *stree* should be included
    for the computation of the mean length utterance (mlu) by applying the function
    *mlux2* to *stree*. The latter function returns a node list and metadata on the
    excluded word nodes.

    .. autofunction:: sastadev.dedup::mlux2

    '''
    result, _ = mlux2(stree)
    return result


def mlux2(stree: SynTree) -> Tuple[List[SynTree], DupInfo]:
    '''
    The function *mlux2* returns a tuple consisting of a list of nodes for words that
    should be included in computing the mean length utterance (mlu), and information
    about duplications in a DupInfo object.

    * It first obtains a list of nodes for words, in the right surface order, of *stree*
    * It filters those nodes that are found by *samplesize* (:ref:`A045_X`)
    * The function maintains two variables:

      * **cleantokennodelist**: the list of nodes still in the utterance
      * **resultnodelist**: the list of nodes that are in the result of this function
      * Each node that is added to the resultnodelist is removed from the cleantokennodelist

    * It updates these variables for  all nodes  if any of the nodes has *word* equal to *xxx*,  *yyy* or  *www*
    * It updates these variables for nodes that have been found by an earlier correction process: these are listed in the metadata.
    * it updates these variables for nodes for  unknown words that are of an open class part of speech
    * it updates these variables for nodes for nodes for the words *ja*, *nee*, *nou*
    * it updates these variables for nodes for interjections (*pt=tsw*)
    * it updates these variables for nodes for filledpauses as found in the :ref:`filledpauseslexicon`
    * it updates these variables for nodes for words and word sequences that are duplicated, using the function *find_simpleduplicates2*:

       * .. autofunction:: sastadev.dedup::find_simpleduplicates2

    * it updates these variables for nodes for word sequences that are duplicated, using the function *find_duplicates2*:

       * .. autofunction:: sastadev.dedup::find_duplicates2

    * it updates these variables for nodes for words the prefix of which is a repetition of its successor, where the prefix is larger than 50% of the length of its successor (long duplications). It does so by means of the function *getprefixwords2*:

       * .. autofunction::sastadev.dedup::getprefixwords2

   * it updates these variables for nodes for unknown words that are a substring of their successor. It does so using the function  *find_substringduplicates2*:

       * .. autofunction:: sastadev.dedup::find_substringduplicates2

   * it updates these variables for nodes for words that consist of consonants only
   * it updates these variables for nodes for words in incomplete sentences.
   Determining the incompleteness of a sentence is very difficult and is so far only done for a limited number of sentence types. It uses the function *incompletetreeleaves* for this purpose:

      * .. autofunction:: sastadev.dedup::incompletetreeleaves

   The function does not (yet) deal with:
    *  false starts, e.g. word + *nee* / *eh* word;  w of pos1 w of pos1
    * the sequence *of nee*
    * *dus* als stopwoordje

    '''
    debug = False
    if debug:
        etree.dump(stree)
    resultnodelist = []
    alldupinfo = DupInfo()
    tokennodelist = getnodeyield(stree)
    excludednodes, dupinfo = samplesize2(stree)
    cleantokennodelist = [n for n in tokennodelist if n not in excludednodes]
    alldupinfo = alldupinfo.merge(dupinfo)

    # remove all if xxx/yyy/www occurs ; this can be done here
    xxxfound = any([isxxx(n) for n in cleantokennodelist])
    if xxxfound:
        resultnodelist = cleantokennodelist
        cleantokennodelist = []

    # add results that have been found earlier by reduce in correction and that are now in the metadata
    # and exclude these nodes for further processing
    if cleantokennodelist != []:
        mdnodes = []
        mlumds = stree.xpath(xmetaxpath)
        for mlumd in mlumds:
            if 'value' in mlumd.attrib and mlumd.attrib['value'] in mlumdvalues:
                tokenbeginstr = mlumd.attrib['annotatedposlist']
                tokenbegins = string2list(tokenbeginstr)
                for tokenbegin in tokenbegins:
                    nodexpath = './/node[(@pt or @pos) and @begin="{}"]'.format(tokenbegin)
                    newnode = find1(stree, nodexpath)
                    if newnode is not None:
                        mdnodes.append(newnode)
                    else:
                        settings.LOGGER.error(
                            'Metadata node not found in tree: md.begin={}'.format(
                                tokenbegin))
                        etree.dump(stree)
        excludednodes += mdnodes
        cleantokennodelist = [
            n for n in cleantokennodelist if n not in excludednodes]
        resultnodelist += mdnodes

    # remove unknown words if open class
    unknown_words = [n for n in cleantokennodelist if getattval(n, 'pt') in openclasspts
                     and not (asta_recognised_wordnode(n))]
    resultnodelist += unknown_words
    cleantokennodelist = [
        n for n in cleantokennodelist if n not in unknown_words]

    # ASTA sec 6.3 p. 11
    # remove ja nee nou
    # janeenoulist = findjaneenou(cleantokennodelist)

    janeenoulist = nodesfindjaneenou(cleantokennodelist)
    resultnodelist += janeenoulist
    cleantokennodelist = [
        n for n in cleantokennodelist if n not in janeenoulist]

    # remove false starts maybe word + nee / of nee / eh word; of w of pos1 w of pos1
    # remove of nee

    # remove tsw incl goh och hé oke
    tswnodes = [n for n in cleantokennodelist if getattval(n, 'pt') == 'tsw']
    resultnodelist += tswnodes
    cleantokennodelist = [n for n in cleantokennodelist if n not in tswnodes]

    # remove other filled pauses
    fpnodes = [n for n in cleantokennodelist if
               getattval(n, 'lemma') in filledpauseslexicon]
    resultnodelist += fpnodes
    cleantokennodelist = [n for n in cleantokennodelist if n not in fpnodes]

    # simple duplicates
    dupnodelist, dupinfo = find_simpleduplicates2(cleantokennodelist)
    resultnodelist += dupnodelist
    alldupinfo = alldupinfo.merge(dupinfo)
    cleantokennodelist = [
        n for n in cleantokennodelist if n not in dupnodelist]

    # for debugging
    # print(showtns(cleantokennodelist))
    dupnodelist, dupinfo = find_duplicates2(cleantokennodelist)
    resultnodelist += dupnodelist
    alldupinfo = alldupinfo.merge(dupinfo)
    cleantokennodelist = [
        n for n in cleantokennodelist if n not in dupnodelist]

    # find prefix herhalingen >= 50%
    def cond(x, y):
        return len(cleanwordofnort(x)) / len(cleanwordofnort(y)) > 0.5

    prefixnodes, dupinfo = getprefixwords2(cleantokennodelist, cond)
    resultnodelist += prefixnodes
    alldupinfo = alldupinfo.merge(dupinfo)
    cleantokennodelist = [
        n for n in cleantokennodelist if n not in prefixnodes]

    # find unknown words that are a substring of their successor
    substringnodes, dupinfo = find_substringduplicates2(cleantokennodelist)
    alldupinfo = alldupinfo.merge(dupinfo)
    cleantokennodelist = [
        n for n in cleantokennodelist if n not in prefixnodes]

    # corrections = findcorrections(cleantokennodelist)
    # if corrections != []:
    #    cleanwordlist = [getattval(n, 'word') for n in cleantokennodelist]
    #    print(space.join(cleanwordlist), file=testfile)
    # for (w, corr) in corrections:
    #    print('--', getattval(w, 'word'), getattval(corr, 'word'), file=testfile)

    # remove dus als stopwoordje

    # remove words that consist of consonants only
    resultnodelist = [n for n in resultnodelist if not (
        all_lower_consonantsnode(n))]

    # remove words in incomplete sentences
    isws = incompletetreeleaves(stree)
    pureisws = [n for n in isws if n in cleantokennodelist]
    resultnodelist += pureisws
    alldupinfo.icsws = pureisws
    cleantokenlist = [n for n in cleantokennodelist if n not in pureisws]

    return resultnodelist, alldupinfo


def getrepeatedtokens(tokenlist, repeatingtokens):
    '''

    :param tokenlist:
    :param repeatingtokens: list of tokens that are repeating a token in tokenlist
    :return: dictionary of repeatingtoken: repeatedtoken pair
    '''
    repeatedtokens = {}
    ltokenlist = len(tokenlist)
    for i in range(ltokenlist):
        if tokenlist[i] in repeatingtokens:
            repeatedtokens[tokenlist[i]] = tokenlist[i + 1]
    return repeatedtokens


def cleanwordofnort(token):
    word = getword(token)
    result = cleanwordof(word)
    return result


def cleanwordof(word):
    lcword = word.lower()
    return lcword


def isnortprefixof(node1, node2):
    w1 = getword(node1)
    cw1 = cleanwordof(w1)
    w2 = getword(node2)
    cw2 = cleanwordof(w2)
    result = isprefixof(cw1, cw2)
    return result


def isprefixof(cw1, cw2):
    ncw1 = normalisestring(cw1)
    ncw2 = normalisestring(cw2)
    result = ncw1 != ncw2 and ncw2.startswith(ncw1)
    return result


def getprefixwords(wlist, cond):
    result, _ = getprefixwords2(wlist, cond)
    return result


def getprefixwords2(wlist: List[Nort],
                    cond: Callable[[Nort, Nort], bool]) \
        -> Tuple[List[Nort], DupInfo]:
    '''
    The function *getprefixwords2* finds nodes with words that are a prefix of the word
    of the successor node, and it creates a DupInfo object that contains a dictionary
    with <position prefixword, position successor word> items.

    '''
    resultlist = []
    dupmapping = dict()
    lwlist = len(wlist) - 1
    tokenctr = lwlist
    while tokenctr > 0:
        repctr = tokenctr - 1
        while repctr >= 0 and isnortprefixof(wlist[repctr], wlist[tokenctr]):
            if cond(wlist[repctr], wlist[tokenctr]):
                resultlist.append(wlist[repctr])
                reppos = getposition(wlist[repctr])
                tokenpos = getposition(wlist[tokenctr])
                dupmapping[reppos] = tokenpos
            repctr -= 1
        tokenctr = repctr
    dupinfo = DupInfo(dict(), dupmapping)
    return resultlist, dupinfo


def newgetprefixwords2(wlist, cond):
    resultlist = []
    dupmapping = dict()
    lwlist = len(wlist) - 1
    tokenctr = lwlist
    while tokenctr > 0:
        repctr = tokenctr - 1
        while repctr >= 0:
            wr = wlist[repctr]
            wt = wlist[tokenctr]

            ok = isnortprefixof(wlist[repctr], wlist[tokenctr])
            # @@@hier @@
            if cond(wlist[repctr], wlist[tokenctr]):
                resultlist.append(wlist[repctr])
                reppos = getposition(wlist[repctr])
                tokenpos = getposition(wlist[tokenctr])
                dupmapping[reppos] = tokenpos
            repctr -= 1
        tokenctr = repctr
    dupinfo = DupInfo(dict(), dupmapping)
    return resultlist, dupinfo


def isnamenort(node):
    theword = getword(node)
    result = theword[0].lower() != theword[0]
    return result


compoundxpath = './/node[@his="compound"]'
wordxpath = './/node[@pt and @pt!="let"]'


def neologisme(stree):
    results = []
    thecompounds = stree.xpath(compoundxpath)
    unknowncompounds = [c for c in thecompounds if
                        getattval(c, 'word') not in compounds.compounds]

    results += unknowncompounds

    # exclude filledpauses, exclude names, misspellings, deviant pronunciations, ......
    allwordnodes = stree.xpath(wordxpath)
    wordnodes = [wn for wn in allwordnodes if
                 len(getattval(wn, 'word')) > 5 and (not isnamenort(wn))]
    unknownwordnodes = [wn for wn in wordnodes if
                        not informlexicon(getattval(wn, 'word').lower())]

    results += unknownwordnodes

    return results


def getunwantedtokens(nortlist: List[Nort]) -> List[Nort]:
    '''
    The function *getunwantedtokens* returns nodes for tokens that are to be discarded
    for sample size as defined in the constant *unwantedtokenlist*

       * .. autodata:: sastadev.dedup::unwantedtokenlist

    '''
    results = []
    for nort in nortlist:
        nortword = getword(nort)
        if nortword in unwantedtokenlist:
            results.append(nort)
    return results


def samplesize(stree: SynTree) -> List[SynTree]:
    '''
    The function *samplesize* yields the tokens to be excluded from the samplesize. It does so by applying the function
    *samplesize2* and ignoring the DupInfo object that is returned in the tuple.

    .. autofunction:: sastadev.dedup::samplesize2

    '''
    result, _ = samplesize2(stree)
    return result


def samplesize2(stree: SynTree) -> Tuple[List[SynTree], DupInfo]:
    '''
    The function *samplesize2* yields the tokens to be excluded from the samplesize
    (based on ASTA4 eVersie sec 3, p. 7-8)
    plus a DupInfo object containing a duplicate mapping with items word in pos x is a
    repeat of the     word in position y.

    It maintains two variables for lists of nodes for tokens:

    * **tokennodelist**: the list of nodes for tokens that should be kept, (in their
    original  order), initially all tokens from the yield of *stree*
    * **resultlist**: a list of nodes that should be excluded

      **Remark** there is also a variable *excludednodes*, whose function is not fully
    clear. it might be redundant

    * The function first adds nodes to the *resultlist* that have been found by the *reduce* function in the correction module and that are represented in the metadata.
    * It next adds nodes for symbols that should be discarded. It obtains these nodes via the function *getunwantedtokens*

        * .. autofunction:: sastadev.dedup::getunwantedtokens


    * It adds nodes for interjections and filledpauses to the resultlist via the function *getfilledpauses*

        * .. autofunction:: sastadev.dedup::getfilledpauses

    * It adds duplicates of the words *ja*, *nee*, *nou*
    * It adds short repetitions in the tokenlist with *ja*, *nee*, *nou* removed by applying the function *getprefixwords2*

        * .. autofunction:: sastadev.dedup::getprefixwords2

    '''

    resultlist = []
    alldupinfo = DupInfo()
    # get the token nodes in sequence
    originaltokennodelist = getnodeyield(stree)
    tokennodelist = originaltokennodelist
    excludednodes = []
    # hitprint(tokennodelist)

    # add results that have been found earlier by reduce in correction and that are now in the metadata
    # and exclude these nodes for further processing
    mdnodes = []
    mlumds = stree.xpath(xmetaxpath)
    for mlumd in mlumds:
        if 'value' in mlumd.attrib and mlumd.attrib['value'] in samplesizemdvalues:
            tokenbeginstr = mlumd.attrib['annotatedposlist']
            tokenbegins = string2list(tokenbeginstr)
            for tokenbegin in tokenbegins:
                nodexpath = './/node[(@pt or @pos) and @begin="{}"]'.format(tokenbegin)
                newnode = find1(stree, nodexpath)
                if newnode is not None:
                    mdnodes.append(newnode)
                else:
                    xsid = getxsid(stree)
                    sentence = getsentence(stree)
                    settings.LOGGER.error(
                        f'Metadata node not found in tree: md.begin={tokenbegin}\n{xsid}: {sentence}')
                    # etree.dump(stree)
    excludednodes += mdnodes
    tokennodelist = [n for n in tokennodelist if n not in excludednodes]
    resultlist += mdnodes

    # throw out unwanted symbols - -- # etc
    unwantedtokens = getunwantedtokens(tokennodelist)
    resultlist += unwantedtokens
    tokennodelist = [n for n in tokennodelist if n not in unwantedtokens]

    # find filledpauses and interjections
    filledpausenodes = getfilledpauses(tokennodelist)
    resultlist += filledpausenodes
    tokennodelist = [n for n in tokennodelist if n not in filledpausenodes]

    # find duplicatenode repetitions of ja, nee, nou
    janeenouduplicatenodes, dupinfo = find_janeenouduplicates2(tokennodelist)
    resultlist += janeenouduplicatenodes
    tokennodelist = [
        n for n in tokennodelist if n not in janeenouduplicatenodes]
    alldupinfo = alldupinfo.merge(dupinfo)

    # temporarily remove ja nee nou to get the right short repetitions
    janeenoutokens = findjaneenou(tokennodelist)
    temptokennodelist = [n for n in tokennodelist if n not in janeenoutokens]

    # find prefix herhalingen < 50%
    def cond(x, y):
        return len(cleanwordofnort(x)) / len(cleanwordofnort(y)) <= 0.5

    prefixnodes, dupinfo = getprefixwords2(temptokennodelist, cond)
    resultlist += prefixnodes
    tokennodelist = [n for n in tokennodelist if n not in prefixnodes]
    alldupinfo = alldupinfo.merge(dupinfo)

    return resultlist, alldupinfo
