"""
Module to develop new functions in . This modulke is NOT used by sastadev. Functions and data in this file are only temporarily here.
"""
import copy
from lxml import etree
import re
from sastadev import correctionlabels
from sastadev.conf import settings
from sastadev.displaytree import printtree
from sastadev.metadata import Meta, bpl_wordlemma, mkSASTAMeta, mkinsertmeta
from sastadev.parse_criteria import Criterion, negative
from sastadev.sastatypes import PositionStr, SynTree, UttId
from sastadev.sastatoken import mktokenlist, Token
from sastadev.semantic_compatibility import getantecedentof
from sastadev.stringfunctions import smartsortkey, intre
from sastadev.tokenmd import TokenListMD
from sastadev.treebankfunctions import find1, getattval, getbeginend, getyieldstr, getxsid, inflate_step
from typing import List

gav = getattval

# these functions to be revised
def normalisebeginend(instree: SynTree) -> SynTree:
    """
    :param instree: syntactic structure
    :return: stree with the values of begin and end attributes normalised
    """
    stree = copy.deepcopy(instree)
    begins = {getattval(node, 'begin')
              for node in stree.xpath('.//node[count(node)=0]')}
    sortedbegins = sorted(list(begins), key=lambda x: int(x))
    result = normalisebeginend2(stree, sortedbegins)
    return result


def normalisebeginend2(instree: SynTree, sortedbegins: List[PositionStr]) -> SynTree:
    """

    :param instree: syntactic structure
    :param sortedbegins: sorted list of begin values of @pt or @pos nodes
    :return:  stree with the values of begin and end attributes normalised
    """
    stree = copy.deepcopy(instree)
    children = list(stree)   # adapt this to select only children with tag node (because of the  ud extensions)
    newchildren = []
    for child in children:
        newchild = normalisebeginend2(child, sortedbegins)
        newchildren.append(newchild)
    #remove the old children
    for child in stree:
        stree.remove(child)
    if stree.tag == "node":
        if newchildren == []:
            nodebegin = getattval(stree, 'begin')
            intnodebegin = int(nodebegin)
            newintbegin = sortedbegins.index(nodebegin)
            newbegin = str(newintbegin)
            newend = str(newintbegin + 1)
            stree.attrib['begin'] = newbegin
            stree.attrib['end'] = newend
        else:
            (minbegin, maxend) = getbeginend(newchildren)
            stree.attrib['begin'] = minbegin
            stree.attrib['end'] = maxend

    #append the new chidren
    stree.extend(newchildren)
    return stree


def denormalisebeginend2(instree: SynTree, sortedbegins: List[PositionStr]) -> SynTree:
    """
    adapts the begins and ends of a tree to the sortedbegins: first word will get the first sortedegin, etc
    :param instree: syntactic structure
    :param sortedbegins: sorted list of begin values of @pt or @pos nodes
    :return: None
    """
    stree = copy.deepcopy(instree)
    children = list(stree) if stree is not None else [] # adapt this to select only children with tag node (because of
    # the  ud extensions) but be careful we should allow metadata etc alpino_ds, sentence
    newchildren = []
    for child in children:
        newchild = denormalisebeginend2(child, sortedbegins)
        newchildren.append(newchild)
    #remove the old children
    for child in stree:
        stree.remove(child)
    if stree.tag == "node":
        if newchildren == []:
            nodebegin = getattval(stree, 'begin')
            intnodebegin = int(nodebegin)
            newbegin = sortedbegins[intnodebegin]
            newend = str(int(newbegin) + 1)
            stree.attrib['begin'] = newbegin
            stree.attrib['end'] = newend
        else:
            (minbegin, maxend) = getbeginend(newchildren)
            stree.attrib['begin'] = minbegin
            stree.attrib['end'] = maxend
    # append the new children
    stree.extend(newchildren)
    return stree



# added this to parse_criteria.py
# predmxpath = './/node[@rel="predm"]'
#
# def getpredmcount(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> int:
#     predms = getpredm(tree)
#     return len(predms)
#
# def getpredm(tree):
#     predms = tree.xpath(predmxpath)
#     return predms
#
# predmcriterion =  Criterion('predmcount', getpredmcount, negative,
#                             "Count of number of occurrences of nodes with relation 'predm'")

# moved to n
# # move PP out of predc/ap
#
# predc_ap_with_pp_xpath = './/node[@cat="ap" and @rel="predc" and node[@cat="pp"]]'
# def transform_ppinap(stree: SynTree) -> SynTree:
#     newstree = copy.deepcopy(stree)
#     predc_ap_with_pp_nodes = newstree.xpath(predc_ap_with_pp_xpath)
#     if predc_ap_with_pp_nodes == []:
#         return stree
#     for apnode in predc_ap_with_pp_nodes:
#         apnodeparent = apnode.getparent()
#         for child in apnode:
#             if gav(child, 'cat') == 'pp':
#                 apnode.remove(child)
#                 apnodeparent.append(child)
#     return newstree


# split advp consisting of two adverbs
adv_adv_advp_xpath = './/node[@cat="advp" and count(node[@pt="bw"]) = 2]'
def splitadvadv(stree: SynTree) -> SynTree:
    newstree = copy.deepcopy(stree)
    adv_adv_advps = newstree.xpath(adv_adv_advp_xpath)
    if adv_adv_advps == []:
        return stree
    for adv_adv_advp in adv_adv_advps:
        adv1 = adv_adv_advp[0]
        adv2 = adv_adv_advp[1]
        if mustbesplit(adv1, adv2):
            adv_adv_advp.remove(adv1)
            adv_adv_advp.remove(adv2)
            if gav(adv1, 'rel') == 'hd':
                adv1.set('rel', gav(adv_adv_advp, 'rel'))
            elif gav(adv2, 'rel') == 'hd':
                adv2.set('rel', gav(adv_adv_advp, 'rel'))
            else:
                settings.LOGGER.info(f'Headless advp: {getyieldstr(adv_adv_advp)} in '
                                     f'utterance {getxsid(stree)}: {getyieldstr(newstree)}')
            adv_adv_advp_parent = adv_adv_advp.getparent()
            adv_adv_advp_parent.remove(adv_adv_advp)
            adv_adv_advp_parent.extend([adv1,adv2])
    return newstree

def mustbesplit(adv1: SynTree, adv2: SynTree) -> bool:
    pass

# moved to corrector
# subjectlessgaxpath = """.//node[@cat="sv1" and
#        node[@rel="hd" and @pt="ww" and @wvorm="pv" and @pvagr="ev" and @pvtijd="tgw" and @lemma="gaan"] and
#        not(node[@rel="su"]) and
#        not(.//node[@lemma="maar" or @lemma="eens" or @lemma="dan" ]) and
#        not(ancestor::alpino_ds/descendant::node[@lemma="!"])
#       ]"""
#
#
# def subjectlessga(tokensmd: TokenListMD, tree: SynTree) -> List[TokenListMD]:
#     """
#     :param tokensmd: list of tokens with metadata
#     :param tree: syntax tree
#     turns "ga naar huis." into "ik ga naar huis"
#     """
#     allresults = []
#     tokens = tokensmd.tokens
#     reducedtokens = [token for token in tokens if not token.skip]
#     metadata = copy.deepcopy(tokensmd.metadata)
#
#     first = reducedtokens[0] if reducedtokens != [] else None
#     matches = tree.xpath(subjectlessgaxpath)
#     if matches == []:
#         return []
#     else:
#         if first.word.lower == "ga":   # we only do it once per utterance, and only if ga is the first word
#             fpos = first.pos - inflate_step
#             inserttokens = [Token('ik', fpos, subpos=5)]
#             resultlist = mktokenlist(tokens, fpos, inserttokens)
#             metadata += mkinsertmeta(inserttokens, resultlist)
#             result = TokenListMD(resultlist, metadata)
#             allresults = [result]
#     return allresults


# moved to corrector
# e zo -< zo'n zoeenerror toevoegen aancorrectionlabels, schwa aan stringfunctions
# def ezo2zon(tokensmd: TokenListMD, tree: SynTree, uttid: UttId) -> List[TokenListMD]:
#     rawtokens = tokensmd.tokens
#     tokens = [t for t in rawtokens if not t.skip]
#     metadata = tokensmd.metadata
#     efound = False
#     zofound = False
#     newtokens = []
#     meta = None
#     for i, token in enumerate(rawtokens):
#         prevtoken = rawtokens[i-1] if i > 0 else None
#         nexttoken = rawtokens[i+1] if i < len(rawtokens)-1 else None
#         if token.skip:
#             newtokens.append(token)
#             continue
#         elif token.word in ['e', schwa] and nexttoken is not None and nexttoken.word == 'zo':
#             newtoken = Token(token.word, token.pos, skip=True)
#             newtokens.append(newtoken)
#             efound = True
#         elif token.word == 'zo' and prevtoken is not None and prevtoken.word in ['e', schwa]:
#             newtoken = Token("zo'n", token.pos)
#             newtokens.append(newtoken)
#             zofound = True
#             meta = mkSASTAMeta(token, newtoken, name=correctionlabels.ezozonreplacement, value="zo'n",
#                                cat=correctionlabels.zoeenerror,
#                                backplacement=bpl_wordlemma, penalty=dp)
#
#         else:
#             newtokens.append(token)
#     if efound and zofound:
#         if meta is not None:
#             metadata.append(meta)
#         results = [TokenListMD(newtokens, metadata)]
#     else:
#         results = []
#     return results

# moved to treetransform
# # jij zelf opspspliten
#
# def getendof(nodes: List[SynTree]) -> str:
#     sortednodes =  sorted(nodes, key=lambda n: int(gav(n, 'end')))
#     if sortednodes == []:
#         return '0'
#     else:
#         return gav(sortednodes[-1], 'end')
#
# pronzelfxpath = './/node[@cat="np"   and node[@rel="mod" and @lemma="zelf"] ]'
#
# def splitpronzelf(stree: SynTree) -> SynTree:
#     newtree = copy.deepcopy(stree)
#     zelfnps = newtree.xpath(pronzelfxpath)
#     if zelfnps == []:
#         return stree
#     for zelfnp in zelfnps:
#         zelfnpparent = zelfnp.getparent()
#         for child in zelfnp:
#             if gav(child, 'lemma') == 'zelf':
#                 zelfnp.remove(child)
#                 zelfnp.set('end', getendof([ch for ch in zelfnp]))
#                 zelfnpparent.append(child)
#                 child.set('rel', 'predm')
#     return newtree

dup_pattern = r'(.+)\1'
def koekoek(wrd:str) -> str:
    newwrd = re.sub(dup_pattern, r'\1', wrd)
    return newwrd




if __name__ == '__main__':
    for wrd in ['koekoeks_klok', 'boeken']:
        newwrd = koekoek(wrd)
        print(newwrd)