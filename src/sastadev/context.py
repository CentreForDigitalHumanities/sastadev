from collections import defaultdict
from editdistance import distance
from lxml import etree
import os
from sastadev.conf import settings
from sastadev.constants import outtreebanksfolder
from sastadev.datasets import infiguresdatasets
from sastadev.filefunctions import getbasename
from sastadev.lexicon import known_word
from sastadev.sastatypes import TreeBank, SynTree
from sastadev.treebankfunctions import getattval, getorigutt, getmeta, getxsid
from sastadev.xlsx import mkworkbook
from typing import Callable, List, Tuple

comma = ','

realwordnodesxpath = """.//node[@word and @pt!='tsw' and @pt!='let']"""

redthreshold = 0.5


def relativedistance(wrd1: str, wrd2: str) -> float:
    dist = distance(wrd1, wrd2)
    maxl = max(len(wrd1), len(wrd2))
    result = dist/maxl
    return result

def mustbedone(stree: SynTree) -> bool:
    origutt = getorigutt(stree)
    xsid = getmeta(stree, 'xsid')
    result = '[+ G]' in origutt or xsid is not None
    return result

def getcontextdict(treebank: TreeBank, cond: Callable) -> dict:
    resultdict = defaultdict(lambda: defaultdict(tuple))
    for tree in treebank:
        if cond(tree):
            xsid = getxsid(tree)
            if xsid == '0':
                continue
            realwordnodes = tree.xpath(realwordnodesxpath)
            words = [getattval(wordnode, 'word') for wordnode in realwordnodes]
            wrongwords = [word for word in words if len(word) > 4 and not known_word(word)]
            origutt = getorigutt(tree)
            if wrongwords == []:
                continue
            for wrongword in wrongwords:
                prevcontext = getcontext(tree, treebank, -5, nottargetchild)
                postcontext = getcontext(tree, treebank, +5, nottargetchild)
                prevbestwords = findbestwords(wrongword, prevcontext, lambda x: True)
                postbestwords = findbestwords(wrongword, postcontext, lambda x: True)
                resultdict[xsid][wrongword] = (prevbestwords, postbestwords)
    return resultdict

def getcontext(stree:SynTree, tb: TreeBank, size: int, cond: Callable) -> List[SynTree]:
    """
    get the context of *stree* in treebank *tb* with size *size*. each stree in the context must satisfy condition *cond*.
    Negative size means preceding context, positive size means following context. Preceding context is delivered reversed
    :param stree:
    :param tb:
    :param size:
    :param cond: SynTree -> bool
    :return:
    """
    if size == 0:
        return []
    streeindex = tb.index(stree)
    ltb = len(tb)
    context = []
    curindex = streeindex
    while curindex >= 0 and curindex < ltb - 1:
        incr = +1 if size > 0 else -1
        curindex = curindex + incr
        curtree = tb[curindex]
        if len(context) == abs(size):
            break
        if cond(curtree) and len(context) < abs(size):
            context.append(curtree)
    # if size < 0:
    #    context = reversed(context)
    return context

def getwordnodetuplesfromcontext(context: List[SynTree], cond: Callable) -> List[Tuple[SynTree, int]]:
    """
    get the real word nodes from the context with their distance if the word satisfies the condition *cond*.
    real words are words that are no interjections or interpunction (pt != 'tsw" and pt!= 'let')
    :param context: List[SynTree]. Preceding context must be in reverse order
    :param cond: str -> bool
    :return:
    """
    results = []
    for i, stree in enumerate(context):
        rawwordnodes = stree.xpath(realwordnodesxpath)
        wordnodes = [wordnode for wordnode in rawwordnodes if cond(getattval(wordnode, 'word'))]
        streeresults = [(wordnode, i) for wordnode in wordnodes]
        results += streeresults
    return results

def getwordtuplesfromcontext(context: List[SynTree], cond: Callable) -> List[Tuple[str, int]]:
    wntuples = getwordnodetuplesfromcontext(context, cond)
    wtuples = [(getattval(wn, 'word'), i) for wn, i in wntuples]
    return wtuples

def getlemmatuplesfromcontext(context: List[SynTree], cond: Callable) -> List[Tuple[str, int]]:
    wntuples = getwordnodetuplesfromcontext(context, cond)
    wtuples = [(getattval(wn, 'lemma'), i) for wn, i in wntuples]
    return wtuples



def islemmaincontext(wordnode: SynTree, context: List[SynTree]) -> bool:
    lemmatuples = getlemmatuplesfromcontext(context, lambda x: True)
    lemmas = [lemma for lemma, i in lemmatuples]
    thislemma = getattval(wordnode, 'lemma')
    result = thislemma in lemmas
    return result

def findbestwords(wrongword: str, context: List[SynTree], cond: Callable) -> List[str]:
    """
    find the word *w* in the context that satisfies *cond*, and scores highest on the properties
    (-relative_edit_distance(wrongword, w), -distance)
    :param wrongword:
    :param context:
    :param cond:
    :return:
    """
    rawresults = []
    wntuples = getwordnodetuplesfromcontext(context, cond)
    bestred = 1
    for wordnode, distance in wntuples:
         word = getattval(wordnode, 'word')
         red = relativedistance(wrongword, word)
         if red < redthreshold:
             rawresults.append((word, red, distance))
    sortedresults = sorted(rawresults, key=lambda x: (x[1], x[2]))
    if sortedresults != []:
        first = sortedresults[0]
        filteredresults = [rawresult for rawresult in sortedresults if (rawresult[1], rawresult[2]) == (first[1], first[2])]
    else:
        filteredresults = []
    finalresults = [w for (w, red, dst) in filteredresults if len(w) > 4]
    return finalresults

def nottargetchild(stree: SynTree) -> bool:
    spk = getmeta(stree, 'speaker')
    result = spk != 'CHI'
    return result


def main():
    table = []
    datasets = infiguresdatasets
    for dataset in datasets:
        fullpath = os.path.join(settings.DATAROOT, dataset.name, outtreebanksfolder)
        filenames = os.listdir(fullpath)
        # filenames= ['TD21.xml']
        for filename in filenames:
            sample = getbasename(filename)
            # print(f'Sample: {sample}')
            infullname = os.path.join(fullpath, filename)
            fulltreebank = etree.parse(infullname)
            if fulltreebank is None:
                print(f'No treebank {infullname} found, aborting')
                exit(-1)
            treebank = fulltreebank.getroot()
            for tree in treebank:
                if mustbedone(tree):
                    realwordnodes = tree.xpath(realwordnodesxpath)
                    words = [getattval(wordnode, 'word') for wordnode in realwordnodes ]
                    wrongwords = [word for word in words if len(word) > 4 and not known_word(word)]
                    origutt = getorigutt(tree)
                    if wrongwords == []:
                        continue
                    # print(f'UTT: {origutt}. Best corrections:' )
                    for wrongword in wrongwords:
                        # print(f'wrong word: {wrongword}')
                        prevcontext = getcontext(tree, treebank, -5, nottargetchild)
                        postcontext = getcontext(tree, treebank, +5, nottargetchild)
                        prevbestwords = findbestwords(wrongword, prevcontext, lambda x: True)
                        # print(f'Preceding context: {comma.join(prevbestwords)}')
                        postbestwords = findbestwords(wrongword, postcontext, lambda x: True)
                        # print(f'Post context: {comma.join(postbestwords)}')
                        row = [dataset.name, sample, wrongword, comma.join(prevbestwords),
                               comma.join(postbestwords), origutt]
                        table.append(row)

    header = ['dataset', 'sample', 'wrongword', 'prev', 'post', 'origutt']
    outfilename = 'contextcorrections.xlsx'
    outpath = os.path.join(settings.SD_DIR, 'data', 'contextcorrections')
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    outfullname = os.path.join(outpath, outfilename)
    wb = mkworkbook(outfullname, [header], table, freeze_panes=(1,0))
    wb.close()

if __name__ == '__main__':
    main()