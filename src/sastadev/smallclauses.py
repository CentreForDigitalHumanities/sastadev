'''
The module *smallclauses* deals with *small clauses*, i.e. utterances with a
predication but no finite verb. Examples include:

* die dicht
* schoenen aan
* ladder hier
* ik varken
* nou Marije nat
* traktor niet hier
* mama even drinken
* nee dees wel
* ikke dees pakke
* ik naar omie

Alpino cannot analyse such utterances in a proper manner. For example,
it analyses *schoenen aan* as a sequence of two discourse part, one a noun, the other an
adjective.

For this reason this module inserts an appropriate finite verb into these utterances. This modified utterance with
a finite verb can be analysed by Alpino. In the resulting parse, SASTA removes the verb
again and the resulting parse tree is subjected to the queries for analysis.

For example, by inserting the finite verb *moeten* in the utterance *schoenen aan*,
resulting in *schoenen moeten aan*, *schoenen* can be analysed as a subject noun and *aan* as predicative adjective,
and the whole utterance as an instance of TARSP *OndVC*.

The small clause utterances are often very short, and we analysed utterances with 2
and 3 "real" words,  "real" in the sense that we excluded interjections, filled pauses,
interpunction signs, CHAT codes such as *xxx*, etc.

The different subcases are dealt with by the function *smallclauses*:

.. autofunction:: sastadev.smallclauses::smallclauses

'''
import copy
from typing import List

from sastadev.conf import settings
from sastadev.dedup import filledpauseslexicon
from sastadev.lexicon import getwordinfo, known_word, tswnouns
from sastadev.metadata import (SASTA, Meta, bpl_delete, bpl_none,
                               defaultpenalty, insertion,
                               insertiontokenmapping)
from sastadev.metadata import modifypenalty as mp
from sastadev.metadata import smallclause, tokenmapping
from sastadev.namepartlexicon import namepart_isa_namepart
from sastadev.sastatoken import Token
from sastadev.sastatypes import SynTree
from sastadev.tokenmd import TokenListMD
from sastadev.top3000 import (genlexicon, intransitive, isanimate, ishuman,
                              pseudotr, transitive)
from sastadev.treebankfunctions import (getattval, getnodeyield, getsentence, gettokenpos_str, inflate_step,
                                      trueclausecats)

space = ' '
biglocvzs = ['achter', 'beneden', 'binnen', 'boven', 'bovenop', 'buiten', 'dichtbij']
#surenouns = ['mama', 'papa'] replaced by tswnouns from lexicon
longvowels = ['a', 'é', 'i', 'o', 'u', 'y']
vowels = ['a', 'e', 'i', 'o', 'u']

uniquelynominativeperspros = ['ik', 'jij', 'hij', 'zij', 'wij', 'ikke', "'k", "k", "ie", "we"]

topicdropmeta = Meta('Topic drop', 'Topic drop', cat='Grammar', subcat='Syntax', source='SASTA', penalty=0)
nominalexceptions = {'weg'}   # words that are nouns but also and more plausibly of a different pt, e.g. bw

def makegen(lemma):
    if lemma is None or len(lemma) < 2:
        result = None
    elif lemma[-1] in ['s', 'z', 'x']:
        result = lemma + "'"
    elif lemma[-2:] in ['ij']:
        result = lemma + 's'
    elif lemma[-2] in vowels and lemma[-1] in vowels:
        result = lemma + 's'
    elif lemma[-1] in longvowels:
        result = lemma + "'s"
    else:
        result = lemma + 's'
    return result


def realword(node):
    result = True
    result = result and getattval(node, 'pt') not in ['tsw', 'let']
    result = result and getattval(node, 'lemma') not in ['xx', 'xxx', 'yyy', 'www', 'hè']
    result = result and getattval(node, 'lemma') not in filledpauseslexicon
    result = result or lemma(node) in tswnouns

    return result


def hasgenitive(node):
    lemma = getattval(node, 'lemma')
    nodept = pt(node)
    if nodept not in ['n', 'vnw']:
        nodept = 'n'
    result = (lemma, nodept) in genlexicon and 'yes' in genlexicon[(lemma, nodept)]
    result = result or namepart_isa_namepart(lemma)
    return result


def aanwvnw(node):
    result = getattval(node, 'pt') == 'vnw' and getattval(node, 'vwtype') == 'aanw' and not rpronoun(node)
    return result


def n(node):
    result = getattval(node, 'pt') == 'n'
    return result


def getal(node):
    result = getattval(node, 'getal')
    return result


def pt(node):
    result = getattval(node, 'pt')
    return result


def bg(node):
    result = int(getattval(node, 'begin'))
    return result


def tw(node):
    result = getattval(node, 'pt') == 'tw'
    return result


def word(node):
    result = getattval(node, 'word')
    return result


def adj(node):
    result = getattval(node, 'pt') == 'adj'
    return result


def perspro(node):
    pt = getattval(node, 'pt')
    vwtype = getattval(node, 'vwtype')
    result = pt == 'vnw' and vwtype == 'pers'
    return result


def nomperspro(node):
    lemma = getattval(node, 'lemma')
    result = perspro(node) and lemma in uniquelynominativeperspros
    return result


def inf(node):
    result = getattval(node, 'pt') == 'ww' and getattval(node, 'wvorm') == 'inf'
    return result

def pastpart(node):
    result = getattval(node, 'pt') == 'ww' and getattval(node, 'wvorm') == 'vd'
    return result


def rpronoun(node):
    result = getattval(node, 'pt') == 'vnw' and \
        getattval(node, 'lemma') in ['er', 'hier', 'daar', 'ergens', 'overal', 'nergens', 'waar']
    return result


def bw(node):
    nodept = getattval(node, 'pt')
    result = nodept == 'bw' or rpronoun(node)
    result = result and getattval(node, 'lemma') != 'er'
    return result


def ww(node):
    result = getattval(node, 'pt') == 'ww'
    return result


def lemma(node):
    result = getattval(node, 'lemma')
    return result


def predadv(node):
    result = locadv(node)
    result = result or (bw(node) and lemma(node) in ['niet', 'mee', 'weg'])
    return result


def vz(node):
    result = getattval(node, 'pt') == 'vz'
    return result


def locadv(node):
    result = getattval(node, 'pt') in ['bw', 'vz']
    frame = getattval(node, 'frame')
    result = result and ('loc' in frame or 'er_adverb' in frame)
    result = result or (rpronoun(node) and getattval(node, 'lemma') != 'er')   # in samll clauses predicates are no clitics
    return result


def biglocvz(node):
    result = getattval(node, 'lemma') in biglocvzs
    return result


def istswnoun(node):
    result = getattval(node, 'lemma') in tswnouns
    return result

def tgwmv(node: SynTree) -> bool:
    result = getattval(node, 'pvtijd') == 'tgw' and getattval(node, 'pvagr') == 'mv'
    return result

def getleavestr(leaves):
    leaveseq = ['{}:{}:{}:{}'.format(getattval(leave, 'end'), getattval(leave, 'word'), getattval(leave, 'lemma'),
                                     getattval(leave, 'pt')) for leave
                in leaves]
    leavestr = space.join(leaveseq)
    return leavestr


def knownnoun(node):
    word = getattval(node, 'word')
    lemma = getattval(node, 'lemma')
    postag = pt(node)
    result = postag == 'n' and (known_word(word) or known_word(lemma))
    result = result or lemma in tswnouns
    return result


def nominal(node):
    result = pt(node) == 'n' or aanwvnw(node)
    return result

def issubstadj(node: SynTree) -> bool:
    pt = getattval(node, 'pt')
    positie = getattval(node, 'positie')
    result = pt == 'adj' and positie == 'vrij'
    return result

def mktoken(node, map):
    nodebegin = bg(node)
    nodeword = word(node)
    if nodebegin in map:
        nodepos = map[nodebegin]
    else:
        settings.LOGGER.error('missing begin in map {}'.format(nodebegin))
        nodepos = int(nodebegin)
    result = Token(nodeword, nodepos)
    return result


def mktokenlist(tokens, fpos, inserttokens):
    resultlist = [token for token in tokens if token.pos <= fpos] + \
        inserttokens + \
                 [token for token in tokens if token.pos > fpos]
    return resultlist


def oldmktokenlist(leaves, themap, fpos, inserttokens):
    resultlist = [mktoken(lv, themap) for lv in leaves if bg(lv) <= fpos] + \
        inserttokens + \
                 [mktoken(lv, themap) for lv in leaves if bg(lv) > fpos]
    return resultlist

def getaux(node: SynTree) -> str:
    pt = getattval(node, 'pt')
    frame =getattval(node, 'frame')
    if pt == 'adj':
        result = 'zijn'
    elif pt == 'ww':
        if frame.startswith('verb(zijn') or frame.startswith('verb(unacc'):
            result = 'zijn'
        elif frame.startswith('verb(hebben'):
            result = 'hebben'
        else:
            result = ''
    return result

def getauxform(aux: str, node:SynTree) -> str:
    persoon = getattval(node, 'persoon')
    getal = getattval(node, 'getal')
    if getal == 'mv':
        result = aux
    else:
        if persoon.startswith('1'):
            result = 'heb' if aux == 'hebben' else 'ben'
        elif persoon.startswith('2'):
            result = 'hebt' if aux == 'hebben' else 'bent'
        elif persoon.startswith('3'):
            result = 'heeft' if aux == 'hebben' else 'is'
        else:   # should never occur
            result = 'heeft' if aux == 'hebben' else 'is'
    return result

def mkinsertmeta(inserttokens, resultlist, penalty=defaultpenalty, cat=smallclause):
    insertposs = [token.pos + token.subpos for token in inserttokens]
    insertwordlist = [token.word for token in inserttokens]
    tokenmappinglist = [token.pos if token.subpos == 0 else None for token in resultlist]
    metadata1 = [Meta(insertion, [insertword], annotatedposlist=[insertpos],
                 annotatedwordlist=[], annotationposlist=[insertpos],
                 annotationwordlist=[insertword], cat=smallclause, source=SASTA, penalty=penalty,
                 backplacement=bpl_delete) for insertword, insertpos in zip(insertwordlist, insertposs)]
    meta2 = Meta(insertiontokenmapping, tokenmappinglist, cat=tokenmapping, source=SASTA, penalty=0,
                 backplacement=bpl_none)
    metadata = metadata1 + [meta2]
    return metadata

def isfirstsubject(first, second) -> bool:
    if intransitive(second):
        firstsubject = True
    elif transitive(second) and (ishuman(first) or nomperspro(first)):
        firstsubject = True
    elif pseudotr(second) and (ishuman(first) or isanimate(first) or nomperspro(first)):
        firstsubject = True
    else:
        firstsubject = False
    return firstsubject

def isditdat(node: SynTree) -> bool:
    lemma = getattval(node, 'lemma')
    result = lemma in {'dit', 'dat'}
    return result
def iscoord(node: SynTree) -> bool:
    pt = getattval(node, 'pt')
    conjtype = getattval(node, 'conjtype')
    result = pt == 'vg' and conjtype == 'neven'
    return result

def isnominalexception(node: SynTree) -> bool:
    result = getattval(node, 'lemma') in nominalexceptions
    return result

def ispropernoun(node: SynTree) -> bool:
    lemma = getattval(node, 'lemma')
    result = lemma[0].isupper() if lemma != "" else False
    return result

def canbeinfinitive(wrd: str) -> bool:
    wordinfos = getwordinfo(wrd)
    result = any([wordinfo[2] == 'i' for wordinfo in wordinfos])
    return result


def isonlypv(node: SynTree) -> bool:
    nodept = getattval(node, 'pt')
    nodewvorm = getattval(node, 'wvorm')
    result = nodept == 'ww' and nodewvorm == 'pv' and not tgwmv(node)
    return result

def iswhpronoun(node: SynTree) -> bool:
    nodelemma = getattval(node, 'lemma')
    result = nodelemma in ['wat', 'wie', 'waar', 'hoe', 'wanneer', 'waarom', 'welk'] or nodelemma.startswith('waar')
    return result

def containsaanhetinf(nodes: List[SynTree]) -> bool:
    lnodes = len(nodes)
    for i in range(lnodes - 2):
        lemma1 = getattval(nodes[i], 'lemma')
        lemma2 = getattval(nodes[i+1], 'lemma')
        pt3 = getattval(nodes[i+2], 'pt')
        wvorm3 = getattval(nodes[i+2], 'wvorm')
        if lemma1 == 'aan' and lemma2 == 'het' and pt3 == 'ww' and wvorm3 == 'inf':
            return True
    return False

def smallclauses(tokensmd: TokenListMD, tree: SynTree) -> List[TokenListMD]:
    '''

    :param tokensmd: list of tokens with metadata
    :param tree: the syntactic structure of the utterance
    :return: a possibly empty list of alternative TokenListMD objects

    The function *smallclauses* creates zero or more alternative TokenListMD
    objects by inserting an appropriate finite verb.

    "Appropriate"in this comtext means that it must fit in *syntactically* and
    *morphologically* in this context:

    * **syntactically** the verb must take the right complements
    * **morphologically** the verb form must agree with the subject

    SASTA usually inserts a verb that has few different inflectional forms, so that the
    agreement requirement is met in the easiest way. (e.g. *moeten* has only one form
    in present tense for singular (*moet*), and only one form for plural (*moeten*).

    The relevant cases from the available TARSP-examples have been inventoried,
    and some of the relevant cases have been implemented. The table below specifies which cases are currently covered.

    Cases covered so far:

    .. csv-table:: Small Clause Subcases covered
      :file: Documentation/smallclausetable.csv
      :widths: 16, 16, 16, 16, 16, 20
      :header-rows: 1


    '''
    resultlist = []
    leaves = getnodeyield(tree)
    sentence = getsentence(tree)
    reducedleaves = [leave for leave in leaves if realword(leave)]
    # no word that can only be a finite verb should be present
    if any([isonlypv(node) for node in reducedleaves]):
        return resultlist
    if reducedleaves != [] and iscoord(reducedleaves[0]):
        reducedleaves = reducedleaves[1:]
    allverbs = [leave for leave in reducedleaves if getattval(leave, 'pt') == 'ww']
    verbs = [leave for leave in allverbs if getattval(leave.getparent(), 'cat') not in trueclausecats]
    if len(allverbs) > 1:
        return resultlist
    if verbs != [] and not (len(reducedleaves) > 1 and len(reducedleaves) <= 5):
        return resultlist
    elif not(len(reducedleaves) > 1):
        return resultlist


    tokens = tokensmd.tokens
    treewords = [word(tokennode) for tokennode in leaves]
    tokenwords = [token.word for token in tokens if not token.skip]
    if treewords != tokenwords:
        settings.LOGGER.warning(
            'Token mismatch: {} v. {}'.format(treewords, tokenwords))
        return []
    reducedtokens = [token for token in tokens if not token.skip]
    themap = {bg(tokennode): token for (tokennode, token) in zip(leaves, reducedtokens)}
    if len(verbs) == 1:
        theverb = verbs[0]
        verbtoken = themap[bg(theverb)]
        if verbtoken.word == getattval(theverb, 'word'):
            theverbok = getattval(theverb, 'wvorm') != 'pv' or tgwmv(theverb)
        else:
            theverbok = canbeinfinitive(verbtoken.word)  # this is needed because the verb may have been changed, e..g by sva
        if not theverbok:
            return resultlist
    else:
        theverb = None



    metadata = copy.deepcopy(tokensmd.metadata)

    if len(reducedleaves) >= 2:
        first = reducedleaves[0]
        second = reducedleaves[1]
    if len(reducedleaves) >= 3:
        third = reducedleaves[2]

    if len(reducedleaves) == 2:
        if (aanwvnw(first) or knownnoun(first) or perspro(first)) and (predadv(second) or vz(second) or bw(second)):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                inserttokens = [Token('moet' if getal(first) != 'mv' else 'moeten', fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        #elif (aanwvnw(second) or knownnoun(second) or perspro(second) or tw(second)) and predadv(first):
        elif nomperspro(second) and predadv(first):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                inserttokens = [Token('moet' if getal(second) != 'mv' else 'moeten', fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif (aanwvnw(first) or knownnoun(first)) and adj(second):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                inserttokens = [Token('is' if getal(first) != 'mv' else 'zijn', fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif (aanwvnw(second) or knownnoun(second) or tw(second)) and biglocvz(first):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                inserttokens = [Token('is' if getal(first) != 'mv' else 'zijn', fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif knownnoun(first) and knownnoun(second)  and not (lemma(first) == lemma(second)):
            if ishuman(second):
                insertform = 'zijn' if getal(first) == 'mv' else 'is'
            else:
                insertform = 'willen' if getal(first) == 'mv' else 'wil'
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                inserttokens = [Token(insertform, fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif (aanwvnw(first) or knownnoun(first) or istswnoun(first) or perspro(first)) and inf(second):
            firstsubject = isfirstsubject(first, second)
            if firstsubject:
                bgfirst = bg(first)
                if bgfirst in themap:
                    fpos = themap[bg(first)].pos
                    inserttokens = [Token('wil' if getal(first) != 'mv' else 'willen', fpos, subpos=5)]
                    resultlist = mktokenlist(tokens, fpos, inserttokens)
                    metadata += mkinsertmeta(inserttokens, resultlist)
                else:
                    settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                          f'tokens={str(reducedtokens)}; No insertion done')
            else:
                bgfirst = bg(first)
                if bgfirst in themap:
                    fpos = themap[bg(first)].pos - inflate_step
                    inserttokens = [Token('ik', fpos, subpos=5), Token('wil', fpos, subpos=8)]
                    resultlist = mktokenlist(tokens, fpos, inserttokens)
                    metadata += mkinsertmeta(inserttokens, resultlist)
                else:
                    settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                          f'tokens={str(reducedtokens)}; No insertion done')
        elif (aanwvnw(first) or knownnoun(first) or istswnoun(first) or perspro(first)) and pastpart(second):  # ik gedaan
            firstsubject = isfirstsubject(first, second)
            if firstsubject: ## otherwise the structure ppart[obj1 hd/ww] is correct to get VCW as tarsp code
                bgfirst = bg(first)
                if bgfirst in themap:
                    fpos = themap[bg(first)].pos
                    verbtoinsert = getaux(second)
                    verbform = getauxform(verbtoinsert, first)
                    if verbtoinsert in ['hebben', 'zijn']:
                        if transitive(second):
                            inserttokens = [Token('dat', 3), Token(verbform, 5)]
                            resultlist = mktokenlist(tokens, 0, inserttokens)
                            metadata += [topicdropmeta]
                        else:
                            inserttokens = [Token(verbform, fpos, subpos=5)]
                            resultlist = mktokenlist(tokens, fpos, inserttokens)
                        metadata += mkinsertmeta(inserttokens, resultlist, penalty=mp(50))
                    # add metadata for topic drop
                else:
                    settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                          f'tokens={str(reducedtokens)}; No insertion done')
        elif not nominal(first) and not ww(first) and inf(second):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bgfirst].pos - inflate_step
                inserttokens = [Token('ik', fpos, subpos=5), Token('wil', fpos, subpos=8)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif (isditdat(first) or nomperspro(first)) and \
                (nominal(second) or  issubstadj(second)) and \
                not isnominalexception(second):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                insertform = 'waren' if getal(first) == 'mv' else 'was'
                inserttokens = [Token(insertform, fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
    elif len(reducedleaves) > 2:
        if theverb is not None and (nomperspro(first) or (knownnoun(first) and intransitive(theverb))) :
            # jij zelf doen         # DLD11,19
            # poppie netjes zitten # TD01, 40
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                insertform = 'moeten' if getal(first) == 'mv' else 'moet'
                inserttokens = [Token(insertform, fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif any([getattval(leave, 'wvorm') == 'inf' for leave in reducedleaves]) and getattval(first, 'pt') == 'bw' \
            and nomperspro(second):   # nu jij 't doen. DLD16, 6
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                insertform = 'moeten' if getal(second) == 'mv' else 'moet'
                inserttokens = [Token(insertform, fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif theverb is not None and not nomperspro(first) and canbeinfinitive(getattval(theverb, 'word')) and \
                not any([getattval(n, 'lemma') in ['moe', 'moeten'] for n in reducedleaves]) and \
                not iswhpronoun(first) and not containsaanhetinf(reducedleaves):
            # die daarin doen tarsp_03, 2
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos - inflate_step
                inserttokens = [Token('jij', fpos, subpos=5), Token('moet', fpos, subpos=8)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif theverb is None and knownnoun(first) and pt(second) == 'bw' and knownnoun(third):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                if ishuman(second):
                    insertform = 'zijn' if getal(first) == 'mv' else 'is'
                else:
                    insertform = 'willen' if getal(first) == 'mv' else 'wil'
                inserttokens = [Token(insertform, fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif theverb is None and (knownnoun(first) or aanwvnw(first)) and predadv(second):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                insertform = 'moeten' if getal(first) == 'mv' else 'moet'
                inserttokens = [Token(insertform, fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')
        elif theverb is None and (knownnoun(first) or aanwvnw(first)) and pt(second) == 'bw' and predadv(third):
            bgfirst = bg(first)
            if bgfirst in themap:
                fpos = themap[bg(first)].pos
                insertform = 'moeten' if getal(first) == 'mv' else 'moet'
                inserttokens = [Token(insertform, fpos, subpos=5)]
                resultlist = mktokenlist(tokens, fpos, inserttokens)
                metadata += mkinsertmeta(inserttokens, resultlist)
            else:
                settings.LOGGER.error(f'No entry for {bgfirst} in themap; leaves={gettokenpos_str(tree)}, '
                                      f'tokens={str(reducedtokens)}; No insertion done')



    if resultlist == []:
        result = []
    else:
        result = [TokenListMD(resultlist, metadata)]
    return result
