"""
Module to develop new functions in . This modulke is NOT used by sastadev. Functions and data in this file are only temporarily here.
"""
import copy
from sastadev.conf import settings
from sastadev.displaytree import printtree
from sastadev.metadata import Meta
from sastadev.parse_criteria import Criterion, negative
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getattval as gav, getyieldstr, getxsid
from typing import List


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

# moved to treetransform
# def mustbesplit(adv1: SynTree, adv2: SynTree) -> bool:
#     pass
#
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


