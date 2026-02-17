import copy
from lxml import etree
import os
from sastadev.conf import settings
from sastadev.constants import outtreebanksfolder
from sastadev.lexicon import informlexicon, adj_no_pp_lexicon
from sastadev.macros import expandmacros
from sastadev.methods import Method
from sastadev.sastatypes import ExactResultsDict, SynTree, TreeBank
from sastadev.stringfunctions import monosyllabic
from sastadev.treebankfunctions import clausebodycats, find1, getattval as gav, getnodeyield, getxsid, getmeta, \
    adjacent, showtree, getbeginend
from typing import List, Tuple

compoundsep = '_'

# def getunknownwordnodes(
#     nt: TreeBank, exactresults: ExactResultsDict, method: Method
# ) -> List[Tuple[SynTree, str, list]]:
#     """
#     identifies nodes that are unknown words and that have not been replaced by SASTA by known words
#     :param nt:
#     :param _:
#     :param method:
#     :return:
#     """
#
#     mn = method.name
#     rawresults = []
#     rawunknownwordnodes = []
#     for tree in nt:
#         uttid = getxsid(tree)
#         if uttid == "0":
#             continue
#         session = getmeta(tree, "session")
#         junk = 0
#         wordnodes = [wn for wn in tree.xpath('.//node[@pt!="tsw"]')]
#         rawunknownwordnodes = [
#             wn
#             for wn in wordnodes
#             if not isvalidword(
#                 wn.attrib["word"].lower(), mn, includealpinonouncompound=False
#             )
#             and not compoundsep in wn.attrib["lemma"]
#             and not isrobustname(wn)
#             and gav(wn, "pt") != "tsw"
#             and not gav(wn, "word").isnumeric()
#             and not isnumericordinal(gav(wn, "word"))
#         ]
#     rawresults += [
#         (unknownwordnode, f'{unknownwordmessage}: {gav(unknownwordnode, "word")}', [])
#         for unknownwordnode in rawunknownwordnodes
#     ]
#     results = filterbymetadata(rawresults, exactresults, method.name)
#     return results

rel_as_avn_xpath = """
.//node[@pt="vnw" and @rel="rhd" and 
        ../../../node[@cat="np" and @rel="--" and
                      node[@pt="n" and @rel="hd"] and
                      node[@cat="rel" and @rel="mod"]] and
	    ../node[@cat="ssub" and @rel="body" and
                node[@pt="ww" and @rel="hd"]]
      ]            """


def get_rel_as_avn_nodes(stree: SynTree) -> List[SynTree]:
    results = []
    rawnodes = stree.xpath(rel_as_avn_xpath)
    for rawnode in rawnodes:
        verbnodes = rawnode.xpath("""../node[@cat="ssub" and @rel="body" ]/node[@pt="ww" and @rel="hd"]""")
        if verbnodes != []:
            verbnode = verbnodes[0]
            if adjacent(rawnode, verbnode, stree):
                results.append(rawnode)
    return results

# this one rejected we prefer to transform the relevant structures
def get_avn(stree: SynTree) -> List[SynTree]:
    avn_xpath = expandmacros(""".//node[%AVn%]""")
    results = stree.xpath(avn_xpath)
    results += get_rel_as_avn_nodes(stree)
    return results


def get_end(stree: SynTree) -> str:
    nodeyield = getnodeyield(stree)
    lastwordnode = nodeyield[-1] if nodeyield != [] else None
    if lastwordnode is not None:
        result = gav(lastwordnode, 'end')
    else:
        result = '-1'
    return result

np_rel_avn_xpath = """.//node[@cat="np" and @rel="--" and
    node[@pt="n" and @rel="hd"] and
    node[@cat="rel" and @rel="mod" and
        node[@pt="vnw" and @rel="rhd"] and
        node[@cat="ssub" and @rel="body" and
            node[@pt="ww" and @rel="hd"]]]]
			"""


def transform_rel2avn(instree: SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    np_nodes = stree.xpath(np_rel_avn_xpath)
    for np_node in np_nodes:
        np_parent = np_node.getparent()
        rel_node = find1(np_node, """./node[@cat="rel" and @rel="mod"]""")
        np_node.remove(rel_node)
        du_node = etree.Element('node', {'cat': ' du', 'rel':'--' })
        np_parent.append(du_node)
        np_node.set('rel', 'sat')
        np_node_end = get_end(np_node)
        np_node.set('end', np_node_end)
        du_node.append(np_node)
        rel_node.set('rel', 'nucl')
        du_node.append(rel_node)
        du_node.set('begin', gav(np_node, 'begin'))
        du_node.set('end', gav(rel_node, 'end'))
    return

adj_pp_xpath = """.//node[@cat="ap" and node[@rel="hd" and @pt="adj"] and node[@cat="pp" or (@pt="bw" and starts-with(@frame,"er_adverb"))]]"""
def transform_adj_pp(instree: SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    ap_nodes = stree.xpath(adj_pp_xpath)
    for ap_node in ap_nodes:
        ap_hd_node = find1(ap_node, """./node[@rel="hd"]""")
        if ap_hd_node is not None:
            hd_lemma = gav(ap_hd_node, 'lemma')
            if hd_lemma in adj_no_pp_lexicon:
                ap_parent = ap_node.getparent()
                ap_parent_cat = gav(ap_parent, 'cat')
                pp_node = find1(ap_node, """./node[@cat="pp" or (@pt="bw" and starts-with(@frame,"er_adverb")) and @rel="mod"]""")
                if pp_node is not None:
                    if ap_parent_cat not in clausebodycats:
                        ap_begin, ap_end = getbeginend(ap_node)
                        ap_node_rel = gav(ap_node, 'rel')
                        new_parent = etree.Element('node',
                                                   {'cat': 'du', 'rel': ap_node_rel,
                                                    'begin': ap_begin, 'end': ap_end})
                        ap_parent.remove(ap_node)
                        new_parent.append(ap_node)
                        ap_node.remove(pp_node)
                        ap_new_begin, ap_new_end = getbeginend(ap_node)
                        new_parent.append(pp_node)
                        ap_parent.append(new_parent)
                        ap_node.set('rel', 'dp')
                        ap_node.set('begin', ap_new_begin)
                        ap_node.set('end', ap_new_end)
                        pp_node.set('rel', 'dp')
                    else:
                        new_parent = ap_parent
                        ap_node.remove(pp_node)
                        ap_new_begin, ap_new_end = getbeginend(ap_node)
                        new_parent.append(pp_node)
                        ap_node.set('begin', ap_new_begin)
                        ap_node.set('end', ap_new_end)
    return stree


def test1():
    datasetname = 'auristrain'
    inputpath = os.path.join(settings.DATAROOT, datasetname, outtreebanksfolder, 'trees', 'TD03_corrected')
    inputfilename = 'TD03_corrected_018.xml'
    inputfullname = os.path.join(inputpath, inputfilename)
    fulltree = etree.parse(inputfullname)
    tree = fulltree.getroot()
    # avn_nodes = get_avn(tree)
    # for node in avn_nodes:
    #     print(node.attrib['word'], node.attrib['begin'])
    # newtree = transform_rel2avn(tree)
    newtree = transform_adj_pp(tree)
    showtree(newtree)
    outtreefile = 'transformed_tree.xml'
    fullnewtree = etree.ElementTree(newtree)
    fullnewtree.write(outtreefile, encoding="UTF8", xml_declaration=False,
                       pretty_print=True)

if __name__ == '__main__':
    test1()