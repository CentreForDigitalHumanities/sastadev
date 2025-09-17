from typing import Callable, List, Tuple
from sastadev.lexicon import vuwordslexicon
from sastadev.macros import expandmacros
from sastadev.sastatypes import SynTree
from sastadev.stringfunctions import punctuationchars
from sastadev.tblex import get_aanloop_and_core
from sastadev.treebankfunctions import (adjacent, find1, get_left_siblings,
                                        getattval, getnodeyield, parent)

comma = ','

nietxpath = './/node[@lemma="niet"]'
wordxpath = './/node[@pt]'

vzn1basexpath = './/node[ @cat="pp" and (node[@pt="vz"] and node[(@pt="n" or @pt="vnw") and not (%Rpronoun%) and @rel="obj1"] and not(node[@pt="vz" and @vztype="fin"]))]'
vzn1xpath = expandmacros(vzn1basexpath)
vzn2xpath = './/node[node[@lemma="in" and @rel="mwp"] and node[@lemma="deze" and @rel="mwp"]]'
vzn3xpath = './/node[@pt="vz" and ../node[(@lemma="dit" or @lemma="dat")  and @begin>=../node[@pt="vz"]/@end and count(node)<=3] ]'
#vzn4basexpath = './/node[node[@pt="vz" and @rel="hd" and ../node[%Rpronoun% and @rel="obj1" and @end <= ../node[@rel="hd"]/@begin]]]'
#vzn4xpath = expandmacros(vzn4basexpath)

#: The constant *voslahbijxpath* selects nodes (PPs) that contain an adposition and an R-pronoun or a index node
#: coindexed with an R-pronoun.
#:
#: **Remark** It is not actually checked whether the indexed node has an R-pronoun as its antecedent
#:
#: **Remark** We may have to do something special for *pobj1*
#:
voslashbijxpath = expandmacros(""".//node[node[@pt="vz" and @rel="hd"] and
            node[@rel="obj1" and
                 ((@index and not(@word or @cat)) or
                  (%Rpronoun%)
                 )]]""")

#: The constant *vobijxpath* uses the macro *Vobij* to identify adverbial pronouns.
#: The macro **Vobij** is defined as follows::
#:
#:   Vobij = """(@pt="bw" and (contains(@frame,"er_adverb" ) or contains(@frame, "tmp_adverb") or @lemma="daarom") and
#:               @lemma!="er" and @lemma!="daar" and @lemma!="hier" and @lemma!="waar" and
#:               (starts-with(@lemma, 'er') or starts-with(@lemma, 'daar') or
#                 starts-with(@lemma, 'hier') or starts-with(@lemma, 'waar'))
#:              )"""
#:
vobijxpath = expandmacros('.//node[%Vobij%]')


mvznxpath = """.//node[@pt = "n" and  @getal ="mv"]"""
mvznsuffixes = ['en', 'e', 's', 'n']

verklxpath = expandmacros(""".//node[@pt="n" and @graad="dim" and not(%nodimlemma%)]""")
verklsuffixes = ['je', 'jes', 'ie', 'ies', 'ke', 'kes']


def notadjacent(n1, n2, t): return not adjacent(n1, n2, t)


def xneg(stree):
    nodepairs = []
    nietnodes = stree.xpath(nietxpath)
    for nietnode in nietnodes:
        pnietnode = parent(nietnode)
        leftnietsiblings = get_left_siblings(nietnode)
        leftsiblings = get_left_siblings(pnietnode)
        ppnietnode = parent(pnietnode)
        if getattval(pnietnode, 'cat') == "advp" and len(leftsiblings) == 1 and getattval(ppnietnode, 'rel') == '--':
            result = True
            theleftsibling = leftsiblings[0]
        elif getattval(pnietnode, 'cat') != "advp" and getattval(pnietnode, 'rel') == '--' and len(leftnietsiblings) == 1:
            result = True
            theleftsibling = leftnietsiblings[0]
        else:
            result = False
        if result:
            nodepairs.append((theleftsibling, nietnode))
    if nodepairs == []:
        return None
    else:
        return nodepairs[0]


def xneg_neg(stree):
    (x, neg) = xneg(stree)
    return neg


def xneg_x(stree):
    (x, neg) = xneg(stree)
    return x


def VzN(stree):
    results = []
    results += stree.xpath(vzn1xpath)
    results += stree.xpath(vzn2xpath)
    results += stree.xpath(vzn3xpath)
    #results += stree.xpath(vzn4xpath) # does not belong here after all, these will be scored under Vo/Bij
    return results


def auxvobij(stree: SynTree, pred: Callable[[SynTree, SynTree, SynTree], bool]) -> List[SynTree]:
    '''

    :param stree: the syntactic structure to be analysed
    :param pred: a predicate that the results found must satisfy
    :return: a list of matching nodes

    The function *auxvobij* finds nodes that are found by the *voslashbijxpath* and selects from these those
    that satisfy the predicate *pred*. It is used to distinguish cases of R-pronoun + adposition that are *adjacent*
    (which should be analysed as TARSP *Vobij*) from those that are not adjacent (which should be analysed as TARSP
    Vo/Bij).

    .. autodata:: sastadev.queryfunctions::voslashbijxpath

    '''
    RPnodes = stree.xpath(voslashbijxpath)
    results = []
    for RPnode in RPnodes:
        # find the head node
        headnode = find1(RPnode, 'node[@rel="hd"]')

        # find the obj1node
        obj1node = find1(RPnode, 'node[@rel="obj1"]')

        if headnode is not None and obj1node is not None:
            if pred(obj1node, headnode, stree):
                results.append(RPnode)
    return results


def vobij(stree: SynTree) -> List[SynTree]:
    '''

    :param stree: syntactic structure to be analysed
    :return: List of matching nodes

    The function *vobij* uses the Xpath expression *vobijxpath* and the function *auxvobij* to obtain its resulting nodes:

    * The *vobijxpath* expression matches with so-called adverbial pronouns:

      .. autodata:: sastadev.queryfunctions::vobijxpath

    * The function *auxvobij*  finds adjacent R-pronoun + adposition cases:

      .. autofunction:: sastadev.queryfunctions::auxvobij

    '''
    results1 = stree.xpath(vobijxpath)
    results2 = auxvobij(stree, vobijpred)
    results = results1 + results2
    return results


def voslashbij(stree: SynTree) -> List[SynTree]:
    '''

    :param stree: syntactic structuire to be analysed
    :return: List of matching nodes

    The function *voslashbij* uses the function *auxvobij* to find non-adjacent R-pronoun + adposition cases:

    .. autofunction:: sastadev.queryfunctions::auxvobij
          :noindex:


    '''
    results = auxvobij(stree, notadjacent)
    return results

def vobijpred(obj1node, headnode, stree) -> bool:
    #check for adjacency  (er naar is ok, er gisteren naar not)
    cond1 = adjacent(headnode, obj1node, stree)

    # check whether the obj1node precedes the headnode: daar naar is ok, naar daar is not ok
    headposition = int(getattval(headnode, 'end'))
    obj1position = int(getattval(obj1node, 'end'))
    cond2 = obj1position < headposition
    result = cond1 and cond2
    return result


def hequery(syntree: SynTree) -> List[SynTree]:
    """

    :param syntree:
    :return: the node for hè or he, sentence final or prefinal and followed by a punctuation sign
    """
    henodes = syntree.xpath('.//node[@lemma="hè" or @lemma="he"]')
    if henodes != []:
        henode = max(henodes, key=lambda node: int(getattval(node, 'end')))
        nodeyield = getnodeyield(syntree)
        barenodeyield = [node for node in nodeyield if getattval(node, 'pt') != 'let']
        result = [henode] if henode == barenodeyield[
            -1] else []  # the found node must be the last one if punctuation is removed
    else:
        result = []
    return result


vudiversxpath = """
.// node[(@ lemma != "ja" and @ lemma != "nee" and @ word != "xxx" and @ lemma != "mama" and @ word != "xx" and
         (( @ pt="tsw" ) or
          ((@ lemma="au" or @ lemma="hoepla" or @ lemma="dag" or @ lemma="kijk" or @ lemma="hap" or @ lemma="aai") and
           (@ rel="--" or @ rel="sat" or @ rel="tag")
		  )
         ) 
		) or %Tarsp_kijkVU% or %Tarsp_hehe% or %dankje_VU%
    ]
"""
def vudivers(syntree: SynTree) -> List[SynTree]:
    expandedvudiversxpath = expandmacros(vudiversxpath)
    rawresults = syntree.xpath(expandedvudiversxpath)
    vuresults = aanloopuitloopvu(syntree)
    allrawresults = rawresults + [node for node in vuresults if node not in rawresults]
    heresults = hequery(syntree)
    results = [result for result in allrawresults if result not in heresults]
    return results

def tarsp_mvzn(stree: SynTree) -> List[SynTree]:
     mvzns = stree.xpath(mvznxpath)
     realmvzns = [mvzn for mvzn in mvzns if any([mvzn.attrib['word'].endswith(suf) for suf in mvznsuffixes])]
     return realmvzns

def tarsp_verkl(stree: SynTree) -> List[SynTree]:
    verkls = stree.xpath(verklxpath)
    realverkls = [verkl for verkl in verkls if any([verkl.attrib['word'].endswith(suf) for suf in verklsuffixes])]
    return realverkls



def getuitloop(nodeyield: List[SynTree]) -> Tuple[List[SynTree], List[SynTree]]:
    lastlemma = getattval(nodeyield[-1], 'lemma')
    if lastlemma in punctuationchars:
        if lastlemma == comma:
            return nodeyield, []
        elif len(nodeyield) >= 3:
            potential_uitloop = [-3, -2]
        else:
            return nodeyield, []
    elif len(nodeyield) >= 2:
        potential_uitloop = [-2, -1]
    else:
        return nodeyield, []
    lemma1 = getattval(nodeyield[potential_uitloop[0]], 'lemma')
    lemma2 = getattval(nodeyield[potential_uitloop[1]], 'lemma')
    if lemma2 in vuwordslexicon and \
        lemma1 == comma and \
        '3' in vuwordslexicon[lemma2] and \
        comma in vuwordslexicon[lemma2]:
        return nodeyield[:potential_uitloop[0]], nodeyield[potential_uitloop[0]:]
    else:
        return nodeyield, []


def aanloopuitloopvu(stree: SynTree) -> List[SynTree]:
    results = []
    nodeyield = getnodeyield(stree)
    aanloop, remainder = get_aanloop_and_core(nodeyield)
    core, uitloop = getuitloop(remainder)
    topnode = find1(stree, './/node[@cat="top"]')
    if topnode is not None and len(aanloop) >= 2:
        topnodebegin = getattval(topnode, 'begin')
        vunode = aanloop[0]
        vunodebegin = getattval(vunode, 'begin')
        vunodelemma = getattval(vunode, 'lemma')
        if vunodebegin == topnodebegin and vunodelemma in vuwordslexicon:
            results.append(vunode)
    if len(uitloop) >= 2:
        vunode = uitloop[1]
        results.append(vunode)
    for node in core:
        nodelemma = getattval(node, 'lemma')
        if nodelemma in vuwordslexicon and '2' in vuwordslexicon[nodelemma]:
            results.append(node)
    return results


def only_puncs(nodelist: List[SynTree]) -> bool:
    for node in nodelist:
        nodelemma = getattval(node, 'lemma')
        if nodelemma not in punctuationchars:
            return False
    return True