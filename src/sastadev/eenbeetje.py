import copy
from lxml import etree
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getattval as gav, showtree

eenbeetjequery = """.//node[@cat="np"  and
    node[@lemma="een" and @pt="lid" and @rel="det"] and
    node[@lemma="beet" and @pt="n" and @rel="hd"] and
    node[@pt="n" and @rel="mod" and @graad="dim"]]"""


def is_een_beetje_complement(node: SynTree) -> bool:
    result = gav(node, 'lemma') != "beet" and gav(node, 'pt') == 'n' and gav(node, 'graad') == 'dim'
    return result

def transform_eenbeetje(instree: SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    npnodes = stree.xpath(eenbeetjequery)
    if npnodes == []:
        return instree
    else:
        for npnode in npnodes:
            npnoderel = gav(npnode, 'rel')
            npnodeparent = npnode.getparent()
            dimns = [child for child in npnode if is_een_beetje_complement(child)]
            dimn = dimns[0] if dimns != [] else None
            beetjes = [child for child in npnode if gav(child, 'lemma') == 'beet']
            beetje = beetjes[0] if beetjes != [] else None
            if dimn is not None and beetje is not None:
                dimn.set('rel', npnoderel)
                npnode.set('rel', 'mod')
                npnode.remove(dimn)
                npnode.set('end', gav(beetje, 'end'))
                npnodeparent.append(dimn)
        return stree


def tryme():
    testfullname = r"D:\Dropbox\jodijk\Utrecht\Projects\SASTADATA\AurisTrain\outtreebanks\trees\TD03_corrected" \
                   r"\TD03_corrected_022.xml"
    fulltree = etree.parse(testfullname)
    tree = fulltree.getroot()
    newtree = transform_eenbeetje(tree)
    showtree(newtree, 'newtree')


if __name__ == '__main__':
    tryme()