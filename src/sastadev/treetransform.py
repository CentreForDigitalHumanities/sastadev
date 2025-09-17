import copy
from sastadev.conf import settings
from sastadev.lexicon import compoundsep, lemmalexicon
from sastadev.macros import expandmacros
from sastadev.treebankfunctions import find1, getattval, getbeginend, getnodeyield, getyield, \
    immediately_precedes, iswordnode, showtree
from sastadev.sastatypes import SynTree
from sastadev.tblex import is_rpronoun
from lxml import etree
from typing import List

space = ' '

tagcommaclausexpath = """.//node[@cat="smain" and 
                          node[@pt="n" and @end = ancestor::alpino_ds/descendant::node[@lemma="," ]/@begin and 
                               @begin = ancestor::node[@cat="top"]/@begin]]"""

sv1xpath = """.//node[@cat="sv1" and parent::node[@cat="top"]]"""
tagxpath = """.//node[@pt="n" and @end = ancestor::alpino_ds/descendant::node[@lemma="," ]/@begin and 
                               @begin = ancestor::node[@cat="top"]/@begin]"""
tagcommaxpath = """.//node[@lemma=","]"""
notsv1xpath = """.//node[(not(@cat) or @cat!="sv1") and parent::node[@cat="top"]]"""

nognonpxpath = """.//node[@lemma="nog" and parent::node[not(@cat="np")]]"""
nogxpath = """.//node[@lemma="nog" and parent::node[@cat="np" and not(node[@rel="hd" and @pt="ww"])]]"""
eenxpath = """.//node[(@lemma="een" or @lemma="één" or @lemma="eentje" or @lemma="meer" or @lemma="minder" or 
                      @lemma="zo'n" or @pt="tw")   and parent::node[@cat="np"]]"""
dexpath = """.//node[(@lemma="de" or @lemma="het" or @lemma="deze" or @lemma="die") and parent::node[@cat="np"]]"""

nognietxpath = """.//node[@cat="advp" and node[@rel="mod" and @lemma="nog"] and node[@rel="hd" and @lemma="niet"] and not(parent::node[@cat="top"])]"""
zelfinnpmodxpath = """.//node[@rel="mod" and @lemma="zelf" and parent::node[@cat="np"]]"""

smainwithverbxpath = """.//node[@cat="smain" and node[@rel="hd" and @pt="ww" and @wvorm="pv"]]"""


hwwwithsvpxpath = expandmacros(""".//node[@pt="ww" and %hwwwithsvp%  and not(%hwwwithsvpexception%) and 
                     ../node[@rel="svp" and  @pt="vz"] and 
                     ../node[@rel="mod" and %Rpronoun%]]""")

def transformtreeld(stree:SynTree) -> SynTree:
    debug = False
    if debug:
        showtree(stree, 'intree')
    newstree = copy.deepcopy(stree)
    ldxpath = """.//node[node[@rel="hd" and @pt="ww"] and
       node[@rel="ld" and (@pt="n" or @cat="np")] and
       node[@rel="svp"  and @pt="vz"] and
       not(node[@rel="su"])
       ]"""
    ldclauses = newstree.xpath(ldxpath)
    for ldclause in ldclauses:
        ldnodes = ldclause.xpath(' node[@rel="ld" and (@pt="n" or @cat="np")]')
        if ldnodes != []:
            ldnodes[0].attrib["rel"] = "su"
    if debug:
        showtree(newstree, 'outtree')
    return newstree

def transformtreenogeen(stree:SynTree) -> SynTree:
    debug = False
    if debug:
        showtree(stree, 'intree')
    newstree = copy.deepcopy(stree)
    nogs = newstree.xpath(nognonpxpath)
    eens = newstree.xpath(eenxpath)
    for nog in nogs:
        for een in eens:
            if immediately_precedes(nog, een, newstree):
                nog.getparent().remove(nog)
                een.getparent().insert(0, nog)
                nog.set('rel', 'mod')      # it can have rel dp when outside the NP
                nogbegin = getattval(nog, 'begin')
                een.getparent().set('begin', nogbegin)
    if debug:
        showtree(newstree, 'outtree')
    return newstree

def transformtreenogde(stree:SynTree) -> SynTree:
    debug = False
    if debug:
        showtree(stree, 'intree')
    newstree = copy.deepcopy(stree)
    nogs = newstree.xpath(nogxpath)
    des = newstree.xpath(dexpath)
    eens = newstree.xpath(eenxpath)
    if eens == []:   # otherwise we have transformtreenogeen
        for nog in nogs:
            for de in des:
                if immediately_precedes(nog, de, newstree):
                    nog.getparent().remove(nog)
                    de.getparent().getparent().append(nog)
            if des == [] and eens == []:
                nog_grandparent = nog.getparent().getparent()
                nog.getparent().remove(nog)
                nog_grandparent.append(nog)
            if debug:
                showtree(newstree, 'outtree')
    return newstree

def transformtagcomma(stree: SynTree) -> SynTree:
    debug = False
    newtree = copy.deepcopy(stree)
    match = find1(newtree, tagcommaclausexpath)

    if match is not None:
        topnode = match.getparent()
        thetag = find1(newtree, tagxpath)
        thetagcomma = find1(newtree, tagcommaxpath)
        thenodeyield = getnodeyield(newtree)
        if isfiniteverbnode(thenodeyield[2]):
            theyield = getyield(newtree)
            sv1str = space.join(theyield[2:])
            sv1parse = settings.PARSE_FUNC(sv1str)
            if debug:
                showtree(sv1parse, 'sv1parse')
            if sv1parse is not None:
                sv1top = find1(sv1parse, './/node[@cat="top"]')
                incr = 2 if thenodeyield[0].attrib['begin'] == '0' else 20
                sv1top = increasebeginends(sv1top, incr)
                sv1node = find1(sv1top, sv1xpath)
                otherpuncs = sv1top.xpath(notsv1xpath)
                topattrib = {'cat': 'top', 'id': getattval(topnode, 'id'), 'begin': getattval(topnode, 'begin'),
                             'end': getattval(topnode, 'end')}
                newtop = etree.Element('node', topattrib)
                duattrib = {'cat': 'du', 'rel': '--', 'id': f'{getattval(topnode, "id")}a',
                            'begin': getattval(thetag, 'begin'), 'end': f'{getattval(sv1node, "end")}'}
                thedu = etree.Element('node', duattrib)
                thetag.attrib['rel'] = 'tag'
                sv1node.attrib['rel'] = 'nucl'
                thedu.append(thetag)
                thedu.append(sv1node)
                newtop.append(thetagcomma)
                newtop.append(thedu)
                newtop.extend(otherpuncs)
                newtree.remove(topnode)
                newtreechildren = [child for child in newtree]
                newtreechildren = [newtop] + newtreechildren
                newtree.extend(newtreechildren)
                result = newtree
            else:
                result = stree
        else:
            result = stree
    else:
        result = stree

    if debug:
        showtree(result, 'result')
    return result


def nognietsplit(stree: SynTree) -> SynTree:
    debug = False
    if debug:
        showtree(stree, 'nognietsplit: stree')
    newstree = copy.deepcopy(stree)
    nognietnodes = newstree.xpath(nognietxpath)
    if nognietnodes == []:
        return stree
    for nognietnode in nognietnodes:
        nog = find1(nognietnode, """./node[@lemma="nog"]""")
        niet = find1(nognietnode, """./node[@lemma="niet"]""")
        nognietnodeparent = nognietnode.getparent()
        nognietnode.remove(nog)
        nognietnode.remove(niet)
        nognietnodeparent.remove(nognietnode)
        nognietnodeparent.append(nog)
        niet.attrib['rel'] = 'mod'
        nognietnodeparent.append(niet)
    if debug:
        showtree(newstree, 'nognietsplit: newstree')
    return newstree


def adaptlemmas(stree: SynTree) -> SynTree:
    newlemmafound = False
    newstree = copy.deepcopy(stree)
    for node in newstree.iter():
        if node.tag == 'node' and iswordnode(node):
            nodeword = getattval(node, 'word')
            nodelemma = getattval(node, 'lemma')
            if nodeword == nodelemma and nodeword in lemmalexicon:
                # node.attrib['lemma'] = lemmalexicon[nodeword]
                node.set('lemma', lemmalexicon[nodeword])
                newlemmafound = True

    if newlemmafound:
        result = newstree
    else:
        result = stree
    return result


def isfiniteverbnode(node: SynTree) -> bool:
    pt = getattval(node, 'pt')
    wvorm = getattval(node, 'wvorm')
    result = pt == 'ww' and wvorm == 'pv'
    return result

def increasebeginends(stree: SynTree, incr: int) -> SynTree:
    newtree = copy.copy(stree)
    newchildren = [increasebeginends(child, incr) for child in stree]
    for child in newtree:
        newtree.remove(child)
    if iswordnode(newtree):
        newtree.attrib['begin'] = str(int(newtree.attrib['begin']) + incr)
        newtree.attrib['end'] = str(int(newtree.attrib['begin']) + 1)
    else:
        (b, e) = getbeginend(newchildren)
        newtree.attrib['begin'] = b
        newtree.attrib['end'] = e
    newtree.extend(newchildren)
    return newtree

def getV2violations(stree: SynTree) -> List[SynTree]:
    results = []
    smains = stree.xpath(smainwithverbxpath)
    for smain in smains:
        childs = [child for child in smain]
        sortedchilds = sorted(childs, key= lambda ch: int(getattval(ch, 'begin')))
        if len(sortedchilds) > 1 and getattval(sortedchilds[1], 'pt') != "ww":
            results.append(sortedchilds[1])
    return results

def transformhwwwithsvp(stree: SynTree) -> SynTree:
    """
    turns e.g kan(op_kunnen) mod/er ... svp/op into kan(kunnen)  ... mod/pp[obj1/er hd/op]
    :param stree:
    :return:
    """
    newstree = copy.deepcopy(stree)
    cands = newstree.xpath(hwwwithsvpxpath)
    if cands == []:
        return stree
    for cand in cands:
        candparent = cand.getparent()
        verb, rpronoun, vz = None, None, None
        for child in candparent:
            childpt = getattval(child, 'pt')
            childrel = getattval(child, 'rel')
            if child == cand:
                verb = child
            if childpt == 'vnw' and childrel == 'mod' and is_rpronoun(child):
                rpronoun = child
            if childrel == 'svp' and childpt == 'vz':
                vz = child
        if verb is not None and rpronoun is not None and vz is not None:
            # adapt the verb
            verblemma = getattval(cand, 'lemma')
            lemmaparts = verblemma.split(compoundsep)
            verb.set('lemma', lemmaparts[-1])

            # detach the rpronoun
            candparent.remove(rpronoun)

            # detach the svp
            candparent.remove(vz)

            # create a mod/PP
            rpronoun_begin = getattval(rpronoun, 'begin')
            vz_end = getattval(vz, 'end')
            vz_id = getattval(vz, 'id')
            pp = etree.Element('node', attrib={'rel': 'mod', 'cat': 'pp', 'begin': rpronoun_begin, 'end': vz_end,
                                               'id': f'{vz_id}a'})

            rpronoun.set('rel', 'obj1')
            vz.set('rel', 'hd')
            pp.append(rpronoun)
            pp.append(vz)
            candparent.append(pp)
    return newstree


