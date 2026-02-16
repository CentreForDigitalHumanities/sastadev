from collections import Counter
from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from sastadev.allresults import AllResults, ResultsKey, mkresultskey
from sastadev.lexicon import getwordinfo, getwordposinfo
from sastadev.sastatypes import Position, SynTree, UttId
from sastadev.stringfunctions import getallrealwords, realwordstring
from sastadev.treebankfunctions import getattval, getnodeyield

lpad = 3
zero = '0'
astamaxwordcount = 300

excluded_lemmas = ['gevallen', 'gewinnen']

nounqid = 'A021'
lexqid = 'A018'
samplesizeqid = 'A045'
mluxqid = 'A029'
pvqid = 'A024'
delpvqid = 'A009'
subpvqid = 'A032'
kqid = 'A013'
mqid = 'A020'
tijdfoutpvqid = 'A041'
nounlemmaqid = 'A046'
formqid = 'A047'
verblemmaqid = 'A049'

nounreskey = mkresultskey(nounqid)
lexreskey = mkresultskey(lexqid)

samplesizereskey = mkresultskey(samplesizeqid)
mluxreskey = mkresultskey(mluxqid)

pvreskey = mkresultskey(pvqid)
delpvreskey = mkresultskey(delpvqid)
subpvreskey = mkresultskey(subpvqid)
tijdfoutpvreskey = mkresultskey(tijdfoutpvqid)
kreskey = mkresultskey(kqid)
mreskey = mkresultskey(mqid)
formreskey = mkresultskey(formqid)

specialform = 'Special Form'
errormarking = 'Error Marking'

#: The variable (constant) *mdnamemdxpathtemplate* is an Xpath template to find
#: metadata (xmeta) with  name=*mdname* and value=*mdvalue*
mdnamemdxpathtemplate = """.//xmeta[@name="{mdname}" and @value="{mdvalue}"]"""

mdnameonlyxpathtemplate = """.//xmeta[@name="{mdname}"]"""
ptposxpathtemplate = './/node[@pt and @begin="{position}"]'


def mdbasedquery(stree: SynTree, mdname: str, mdvalue: str) -> List[SynTree]:
    '''
    The function *mdbasedquery* searches for metadata in *stree* with name = *mdname*
    and value = *mdvalue*. It then obtains the position of the node to which the
    metadata apply, and next finds all nodes with that position as value for its *begin* attribute.
    '''
    mdnamemdxpath = mdnameonlyxpathtemplate.format(
        mdname=mdname)
    mdnamemds = stree.xpath(mdnamemdxpath)
    results = []
    for mdnamemd in mdnamemds:
        thevaluelist = eval(mdnamemd.attrib['value'])
        if mdvalue in thevaluelist:
            annotatedposstr = mdnamemd.attrib['annotatedposlist']
            if annotatedposstr != '':
                mdbeginval = annotatedposstr[1:-1]
                ptposxpath = ptposxpathtemplate.format(position=mdbeginval)
                newresults = stree.xpath(ptposxpath)
                results += newresults

    return results


def neologisme(stree: SynTree) -> List[SynTree]:
    '''
    The function *neologisme* identifies the nodes for which the CHAT error marking "[*
    n]" or the special form "@n" applies. It uses the function *mdbasedquery* to
    achieve this.

    .. autofunction:: sastadev.ASTApostfunctions::mdbasedquery

    '''
    results1 = mdbasedquery(stree, errormarking, 'n')
    results2 = mdbasedquery(stree, specialform, '@n')
    results = results1 + results2
    return results


def sempar(stree: SynTree) -> List[SynTree]:
    '''
    The function *sempar* identifies the nodes for which the CHAT error marking "[*
    s]"  applies. It uses the function *mdbasedquery* to achieve this.

    .. autofunction:: sastadev.ASTApostfunctions::mdbasedquery


    '''
    results = mdbasedquery(stree, errormarking, 's')
    return results


def phonpar(stree: SynTree) -> List[SynTree]:
    '''
    The function *phonpar* identifies the nodes for which the CHAT error marking "[*
    p]"  applies. It uses the function *mdbasedquery* to achieve this.

    .. autofunction:: sastadev.ASTApostfunctions::mdbasedquery

    '''
    results = mdbasedquery(stree, errormarking, 'p')
    return results


def sumctr(ctr):
    result = sum(ctr.values())
    return result


def wordcountperutt(allresults):
    lemmas = getalllemmas(allresults)
    wordcounts = {uttid: sum(ctr.values()) for uttid, ctr in lemmas.items()}
    ignorewordcounts = deepcopy(
        allresults.coreresults[
            samplesizereskey]) if samplesizereskey in allresults.coreresults else Counter()  # samplesize
    ignorewordcounts += allresults.coreresults[
        mluxreskey] if mluxreskey in allresults.coreresults else Counter()  # mlux
    # ignorewordcounts += allresults.coreresults['A050'] if 'A050' in allresults.coreresults else Counter() # echolalie covered by mlux
    result = {}
    for uttid in wordcounts:
        tosubtract = ignorewordcounts[uttid] if uttid in ignorewordcounts else 0
        result[uttid] = wordcounts[uttid] - tosubtract
    # remove uttids which have 0 words
    result = {uttid: ctr for uttid, ctr in result.items() if ctr != 0}
    return result


def getignorewordcount(allresults, uttid):
    result = 0
    if samplesizereskey in allresults.coreresults:
        if uttid in allresults.coreresults[samplesizereskey]:
            result = allresults.coreresults[samplesizereskey][uttid]
    return result


def getastamaxsamplesizeuttidsandcutoff(allresults: AllResults) -> Tuple[List[UttId], int, Position]:
    cutoffpoint = None
    words = getallrealwords(allresults)
    cumwordcount = 0
    wordcounts: Dict[UttId, Tuple[int, int, int]] = {}
    uttidlist = []
    for uttid in allresults.allutts:
        basewordcount = sum(words[uttid].values())
        ignorewordcount = getignorewordcount(allresults, uttid)
        wordcount = basewordcount - ignorewordcount
        wordcounts[uttid] = (basewordcount, ignorewordcount, wordcount)
        uttidlist.append(uttid)
        if cumwordcount + wordcount <= astamaxwordcount:
            cumwordcount += wordcount
        else:
            diff = astamaxwordcount - cumwordcount
            cumwordcount = astamaxwordcount
            cutoffpoint = getcutoffpoint(allresults, uttid, diff)
            break
    result = (uttidlist, cumwordcount, cutoffpoint)
    return result


def getcutoffpoint(allresults: AllResults, uttid: UttId, diff: int) -> int:
    theutt = allresults.allutts[uttid]
    final = diff
    for i, w in enumerate(theutt):
        if (uttid, i + 1) in allresults.exactresults[samplesizereskey]:
            final += 1
        if i + 1 == final:
            break
    return final


def getignorewordcount(allresults, uttid):
    result = 0
    if samplesizereskey in allresults.coreresults:
        if uttid in allresults.coreresults[samplesizereskey]:
            result = allresults.coreresults[samplesizereskey][uttid]
    return result


def getastamaxsamplesizeuttidsandcutoff(allresults: AllResults) -> Tuple[List[UttId], int, Position]:
    cutoffpoint = None
    words = getallrealwords(allresults)
    cumwordcount = 0
    wordcounts: Dict[UttId, Tuple[int, int, int]] = {}
    uttidlist = []
    for uttid in allresults.allutts:
        basewordcount = sum(words[uttid].values())
        ignorewordcount = getignorewordcount(allresults, uttid)
        wordcount = basewordcount - ignorewordcount
        wordcounts[uttid] = (basewordcount, ignorewordcount, wordcount)
        uttidlist.append(uttid)
        if cumwordcount + wordcount <= astamaxwordcount:
            cumwordcount += wordcount
        else:
            diff = astamaxwordcount - cumwordcount
            cumwordcount = astamaxwordcount
            cutoffpoint = getcutoffpoint(allresults, uttid, diff)
            break
    result = (uttidlist, cumwordcount, cutoffpoint)
    return result


def getcutoffpoint(allresults: AllResults, uttid: UttId, diff: int) -> int:
    theutt = allresults.allutts[uttid]
    final = diff
    for i, w in enumerate(theutt):
        if samplesizereskey in allresults.exactresults and \
            (uttid, i + 1) in allresults.exactresults[samplesizereskey]:
            final += 1
        if i + 1 == final:
            break
    return final

def finietheidsindex(allresults, _):
    allpvs = allresults.coreresults[
        pvreskey] if pvreskey in allresults.coreresults else Counter()
    subpvs = allresults.coreresults[
        subpvreskey] if subpvreskey in allresults.coreresults else Counter()
    delpvs = allresults.coreresults[
        delpvreskey] if delpvreskey in allresults.coreresults else Counter()
    tijdfoutpvs = allresults.coreresults[
        tijdfoutpvreskey] if tijdfoutpvreskey in allresults.coreresults else Counter()
    foutepvs = subpvs + delpvs + tijdfoutpvs
    allpvcount = sumctr(allpvs)
    foutepvcount = sumctr(foutepvs)
    okpvcount = allpvcount - foutepvcount
    if allpvcount == 0:
        result = 0
    else:
        result = okpvcount / allpvcount
    return result


def countwordsandcutoff(allresults, _):
    # @@to be adapted
    result = (None, 0)
    if formreskey in allresults.postresults:
        paddedlist = []
        for key, val in allresults.postresults[formreskey].items():
            paddedkey = key.rjust(lpad, zero)
            paddedlist.append((paddedkey, val))
        sortedlist = sorted(paddedlist)
        wc = 0
        for key, val in sortedlist:
            if wc + val > astamaxwordcount:
                result = (key, wc)
                break
            else:
                wc += val
                result = (None, wc)
    return result


def KMcount(allresults, _):
    Kcount = sumctr(
        allresults.coreresults[kreskey]) if kreskey in allresults.coreresults else 0
    Mcount = sumctr(
        allresults.coreresults[mqid]) if mqid in allresults.coreresults else 0
    result = Kcount + Mcount
    return result


# def getlemmas(allresults, _):
#    result = getcondlemmas(allresults, _, lambda reskey: reskey in [nounreskey, lexreskey])
#    return result


def getnounlemmas(allresults, _):
    '''
    The function *getnounlemmas* uses the function *getposlemmas* applied to
    *allresults* and the query identifier for nouns to obtain the lemmas
    for nouns.

    .. autofunction:: sastadev.ASTApostfunctions::getposlemmas

    '''
    result = getposlemmas(allresults, nounreskey)
    return result


def getlexlemmas(allresults, _):
    '''
    The function *getlexlemmas* uses the function *getposlemmas* applied to
    *allresults* and the query identifier for lexical verbs to obtain the lemmas
    for lexical verbs.

    .. autofunction:: sastadev.ASTApostfunctions::getposlemmas
    '''
    result = getposlemmas(allresults, lexreskey)
    return result


def realword(node):
    result = getattval(node, 'pt') not in ['let']
    return result


def getalllemmas(allresults):
    result = {}
    if allresults.annotationinput:
        for uttid in allresults.allutts:
            lemmas = [bgetlemma(w) for w in allresults.allutts[uttid] if
                      realwordstring(w)]
            result[uttid] = Counter(lemmas)
    else:
        for uttid, syntree in allresults.analysedtrees:
            # uttid = getuttid(syntree)
            lemmas = [getattval(node, 'lemma') for node in getnodeyield(syntree) if
                      realword(node)]
            result[uttid] = Counter(lemmas)
    return result


def getposfromqid(qid):
    if qid == 'A021':
        pos = 'n'
    elif qid == 'A018':
        pos = 'ww'
    else:
        pos = None
    return pos


def getposlemmas(allresults: AllResults, posreskey: ResultsKey) -> List[Tuple[str, UttId]]:
    '''
    The function *getposlemmas* obtains the lemmas from *allresults* that have been
    found by a query with identifier *posreskey*.

    The lemma is obtained from the parse tree if there is one, otherwise (in case the
    input was an annotation form) from the lexicon (CELEX).
    '''
    result = Counter()
    if allresults.annotationinput:
        for (uttid, position) in allresults.exactresults[posreskey]:
            word = allresults.allutts[uttid][position - 1]
            posqid = posreskey[0]
            pos = getposfromqid(posqid)
            lemma = bgetlemma(word, pos)
            result.update([(lemma, uttid)])
    else:
        allmatches = allresults.allmatches
        for el in allmatches:
            (reskey, uttid) = el
            if reskey == posreskey:
                for amatch in allmatches[el]:
                    # theword = normalizedword(amatch[0])
                    theword = getattval(amatch[0], 'lemma')
                    result.update([(theword, uttid)])
    return result


def bgetlemma(word: str, pos: Optional[str] = None):
    if pos is None:
        wordinfos = getwordinfo(word)
        if wordinfos == []:
            lemma = word
        else:
            filteredwordinfos = [
                wi for wi in wordinfos if wi[3] not in excluded_lemmas]
            if filteredwordinfos == []:
                lemma = wordinfos[0][3]
            else:
                lemma = filteredwordinfos[0][3]
    else:
        wordinfos = getwordposinfo(word, pos)
        if wordinfos == []:
            lemma = word
        else:
            filteredwordinfos = [
                wi for wi in wordinfos if wi[3] not in excluded_lemmas]
            if filteredwordinfos == []:
                lemma = wordinfos[0][3]
            else:
                lemma = filteredwordinfos[0][3]
    return lemma
