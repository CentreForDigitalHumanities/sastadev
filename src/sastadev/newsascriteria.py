import copy
from lxml import etree
import os
from sastadev.celexlexicon import getinflforms, pos2posnum
from sastadev.conf import settings
from sastadev.constants import outtreebanksfolder
from sastadev.lexicon import informlexicon, adj_no_pp_lexicon
from sastadev.macros import expandmacros
from sastadev.methods import Method
from sastadev.sas_filter import filterbymetadata
from sas_queries import get_message_with_word_function
from sastadev.sastatypes import ExactResultsDict, SynTree, TreeBank
from sastadev.stringfunctions import monosyllabic
from sastadev.treebankfunctions import (clausebodycats, find1, immediately_follows, getattval as gav, getnodeyield,
                                        getxsid, getmeta, getyield, iswordnode, nodecopy,
                                        adjacent, showtree, getbeginend)
from typing import List, Tuple

compoundsep = '_'
space = ' '

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

wrong_sep_wws = ['aan_gaan', 'uit_zijn']
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


inflate_start = 10
inflate_step = 10
getattval = gav

def treeinflate(stree: SynTree, start: int = inflate_start, inc: int = inflate_step) -> None:
    """
    The function *treeinflate* adapts the input tree *stree* in such a way that:

    * for word nodes: the int value of the *begin* attribute  (ib) is changed to str(newib = start + ib  *
    inc),
    and the value of the *end* attribute to str(newib + 1)
    * for phrasal nodes: new values for *begin* and *end* are computed by the function *getbeginend*
    * for other nodes: for newib the same as  for word nodes, ie is stanged into str(newie) with
     newie = start + (ie-1) * inc + 1

    The parameters of this function are:

    * stree: input syntactic structure, which is modified
    * start: int value of begin of the first word (default value inflate_start = 10)
    * inc: increment, (default value inflate_step = 10 )

    and it returns *None*. (it modifies the input tree)

    """
    # fatstree = deepcopy(stree)
    if stree is None:
        pass
    else:
        for child in stree:
            treeinflate(child, start, inc)
        children = [ch for ch in stree]
        if stree.tag == 'node':
            ib = int(getattval(stree, 'begin'))
            ie = int(getattval(stree, 'end'))
            # newib = (ib + 1) * 10
            newib = start + ib * inc
            newie = start + (ie-1) * inc + 1
            stree.attrib['begin'] = str(newib)
            if iswordnode(stree):
                stree.attrib['end'] = str(newib + 1)
            elif 'cat' in stree.attrib:
                (b, e) = getbeginend(children)
                stree.attrib['begin'] = b
                stree.attrib['end'] = e
            else:
                stree.attrib['begin'] = str(newib)
                stree.attrib['end'] = str(newie)





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




streestrings = {}
streestrings[0] = """
<alpino_ds version="1.3">
  <node begin="0" cat="top" end="7" id="0" rel="top">
    <node begin="0" cat="du" end="6" id="1" rel="--">
      <node begin="0" cat="np" end="3" id="2" rel="dp">
        <node begin="0" end="1" frame="proper_name(sg,'PER')" genus="zijd" getal="ev" graad="basis" id="3" lcat="np" lemma="Maartje" naamval="stan" neclass="PER" ntype="eigen" num="sg" pos="name" postag="N(eigen,ev,basis,zijd,stan)" pt="n" rel="hd" rnum="sg" root="Maartje" sense="Maartje" word="Maartje"/>
        <node begin="1" cat="rel" end="3" id="4" rel="mod">
          <node begin="1" case="no_obl" end="2" frame="rel_pronoun(de,no_obl)" gen="de" getal="getal" id="5" index="1" lcat="np" lemma="die" naamval="stan" pdtype="pron" persoon="persoon" pos="pron" postag="VNW(betr,pron,stan,vol,persoon,getal)" pt="vnw" rel="rhd" rnum="sg" root="die" sense="die" status="vol" vwtype="betr" wh="rel" word="die"/>
          <node begin="1" cat="ssub" end="3" id="6" rel="body">
            <node begin="1" end="2" id="7" index="1" rel="su"/>
            <node begin="2" end="3" frame="verb(hebben,sg,intransitive)" id="8" infl="sg" lcat="ssub" lemma="zitten" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="zit" sc="intransitive" sense="zit" tense="present" word="zit" wvorm="pv"/>
          </node>
        </node>
      </node>
      <node begin="3" cat="ap" end="6" id="9" rel="dp">
        <node aform="base" begin="3" buiging="zonder" end="4" frame="adjective(no_e(adv))" graad="basis" id="10" infl="no_e" lcat="ap" lemma="gewoonlijk" pos="adj" positie="vrij" postag="ADJ(vrij,basis,zonder)" pt="adj" rel="hd" root="gewoonlijk" sense="gewoonlijk" vform="adj" word="gewoonlijk"/>
        <node begin="4" cat="pp" end="6" id="11" rel="mod">
          <node begin="4" end="5" frame="preposition(op,[af,na])" id="12" lcat="pp" lemma="op" pos="prep" postag="VZ(init)" pt="vz" rel="hd" root="op" sense="op" vztype="init" word="op"/>
          <node begin="5" end="6" frame="noun(de,count,sg)" gen="de" genus="zijd" getal="ev" graad="basis" id="13" lcat="np" lemma="school" naamval="stan" ntype="soort" num="sg" pos="noun" postag="N(soort,ev,basis,zijd,stan)" pt="n" rel="obj1" rnum="sg" root="school" sense="school" word="school"/>
        </node>
      </node>
    </node>
    <node begin="6" end="7" frame="punct(punt)" id="14" lcat="punct" lemma="." pos="punct" postag="LET()" pt="let" rel="--" root="." sense="." special="punt" word="."/>
  </node>
  <sentence sentid="205">Maartje die zit gewoonlijk op school .</sentence>
<metadata>
<meta type="text" name="charencoding" value="UTF8" />
<meta type="text" name="childage" value="3;09.06" />
<meta type="int" name="childmonths" value="45" />
<meta type="date" name="date" value="1984-10-29" />
<meta type="text" name="location" value="NIE's home , Utrecht , Holland" />
<meta type="text" name="pid" value="11312/c-00022490-1" />
<meta type="text" name="session" value="TD30" />
<meta type="text" name="situation" value="looking	at photographs" />
<meta type="text" name="transcriber" value="Frank Wijnen , Herma Veenhof-Haan" />
<meta type="text" name="origutt" value="Maartje &lt;zit hier &amp;O (.)&gt; [//] die zit &lt;gewoon (.) uh (.)&gt; [/] gewoonlijk op school." />
<meta type="text" name="parsefile" value="Wijnen_TD30_u00000000205.xml" />
<meta type="text" name="speaker" value="FRA" />
<meta type="int" name="uttendlineno" value="310" />
<meta type="int" name="uttid" value="205" />
<meta type="int" name="uttstartlineno" value="310" />
<meta type="text" name="name" value="Frank" />
<meta type="text" name="SES" value="" />
<meta type="text" name="age" value="" />
<meta type="text" name="corpus" value="Wijnen" />
<meta type="text" name="custom" value="" />
<meta type="text" name="education" value="" />
<meta type="text" name="group" value="" />
<meta type="text" name="language" value="nld" />
<meta type="text" name="months" value="" />
<meta type="text" name="role" value="Father" />
<meta type="text" name="sex" value="" />
<meta type="int" name="uttno" value="205" />
</metadata>
</alpino_ds>
"""

strees = {i: etree.fromstring(streestring) for i, streestring in streestrings.items()}

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
    newtree = transform_dp_dp_rel2avn(tree)
    showtree(newtree)
    outtreefile = 'transformed_tree.xml'
    fullnewtree = etree.ElementTree(newtree)
    fullnewtree.write(outtreefile, encoding="UTF8", xml_declaration=False,
                       pretty_print=True)

def test2():
    for i, stree in strees.items():
        newtree = transform_dp_dp_rel2avn(stree)
        showtree(newtree)
        outtreefile = 'transformed_tree.xml'
        fullnewtree = etree.ElementTree(newtree)
        fullnewtree.write(outtreefile, encoding="UTF8", xml_declaration=False,
                           pretty_print=True)

def test3():
    datasetname = 'auristrain'
    samplename= 'TD27'
    inputpath = os.path.join(settings.DATAROOT, datasetname, outtreebanksfolder, 'trees', f'{samplename}_corrected')
    inputfilename = f'{samplename}_corrected_033.xml'   # 31 AND 33
    inputfullname = os.path.join(inputpath, inputfilename)
    fulltree = etree.parse(inputfullname)
    tree = fulltree.getroot()
    # avn_nodes = get_avn(tree)
    # for node in avn_nodes:
    #     print(node.attrib['word'], node.attrib['begin'])
    # newtree = transform_rel2avn(tree)
    # newtree = transform_adj_pp(tree)
    # newtree = transform_dp_dp_rel2avn(tree)
    newtree = transform_sep_ww(tree)
    showtree(newtree)
    outtreefile = 'transformed_tree.xml'
    fullnewtree = etree.ElementTree(newtree)
    fullnewtree.write(outtreefile, encoding="UTF8", xml_declaration=False,
                       pretty_print=True)


def get_plural(node: SynTree) -> List[str]:
    word = gav(node, 'word')
    lemma = gav(node, 'lemma')
    pt = gav(node, 'pt')
    dim = gav(node, 'graad') == 'dim'
    if pt != 'n':
        return []
    ncode = pos2posnum[pt]
    if dim:
        newwords = getinflforms(lemma, ncode, 'dm')
    else:
        newwords = getinflforms(lemma, ncode, 'm')
    return newwords

get_plural_test_list = [('beer', 'beer', 'basis'), ('beer', 'beertje', 'dim')]
def test4():
    for lemma, word, degree in get_plural_test_list:
        thenode = etree.Element('node', {'lemma': lemma, 'word': word, 'graad': degree, 'pt': 'n'})
        newwords = get_plural(thenode)
        print(f'{word}: {str(newwords)}')

def requires_plural_tw(node: SynTree) -> bool:
    lemma = gav(node, 'lemma')
    pt = gav(node, 'pt')
    result = pt == 'tw' and lemma != 'één'
    return result

if __name__ == '__main__':
    # test1()
    # test2()
    # test3()
    test4()