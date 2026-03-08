import copy
from sastadev.conf import settings
from sastadev.lexicon import adj_no_pp_lexicon, compoundsep, lemmalexicon
from sastadev.macros import expandmacros
from sastadev.treebankfunctions import clausebodycats, find1, getattval, getbeginend, getnodeyield, getyield, \
    immediately_precedes, iswordnode, showtree, treeinflate
from sastadev.sastatypes import SynTree
from sastadev.tblex import is_rpronoun
from lxml import etree
from typing import List

space = ' '

gav = getattval

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


gaan_predc_xpath = """.//node[@rel='predc' and ../node[@rel="hd" and @lemma="gaan"]]"""
def transform_gaan_predc(instree:SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    predcs = stree.xpath(gaan_predc_xpath)
    for predc in predcs:
        predc.set('rel', 'mod')
    return stree



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

# jij zelf opspspliten

def getendof(nodes: List[SynTree]) -> str:
    sortednodes =  sorted(nodes, key=lambda n: int(gav(n, 'end')))
    if sortednodes == []:
        return '0'
    else:
        return gav(sortednodes[-1], 'end')

pronzelfxpath = './/node[@cat="np"   and node[@rel="mod" and @lemma="zelf"] ]'

def splitpronzelf(stree: SynTree) -> SynTree:
    newtree = copy.deepcopy(stree)
    zelfnps = newtree.xpath(pronzelfxpath)
    if zelfnps == []:
        return stree
    for zelfnp in zelfnps:
        zelfnpparent = zelfnp.getparent()
        for child in zelfnp:
            if gav(child, 'lemma') == 'zelf':
                zelfnp.remove(child)
                zelfnp.set('end', getendof([ch for ch in zelfnp]))
                zelfnpparent.append(child)
                child.set('rel', 'predm')
    return newtree


# move PP out of predc/ap

predc_ap_with_pp_xpath = './/node[@cat="ap" and @rel="predc" and node[@cat="pp"]]'
def transform_ppinap(stree: SynTree) -> SynTree:
    newstree = copy.deepcopy(stree)
    predc_ap_with_pp_nodes = newstree.xpath(predc_ap_with_pp_xpath)
    if predc_ap_with_pp_nodes == []:
        return stree
    for apnode in predc_ap_with_pp_nodes:
        apnodeparent = apnode.getparent()
        for child in apnode:
            if gav(child, 'cat') == 'pp':
                apnode.remove(child)
                apnodeparent.append(child)
                child.set('rel', 'mod')
    return newstree

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
        node[@pt="vnw" and @rel="rhd" and (@lemma="die" or @lemma="dat")] and
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
    return stree

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

dp_dp_rel_avn_xpath = """.//node[count(node[@rel="dp"]) > 1 and node[@cat="np" and @rel="dp" and
    node[@pt="n" and @rel="hd"] and
    node[@cat="rel" and @rel="mod" and
        node[@pt="vnw" and @rel="rhd" and (@lemma="die" or @lemma="dat")] and
        node[@cat="ssub" and @rel="body" and
            node[@pt="ww" and @rel="hd"]]]]]"""

dp_np_rel_xpath = """./node[@cat="np" and @rel="dp" and
                            node[@pt="n" and @rel="hd"] and
                            node[@cat="rel" and @rel="mod"]
                            ]"""


def follows(node1: SynTree, node2: SynTree) -> bool:
    node2_end = gav(node2, 'end')
    node1_begin = gav(node1, 'begin')
    result = int(node1_begin) >= int(node2_end)
    return result

def transform_dp_dp_rel2avn(instree: SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    dp_dp_parents = stree.xpath(dp_dp_rel_avn_xpath)
    result = instree
    for dp_dp_parent in dp_dp_parents:
        dp_np = find1(dp_dp_parent, dp_np_rel_xpath)
        dp2s = [child for child in dp_dp_parent if child != dp_np and
                                                  gav(child, 'rel') == 'dp' and
                                                  follows(child, dp_np)]
        dp2 = dp2s[0] if dp2s != [] else None
        relclause = find1(dp_np, """./node[@cat="rel" and @rel="mod"]""")
        if dp2 is not None and relclause is not None:
            stree_tokens = getyield(stree)
            dp_np.remove(relclause)
            dp_np_tokens = getyield(dp_np)
            relclause_tokens = getyield(relclause)
            l_dp_np_tokens = len(dp_np_tokens)
            todo_tokens = stree_tokens[l_dp_np_tokens:]
            todo_str = space.join(todo_tokens)
            new_tree = settings.PARSE_FUNC(todo_str)
            treeinflate(new_tree, start=l_dp_np_tokens, inc=1)
            new_smain = find1(new_tree, './node[@cat="top"]/node[@cat="smain" ]')
            top_node = find1(stree, './node[@cat="top" and @rel="top"]')
            if new_smain is not None and top_node is not None:
                for child in top_node:
                    top_node.remove(child)
                du_node = etree.Element('node',
                                        {'cat':"du", 'rel': '--',
                                               'begin':gav(top_node, 'begin'),
                                               'end':gav(top_node, 'end')})
                new_smain.set('rel', 'nucl')
                dp_np.set('rel', 'sat')
                dp_np.set('end', str(l_dp_np_tokens))
                du_node.append(dp_np)
                du_node.append(new_smain)
                top_node.append(du_node)
                result = stree
            else:
                result = instree
        else:
            result = instree
    return result



wrong_sep_wws = ['uit_zijn', 'af_moeten']  # removed 'aan_gaan'
sep_ww_xpath = f""".//node[@pt="ww" and contains(@lemma,'_' )]"""
def transform_sep_ww(instree: SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    sep_wws = stree.xpath(sep_ww_xpath)
    for sep_ww in sep_wws:
        sep_ww_lemma = gav(sep_ww, 'lemma')
        if  sep_ww_lemma in wrong_sep_wws:
            particle_node = find1(sep_ww, '../node[@pt and @rel="svp"]')
            if particle_node is not None:
                sep_pos = sep_ww_lemma.index('_')
                newlemma = sep_ww_lemma[sep_pos + 1:]
                sep_ww.set('lemma', newlemma)
                particle_node.set('rel', 'ld')
    return stree


erazxpath = """.//node[@lemma="er" and ../node[@pt="vz" and @vztype="fin"]]"""
az_xpath = """.//node[@pt="vz" and @vztype="fin"]"""
def transform_er_az(instree: SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    er_az_nodes = stree.xpath(erazxpath)
    az_nodes = stree.xpath(az_xpath)
    for er_az_node in er_az_nodes:
        for az_node in az_nodes:
            if immediately_precedes(er_az_node, az_node, stree):
                er_az_parent = er_az_node.getparent()
                er_az_parent.remove(er_az_node)
                er_az_parent.remove(az_node)
                pp_node = etree.Element('node', {'cat': 'pp', 'rel': 'mod',
                                                 'begin': gav(er_az_node, 'begin'),'end': gav(az_node, 'end')})
                er_az_node.set('rel', 'obj1')
                pp_node.append(er_az_node)
                az_node.set('rel', 'hd')
                pp_node.append(az_node)
                er_az_parent.append(pp_node)
    return stree
