from collections import defaultdict
from itertools import accumulate
from lxml import etree
from typing import List
from sastadev.conf import settings
from sastadev.constants import outtreebanksfolder, silverfolder, silversuffix
from sastadev.datasets import dsname2ds
from sastadev.filefunctions import getbasename
from sastadev.macros import expandmacros
from sastadev.methods import Method, supported_methods
from sastadev.readmethod import read_method
from sastadev.resultsbyutterance import getexactbyutt
from sastadev.SAFreader import get_golddata, richscores2scores
from sastadev.sastatypes import QId, SynTree
from sastadev.treebankfunctions import getattval as gav, getnodeyield, getsentence, getxsid
from sastadev.tarsp_codes import allVcombinations, allVBcombinations, Vcombinations, \
    anymood, decl, imp, question, V1questioncodes, noV1questioncodes
from sastadev.xlsx import mkworkbook
from sastadev.gettarspstats import predictiondict, tarspfrequenciesdict
# from sas_queries import synxsid, synquery
import os

comma = ','

outtreebankssuffix = '_corrected'


methodfullname = "D:\Dropbox\jodijk\myprograms\python\sastacode\mysastadev\src\sastadev\data\methods\TARSP_Index_Current.xlsx"

# tarspmethod = read_method('tarsp', methodfullname)

xsidquery = './/meta[@name="xsid"]/@value'
synquery = './/meta[@name="syn"]/@value'

unexpandedimpxpath = './/node[%basicimperative%]'
impxpath = expandmacros(unexpandedimpxpath)

errorheader = ['dataset', 'sample', 'xsid', 'sent', 'refcodes', 'suggestions', 'refitems', 'suggesteditems',
               'prediction']

errorfilename = 'VCsuggestionerrors.xlsx'
errorpath = './VCsuggestions'
os.makedirs(errorpath, exist_ok=True)
errorfullname = os.path.join(errorpath, errorfilename)

def getaddition(stage, mood) -> List[str]:
    if (stage, mood) in Vcombinations:
        result = Vcombinations[(stage, mood)]
    elif (stage, anymood) in Vcombinations:
        result = Vcombinations[(stage, anymood)]
    else:
        result = []
    return result

def predictcodes(key: tuple) -> List[str]:
    (lnodeyields, lrealwords, lphrasewords, lbnodes, mood, v1found, nietfound) = key
    rawsuggestions = []
    themax = min(lphrasewords, 7)
    if themax >= 2:
        for i in range(themax):
            if i > 0:
                addition = getaddition(i+1, mood)
                rawsuggestions.extend(addition)
    suggestions = []
    for rawsuggestion in rawsuggestions:
        if key in predictiondict and rawsuggestion in predictiondict[key]:
            predictionfrq = predictiondict[key][rawsuggestion]
        else:
            predictionfrq = 0
        if lbnodes > 0:
            if rawsuggestion in allVBcombinations:
                lbnodescore = 1
            else:
                lbnodescore = 0
        else:
            lbnodescore = 0
        if rawsuggestion in tarspfrequenciesdict:
            tarspfrq = tarspfrequenciesdict[rawsuggestion]
        else:
            tarspfrq = 0
        sortkey = (lbnodescore, predictionfrq, tarspfrq)
        newsuggestion = (rawsuggestion, sortkey)
        suggestions.append(newsuggestion)
    uniquesuggestions = list(set(suggestions))
    if not nietfound:
        uniquesuggestions = [codetuple for codetuple in uniquesuggestions if codetuple[0] != 'T140']
    if v1found:
        uniquesuggestions = [codetuple for codetuple in uniquesuggestions if codetuple[0] not in noV1questioncodes]
    else:
        uniquesuggestions = [codetuple for codetuple in uniquesuggestions if codetuple[0] not in V1questioncodes]
    sortedsuggestions = sorted(uniquesuggestions, key=lambda x: x[1], reverse=True)
    result = [el[0] for el in sortedsuggestions]
    return result





def getstype(stree: SynTree):
    nodes = getnodeyield(stree)
    lastnode = nodes[-1]
    lastnodept = gav(lastnode, 'pt')
    lastnodelemma = gav(lastnode, 'lemma')
    headverbs = stree.xpath('.//node[@rel="hd" and @pt="ww" and parent::node[parent::node[@cat="top"]]]')
    headverb = headverbs[0] if headverbs != [] else None
    isimperative = stree.xpath(impxpath) != []
    hetochfound = gav(nodes[-2], 'lemma') in  ['hè', 'he', 'toch']
    firstwordwh = gav(nodes[0], 'pt') == 'vnw' and gav(nodes[0], 'vwtype') == 'vb' or stree.xpath('.//node[@cat="whq"]')
    firstwordv =  gav(nodes[0], 'pt') == 'ww' and gav(nodes[0], 'wvorm') == 'pv' or \
                  stree.xpath('.//node[@cat="sv1" and @rel!="body"]')
    if firstwordwh:
        result = question
    elif lastnodept == 'let':
        if lastnodelemma == '.':
            if isimperative:
                result = imp
            else:
                result = decl
        elif lastnodelemma == '?':
            if hetochfound:
                result = decl
            elif firstwordwh or firstwordv:
                result = question
            else:
                result = decl
        elif lastnodelemma == '!':
            if isimperative:
                result = imp
            else:
                result = decl
        else:
            if isimperative:
                result = imp
            else:
                result = decl
    else:
        result = decl
    return result

def xsid(tree: SynTree) -> bool:
    xsids = tree.xpath(xsidquery)
    result = xsids != []
    return result

def promoteb(codelist: List[str]) -> List[str]:
    bs = []
    nobs = []
    for code in codelist:
        if code in allVBcombinations:
            bs.append(code)
        else:
            nobs.append(code)
    result = bs + nobs
    return result

def predictvcombinations(stree: SynTree, method: Method, qids=False) -> List[str]:
    nodeyield = getnodeyield(stree)
    sent = getsentence(stree)
    wwnodes = [n for n in nodeyield if gav(n, 'pt') == 'ww']
    if wwnodes == []:
        return []
    lnodeyields = len(nodeyield)
    realwords = [n for n in nodeyield if gav(n, 'pt') not in ['tsw', 'let']]
    phrasewords = [n for n in realwords if (not(gav(n, 'pt') == 'vz' and gav(n, 'rel') == 'hd') or n == realwords[-1])
                   and gav(n, 'pt') != 'lid']
    bnodes = [n for n in realwords if gav(n, 'pt') in ['vz', 'bw']]
    lrealwords = len(realwords)
    lphrasewords = len(phrasewords)
    lbnodes = len(bnodes)
    mood = getstype(stree)
    v1found = stree.xpath('.//node[@cat="sv1" and @rel!="body"]') != [] or gav(nodeyield[0], 'pt') == 'ww'
    nietfound = stree.xpath('.//node[@lemma="niet"]') != []
    keyproperties = (lnodeyields, lrealwords, lphrasewords, lbnodes, mood, v1found, nietfound)
    qidresult = predictcodes(keyproperties)
    if qidresult == [] and mood != decl:
        keyproperties = (lnodeyields, lrealwords, lphrasewords, lbnodes, decl, v1found, nietfound)
        qidresult = predictcodes(keyproperties)
    if qids:
        result = [qid for qid in qidresult if qid in method.queries]
    else:
        result = [method.queries[qid].item for qid in qidresult if qid in method.queries]
    return result


def getsimpleposition(suggestions: List[QId], reference: List[QId]) -> int:
    for i, suggestion in enumerate(suggestions):
        if suggestion in reference:
            return i
    return -1

def getposition(suggestions: List[QId], reference: List[str], method: Method) -> int:
    simplealtcodedict = method.simplealtcodedict
    qidreference = []
    for code in reference:
        codelc = code.lower()
        if codelc in method.simpleitem2idmap:
            qid = method.simpleitem2idmap[codelc]
        elif codelc in simplealtcodedict:
            defcode = simplealtcodedict[codelc]
            qid = method.simpleitem2idmap[defcode] if defcode in method.simpleitem2idmap else 'UNK'
        else:
            qid = 'UNK'
        qidreference.append(qid)
    for i, suggestion in enumerate(suggestions):
        if suggestion in qidreference:
            return i
    return -1



def tryme():
    errordata = []
    positions = defaultdict(int)
    suggestionlengths = defaultdict(int)
    datasetnames = ['auristrain', 'vkltarsp']
    datasetnames = ['auristest']
    treebankfilenames = []
    irrelevantcount = 0
    for datasetname in datasetnames:
        treebankspath = os.path.join(settings.DATAROOT, datasetname, outtreebanksfolder)
        treebankfilenames = [fn for fn in os.listdir(treebankspath) if fn.endswith('.xml') ]
        dataset = dsname2ds[datasetname]
        methodname = dataset.method
        variant = dataset.variant
        methodfilename = supported_methods[methodname]
        themethod = read_method(methodname, methodfilename, variant=variant)

        for treebankfilename in treebankfilenames:
            treebankfullname = os.path.join(treebankspath, treebankfilename)
            fulltreebank = etree.parse(treebankfullname)
            treebank = fulltreebank.getroot()
            silverfilename = f'{getbasename(treebankfilename)[:-len(outtreebankssuffix)]}{silversuffix}.xlsx'
            silverpath = os.path.join(settings.DATAROOT, datasetname, silverfolder)
            silverfullname = os.path.join(silverpath, silverfilename)
            silverallannutts, richexactsilverscores = get_golddata(silverfullname, themethod)
            exactsilverscores = richscores2scores(richexactsilverscores)
            theresultsbyutt = getexactbyutt(exactsilverscores)
            for tree in treebank:
                if xsid(tree):
                    sent = getsentence(tree)
                    thexsid = getxsid(tree)
                    nodeyield = getnodeyield(tree)
                    wwnodes = [n for n in nodeyield if gav(n, 'pt') == 'ww']
                    lwwnodes = len(wwnodes)
                    realwords = [n for n in nodeyield if gav(n, 'pt') not in ['tsw', 'let']]
                    lrealwords = len(realwords)
                    if wwnodes == [] or lrealwords < 2 or lrealwords == lwwnodes:
                        irrelevantcount += 1
                        continue
                    thecodes = [key[0][0] for key in theresultsbyutt[thexsid]]
                    suggestions = predictvcombinations(tree, qids=True)
                    suggestionlengths[len(suggestions)] += 1
                    if thecodes == []:
                        position = -2
                    else:
                        position = getsimpleposition(suggestions, thecodes)
                        if position == -1:
                            codeitems = [themethod.queries[qid].item for qid in thecodes]
                            suggesteditems = [themethod.queries[qid].item for qid in suggestions]
                            vccodes = [qid for qid in thecodes if qid in allVcombinations]
                            predicted = vccodes == []
                            predictionval = 'predicted' if predicted else 'incorrect'
                            errorrow = [datasetname, treebankfilename, thexsid, sent, thecodes, suggestions,
                            codeitems, suggesteditems, predictionval ]
                            errordata.append(errorrow)
                        junk = 0
                    positions[position] += 1


    print(f'Irrelevant utterances: {irrelevantcount}')

    print('\nSuggestion lengths:\n')
    for el in suggestionlengths:
        print(f'{el}: {suggestionlengths[el]}')

    print('\nPositions:\n')
    rawpositionslist = [(key, freq) for key, freq in positions.items()]
    positionslist = [el for el in rawpositionslist if el[0] != -1]
    sortedpositionslist = sorted(positionslist, key=lambda x: x[0])
    sortedkeylist = [el[0] for el in sortedpositionslist]
    sortedfrqlist = [el[1] for el in sortedpositionslist]
    cumsumlist =  list(accumulate(sortedfrqlist))
    cumsum = cumsumlist[-1]
    sortedpctlist = [frq / cumsum * 100 for frq in sortedfrqlist]
    cumpctlist = list(accumulate(sortedpctlist))
    fulllist = list(zip(sortedkeylist, sortedfrqlist, cumsumlist, sortedpctlist, cumpctlist))
    min1 = [el for el in rawpositionslist if el[0] == -1]
    for el in min1:
        print(f'{el[0]}\t{el[1]}\t\t')
    for key, freq, cumfreq, pct, cumpct in fulllist:
        print(f'{key}\t{freq}\t{cumfreq}\t{pct:.1f}\t{cumpct:.1f}')

    errortable = []
    for row in errordata:
        rowstr = [str(el) for el in row]
        errortable.append(rowstr)
    wb = mkworkbook(errorfullname, [errorheader], errortable, freeze_panes=(1,0))
    wb.close()


if __name__ == '__main__':
    tryme()

