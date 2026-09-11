import os

from sastadev.conf import settings
from sastadev.constants import intreebanksfolder, outtreebanksfolder
from sastadev.datasets import alldatasets, trainingdatasets, testdatasets
from sastadev.lexicon import modalverbs
from sastadev.dedup import filledpauseslexicon
from sastadev.sastatypes import FileName, SynTree
from sastadev.treebankfunctions import (getattval, getnodeyield, getstree,
                                        getuttid, getyield, onbvnwdet)
from typing import List

digits2 = r'\d\d'

asta = 'asta'
tarsp = 'tarsp'
stap = 'stap'
dld = 'dld'
schl = 'schlichting'
auris = 'auris'

gav = getattval

def shorten(fullname):
    _, filename = os.path.split(fullname)
    basename, _ = os.path.splitext(filename)
    return basename


def getpaths(dataset, source='both'):
    result = []
    if source in ['in', 'both']:
        result += [os.path.join(settings.DATAROOT, dataset, intreebanksfolder)]
    if source in ['out', 'both']:
        result += [os.path.join(settings.DATAROOT, dataset, outtreebanksfolder)]
    return result



ext = '.xml'


class Ngram:
    def __init__(self, n, cond):
        self.n = n
        self.cond = cond


def commonancestor(node1, node2, stree, ancestorcond):
    nodes = stree.xpath('.//node')
    ancestorcandidates = [n for n in nodes if ancestorcond(n)]
    for anc in ancestorcandidates:
        descendants = anc.xpath('.//node')
        if node1 in descendants and node2 in descendants:
            return True
    return False


def lemma(x):
    return getattval(x, 'lemma')


def word(x):
    return getattval(x, 'word')


# det = lambda x : pt(x) == 'lw' or (pt(x) == 'vnw' and getattval(x, 'vwtype') in {'aanw', 'bez'})

def pt(x):
    return getattval(x, 'pt')


def findmatches(ngram, leaves):
    matches = []
    for i in range(len(leaves) - ngram.n + 1):
        if ngram.cond(leaves[i:i + ngram.n], leaves, i):
            newmatch = (i, i + ngram.n)
            matches.append(newmatch)
    return matches

def get_paths(ds, source='both') -> List[FileName]:
    base_path = os.path.join(settings.DATAROOT, ds.name)
    results = []
    if source in ['in', 'both']:
        results += [os.path.join(base_path, intreebanksfolder)]
    if source in ['out', 'both']:
        results += [os.path.join(base_path, outtreebanksfolder)]
    return results


def getfilenames(ds, session=None, source='both'):
    thepaths = get_paths(ds, source)
    if session is not None:
        def cond(x): return (x + 1 == session)
    else:
        def cond(_): return True
    infullnames = [os.path.join(path, ifn) for path in thepaths for ifn in os.listdir(path) if ifn.endswith('.xml')]
    return infullnames


def Rpronoun(el):
    result = lemma(el) in {'er', 'hier', 'daar'}
    return result


def ispv(n):
    result = pt(n) == 'ww' and getattval(n, 'wvorm') == 'pv'
    return result


def sipvjpvjsi(ns, stree):
    resultmatches = []
    ngram1 = Ngram(2, cond13)
    matches = findmatches(ngram1, ns)
    for (b, e) in matches:
        vnw1 = ns[b]
        pv1 = ns[e - 1]
        pv2found = False
        for mc in range(e, len(ns) - 2):
            if ispv(ns[mc]):
                if word(ns[mc]).lower() == word(pv1).lower():
                    pv2 = ns[mc]
                    if not commonancestor(pv1, pv2, stree, lambda x: getattval(x, 'cat') == 'smain'):
                        pv2found = True
                        pv2pos = mc
                    break
            else:
                mc += 1
        if pv2found:
            vnw2found = word(ns[pv2pos + 1]).lower() == word(vnw1).lower()
            if vnw2found:
                resultmatch = (b, e, mc, mc + 2)
                resultmatches.append(resultmatch)
    return resultmatches


def cond17f(ns, lvs, i):
    result = lemma(ns[0]) == 'te'
    result = result and getattval(ns[1], 'his') == 'te_verb'
    result = result and lemma(ns[2]) == 'te'
    return result


def cond1(ns, _, i): return pt(ns[0]) == 'vnw' and pt(ns[1]) == 'ww' and getattval(ns[1], 'wvorm') == 'pv' and \
    pt(ns[2]) == 'vnw' and lemma(ns[0]) == lemma(ns[2]) and pt(ns[3]) == 'ww' and \
    getattval(ns[3], 'wvorm') == 'pv'


def det(el): return (pt(el) == 'lid'
                     or (pt(el) == 'vnw' and getattval(el, 'vwtype') in {'aanw', 'bez'})
                     or (pt(el) == 'vnw' and getattval(el, 'vwtype') == 'onbep' and onbvnwdet(el))
                     ) and \
    not Rpronoun(el)   # and getattval(el, 'positie') == 'prenom' left out


def erhierdaar(el): return lemma(el) in {'er', 'hier', 'daar'}


def is_def_det(el):
    result1 = pt(el) == 'vnw' and (getattval(el, 'vwtype') in {'aanw', 'bez'})  # deze man, mijn huis, Jan zijn vrouw
    result2 = pt(el) == 'lid' and getattval(el, 'lwtype') == 'bep'              # de man, het huis
    result3 = pt(el) == 'n' and getattval(el, 'naamval') == 'gen'               # Jans huis
    result4 = pt(el) == 'vnw' and getattval(el, 'naamval') == 'gen'             # wiens huis maar iemand krijgt de verkeerde naamval
    result5 = pt(el) == 'vnw' and getattval(el, 'word').lower() == 'iemands'    # iemands huis
    result = result1 or result2 or result3 or result4 or result5
    return result

def cond2(ns, _, i): return pt(ns[0]) == 'vz' and det(ns[1]) and (not erhierdaar(ns[1])) and pt(ns[2]) == 'vz' and \
    det(ns[3]) and (not erhierdaar(ns[3]))


def cond3(ns, _, i): return pt(ns[0]) == 'n' and pt(ns[1]) == 'n'
def cond4(ns, lvs, i): return lemma(ns[0]) == "," and ns[1] == lvs[-1]
def cond4a(ns, lvs, i): return lemma(ns[0]) == "," and pt(ns[2]) == 'let' and ns[2] == lvs[-1]
def cond5(ns, _, i): return lemma(ns[0]) == 'nou' and lemma(ns[1]) == 'ja'
def cond6(ns, lvs, i): return pt(ns[0]) == 'n' and len([lv for lv in lvs[:i - 1] if lemma(lv) == lemma(ns[0])]) > 1
def cond7(ns, lvs, i): return pt(ns[0]) == 'vg' and det(ns[1]) and lemma(ns[2]) == lemma(ns[0]) and det(ns[3])
def cond8(ns, lvs, i): return word(ns[2]).startswith(word(ns[0])) and word(ns[3]).startswith(word(ns[1]))


def cond9(ns, _, i): return pt(ns[0]) == 'vnw' and getattval(ns[0], 'vwtype') == 'pers' and pt(ns[1]) == 'ww' and \
    getattval(ns[1], 'wvorm') == 'pv' and pt(ns[2]) == 'vnw' and getattval(ns[2], 'vwtype') == 'pers' and pt(ns[3]) == 'ww' and \
    getattval(ns[3], 'wvorm') == 'pv'  and getattval(ns[1], 'lemma') not in  ['denken', 'bedoelen'] and getattval(ns[3], 'lemma') != 'geloven' # and \
# (word(ns[0]) == word(ns[2]) or word(ns[1]) == word(ns[3]) or lemma(ns[1]) == lemma(ns[3]))


def cond10(ns, lvs, i): return pt(ns[0]) == 'vnw' and getattval(ns[0], 'vwtype') == 'pers' and \
    pt(ns[1]) == 'ww' and getattval(ns[1], 'wvorm') == 'pv' and \
    pt(ns[2]) != 'ww' and word(ns[3]) == word(ns[1]) and word(ns[4]) == word(ns[0])


def cond11(ns, lvs, i): return lemma(ns[0]) == lemma(ns[2]) and lemma(ns[1]) == lemma(ns[3]) and \
    (word(ns[0]) != word(ns[2]) or word(ns[1]) != word(ns[3]))


def cond12(ns, lvs, i): return pt(ns[0]) == 'vz' and det(ns[1]) and pt(ns[2]) == 'vz' and det(ns[3])  # == cond2


def cond13(ns, lvs, i): return pt(ns[0]) == 'vnw' and getattval(ns[0], 'vwtype') == 'pers' and pt(ns[1]) == 'ww' and \
    getattval(ns[1], 'wvorm') == 'pv'


def cond14(ns, lvs, i): return ns[0] != lvs[0] and lemma(ns[0]) != 'nou' and (lemma(ns[1]) in filledpauseslexicon or pt(ns[0]) == 'tsw') and lemma(ns[2]) == 'nee'
def cond15(ns, lvs, i): return ns[0] != lvs[0] and lemma(ns[1]) == 'nee'


def cond16(ns, lvs, i): return det(ns[0]) and det(ns[2]) and lemma(ns[1]) == lemma(ns[3]) \
    and pt(ns[1]) == 'n' and pt(ns[3]) == 'n'
def cond16a(ns, lvs, i): return lemma(ns[0]) in {'een', 'geen'} and lemma(ns[2]) in {'een', 'geen'} and lemma(ns[1]) == lemma(ns[3]) \
    and pt(ns[1]) == 'n' and pt(ns[3]) == 'n'


def cond17(ns, lvs, i): return lemma(ns[0]) == 'te' and getattval(ns[1], 'his') == 'te_verb' and lemma(ns[2]) == 'te'
# cond17 = cond17f
def cond17a(ns, lvs, i): return lemma(ns[0]) == 'te' and word(ns[1]) == 'kregen' and lemma(ns[2]) == 'te'


def cond18(ns, lvs, i): return pt(ns[0]) == 'vz' and lemma(ns[1]) in {'dit', 'dat', 'deze', 'die'}

def cond19(ns, lcs, i): return  pt(ns[0]) == 'vg'  and pt(ns[1]) == 'vg'  and \
                               gav(ns[0], 'conjtype') == 'onder' and gav(ns[1], 'conjtype') == 'onder' and \
                               not (lemma(ns[0]) == 'dat' and lemma(ns[1]) == 'als') # omdat doordat

def cond20(ns, _, i): return pt(ns[1]) == 'vnw' and getattval(ns[1], 'vwtype') == 'pers' and pt(ns[0]) == 'ww' and \
    getattval(ns[0], 'wvorm') == 'pv' and pt(ns[3]) == 'vnw' and getattval(ns[3], 'vwtype') == 'pers' and pt(ns[2]) == 'ww' and \
    getattval(ns[2], 'wvorm') == 'pv'  and getattval(ns[0], 'lemma') not in  ['denken', 'bedoelen', 'geloven'] and \
    getattval(ns[2], 'lemma') not in  ['denken', 'bedoelen', 'geloven']

def cond21(ns, _, i): return pt(ns[1]) =='adj' and getattval(ns[1], 'buiging') == 'met-e' and \
                            pt(ns[2]) == 'n' and getattval(ns[2], 'getal') == 'ev' and \
                            getattval(ns[2], 'genus') == 'onz' and \
                            not is_def_det(ns[0]) and not(word(ns[0]) == 'onder' and word(ns[1]) == 'andere')

def cond22(raw_ns, _, i):
    ns = [n for n in raw_ns if pt(n) != 'let']
    if len(ns) >= 3:
        return pt(ns[0]) not in ['vg', 'tsw'] and lemma(ns[1]) in ['die'] and pt(ns[2]) == 'ww' and gav(ns[2], 'wvorm') == 'pv'
    else:
        return False

def is_tgw_mv(nd: SynTree) -> bool:
    result = gav(nd, 'pt') == 'ww' and gav(nd, 'wvorm') == 'pv' and \
             gav(nd, 'pvtijd') == 'tgw' and gav(nd, 'pvagr') == 'mv'
    return result

def cond23(ns,_, i):
    if len(ns) >= 3:
        result0 = pt(ns[0]) != 'ww'
        first = ns[1]
        second = ns[2]
        result1 = pt(first) == 'ww'
        result2 = gav(first, 'wvorm') == 'inf'
        result6 = gav(first, 'lemma') not in modalverbs
        result7 = gav(first, 'positie') != 'nom'
        result3 = is_tgw_mv(first)
        result4 = gav(second, 'lemma') in modalverbs
        result5 = gav(second, 'wvorm') == 'pv'
        return  result0 and result1 and (result2 or result3) and result6 and \
               result4

ngram1 = Ngram(4, cond1)
ngram2 = Ngram(4, cond2)
ngram3 = Ngram(2, cond3)
ngram4 = Ngram(2, cond4)  # uitloop maar zonder punc daarachter
ngram4a = Ngram(3, cond4a)  # uitlopp maar met punc daarachter
ngram5 = Ngram(2, cond5)
ngram6 = Ngram(1, cond6)
ngram7 = Ngram(4, cond7)
ngram8 = Ngram(4, cond8)  # partial repeat sequence
ngram9 = Ngram(4, cond9)  # vnw pv vnw pv
ngram10 = Ngram(5, cond10)  # vnwj pvi x pvi vnwj
ngram11 = Ngram(4, cond11)  # lemma_i lemma_j lemma_i lemma_j
ngram12 = Ngram(4, cond12)  # vz det vz det
ngram14 = Ngram(3, cond14)  # fp/tsw + nee , to apply to the uncleaned leaves
ngram15 = Ngram(2, cond15)  # word + nee, to apply to the cleanleaves
ngram16 = Ngram(4, cond16)  # geen beroerte een beroerte
ngram16a = Ngram(4, cond16a)  # geen beroerte een beroerte test
ngram17 = Ngram(4, cond17)  # te kregen te krijgen
ngram17a = Ngram(4, cond17a)  # te kregen te krijgen test
ngram18 = Ngram(2, cond18)  # met dit
ngram19 = Ngram(2, cond19) # omdat doordat
ngram20 = Ngram(4, cond20) # heb ik zie ik: pv vnw pv vnw
ngram21 = Ngram(3, cond21) # een mooie meisje
ngram22 = Ngram(3, cond22) # (dit is een man) die heeft een mooi jasje
ngram23 = Ngram(3, cond23)  # beesten die *bloeden kunnen*

def main():

    infullnames = []
    thedatasets = trainingdatasets + testdatasets
    for ds in thedatasets:
        infullnames += getfilenames(ds, source='in')

    # for ds in [asta]:
    #    infullnames += getfilenames(ds, session=4)

    for infullname in infullnames:
        short = shorten(infullname)
        fulltreebank = getstree(infullname)
        if fulltreebank is not None:
            treebank = fulltreebank.getroot()
            for tree in treebank:
                uttid = getuttid(tree)
                leaves = getnodeyield(tree)
                cleanleaves = [leave for leave in leaves if getattval(leave, 'word') not in filledpauseslexicon]
                cleanwordlist = [getattval(leave, 'word') for leave in cleanleaves]
                matches = findmatches(ngram23, cleanleaves)
                # matches = sipvjpvjsi(cleanleaves, tree)
                for match in matches:
                    uttid = getuttid(tree)
                    cleanleaves_str = [word(el) for el in cleanleaves]
                    print(short, uttid, match, cleanleaves_str, getyield(tree))


if __name__ == '__main__':
    main()
