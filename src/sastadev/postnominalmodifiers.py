import copy
from lxml import etree
from sastadev.sastatypes import SynTree, XpathExpression
from sastadev.treebankfunctions import getattval, find1, hasnominativehead, immediately_precedes
from typing import Tuple

postnominalmodifier = "Postnominal Modifier Adaptation"

nonvheadedparentnp = """parent::node[@cat="np" and node[@rel="hd" and @pt!="ww"]]"""

ppinnpxpath = f""".//node[@cat="pp" and node[@rel="hd" and @lemma!="van" and @lemma!="met" and @lemma!="mee"] and 
                         {nonvheadedparentnp}]"""

modbwinnpxpath = f""".//node[(@lemma="ook" or @lemma="eerst") and 
                         {nonvheadedparentnp}]"""

alleenbwinnpxpath = f""".//node[@lemma="alleen" and 
                         {nonvheadedparentnp}]"""

modRinnpxpath = f""".//node[@pt="vnw" and @special="er_loc" and {nonvheadedparentnp}]"""

def transformppinnp(instree: SynTree) -> SynTree:
    result = transformmodinnp(instree, ppinnpxpath)
    return result

def transformbwinnp(instree: SynTree) -> SynTree:
    result = transformmodinnp(instree, modbwinnpxpath)
    return result

def transformalleeninnp(instree: SynTree) -> SynTree:
    result = transformmodinnp(instree, alleenbwinnpxpath)
    return result


def transformmodRinnp(instree: SynTree) -> SynTree:
    result = transformmodinnp(instree, modRinnpxpath)
    return result


def is_np1v2(np: SynTree, stree: SynTree) -> bool:
    np_parent = np.getparent()
    np_parent_cat = getattval(np_parent, 'cat')
    if np_parent_cat != 'smain':
        return False
    pv = find1(np, '../node[@pt="ww" and @rel="hd" and @wvorm="pv"]')
    if pv is None:
        return False
    result = immediately_precedes(np, pv, stree)
    return result


def transformmodinnp(instree: SynTree, modxpath: XpathExpression) -> SynTree:
    stree = copy.deepcopy(instree)
    ppsinnp = stree.xpath(modxpath)
    for ppinnp in ppsinnp:
        theparent = ppinnp.getparent()
        grandparent = theparent.getparent()
        grandparentcat = getattval(grandparent, 'cat')
        thenp_head = find1(theparent, './node[@rel="hd"]')
        thenp_head_vwtype = getattval(thenp_head, 'vwtype')
        if grandparentcat == 'top':
            # create a new clause node under
            clausebegin = getattval(theparent, 'begin')
            clauseend = getattval(theparent, 'end')
            clausenode = etree.Element('node', {'cat': 'smain', 'rel': '--', 'begin': clausebegin, 'end': clauseend,
                                                'id': "1000"})
            grandparent.append(clausenode)
            # put the np under this clausenode
            clausenode.append(theparent)
            # detach the pp to under the clausenode
            detach(ppinnp)
            # make and insert a verb
            # determine getal of the np
            # next is not needed and not desirable
            # getal = getgetal(theparent)
            # moetattrib = getmoetattrib(getal, "1001", theparent.attrib['end'])
            # smallclauseverb = etree.Element('node', moetattrib)
            # clausenode.append(smallclauseverb)
            # insertword = getattval(smallclauseverb, 'word')
            # insertpos = getattval(smallclauseverb, 'begin')
            # meta1 = Meta(insertion, [insertword], annotatedposlist=[insertpos],
            #      annotatedwordlist=[], annotationposlist=[insertpos],
            #      annotationwordlist=[insertword], cat=postnominalmodifier, source=SASTA, penalty=defaultpenalty,
            #      backplacement=bpl_delete)
            # metadata = [meta1]
        elif grandparentcat == 'smain' and thenp_head_vwtype != 'pers':
            if not is_np1v2(theparent, stree):
                theparent.remove(ppinnp)
                grandparent.append(ppinnp)
        else:
            detach(ppinnp)
            # metadata = []

    return stree

def detach(node: SynTree):
    """
    remove the node from its parent and attach it to its grandparent but only if node.emd == parent.end
    :param node:
    :return:
    """

    # remove node from its parent, adapt parent begin and end; only if end of node1 == end of parent
    parent = node.getparent()
    targetnode = parent.getparent()
    node_end = getattval(node, 'end')
    parent_end = getattval(parent, 'end')
    node_begin = getattval(node, 'begin')
    parent_begin = getattval(node, 'begin')
    if node_end == parent_end or node_begin == parent_begin:
        parent.remove(node)
        parent_rel = getattval(parent, 'rel')
        therel = 'su' if hasnominativehead(parent) else parent_rel
        parent.attrib['rel'] = therel   # @@@ or obj1 if not clearly nominative

        # adapt the (begin and ) end of the nodeparent
        newbegin, newend = getbeginandend(parent)
        parent.attrib['begin'] = newbegin
        parent.attrib['end'] = newend

        # append node to the targetnode
        targetnode.append(node)


def getmoetattrib(getal: str, id: int, prevend: str) -> dict:
    word = 'moet' if getal == 'ev' else 'moeten'
    moetbegin = str(int(prevend) - 1 + 5)
    moetend = str(int(moetbegin) + 1)
    result = {'lemma': 'moeten', 'word': word,  'pt': 'ww', 'wvorm': 'pv', 'pvagr': getal,
              'pvtijd': 'tgw', 'root': 'moet', 'sense': 'moet', 'postag': f'WW(pv, tgw,{getal})',
              'id': id, 'begin': moetbegin, 'end': moetend}
    return result


def getgetal(node: SynTree) -> str:
    # @@to be extended
    for child in node:
        childrel = getattval(child, 'rel')
        if childrel == 'hd':
            if 'getal' in child.attrib:
                 return child.attrib['getal']
            else:
                return 'ev'
        elif childrel == 'cnj':
            return 'mv'                  # @@this is a adhoc and will be sufficient for most cases but must be extended'

def getbeginandend(node: SynTree) -> Tuple[str, str]:
    curbegin = 10000
    curend = 0
    for child in node:
        if int(child.attrib['begin']) < curbegin:
            curbegin = int(child.attrib['begin'])
        if int(child.attrib['end']) > curend:
            curend = int(child.attrib['end'])
    return str(curbegin), str(curend)

met_np_pp_xpath = """.//node[@cat="pp" and node[@rel="hd" and @lemma="met"] and node[@cat="np" and node[@cat="pp" or @cat="advp" or @pt="adv"]]]"""
def transform_met_np_pp(instree: SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    met_np_pps = stree.xpath(met_np_pp_xpath)
    for met_np_pp in met_np_pps:
        pp = find1(met_np_pp, './node[@pt="np"]/node[@pt="pp"]')
        if pp is None:
            return instree
        pp_parent = pp.getparent()
        met_np_pp_parent = met_np_pp.getparen()
        if pp_parent is not None and met_np_pp_parent is not None:
            pp_parent.remove(pp)
            met_np_pp_parent.append(pp)
            pp.set('rel', 'mod')
    return stree
