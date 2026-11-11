from typing import Callable, List, Optional, Tuple

from sastadev.asta_queries import asta_delpv
from sastadev.basicreplacements import is_pronominal_adverb, wrongmorph, ervzvariants, basicreplacements
from sastadev.celexlexicon import celex2dcoimap
from sastadev.conf import settings
from sastadev.CHAT_Annotation import (CHAT_replacement, CHAT_wordnoncompletion, CHAT_omittedword,
                                      CHAT_repetition, CHAT_retracing)
from sastadev.constants import false_start_mode, repetition_mode, self_correction_mode
from sastadev import correctionlabels
from sastadev.deregularise import correctinflection, overgen, wrongovergen
from sastadev.find_ngram import findmatches, ngram21
from sastadev.iedims import getjeforms
from sastadev.imperatives import wx, imperatives
from sastadev.lexicon import (dat_obj1_verbs, dat_su_verbs, vuwordslexicon, filledpauseslexicon, getwordinfo, getwordposinfo, informlexicon,
                              type_I_adj_n_pairs, known_pronunciation_variants, known_pronunciation_variants_map)
from sastadev.list_functions import pred
from sastadev.macros import expandmacros
from sastadev.metadata import Meta
from sastadev.missing_det import get_missing_det
from sastadev.normalise_lemma import normaliselemma
from sastadev.predcvagreement import get_predc_v_mismatching_heads
# from sastadev.sasta_explanation import get_prefix_and_core
from sastadev.sastatypes import SynTree, TreeBank, UttId, WordInfo
from sastadev.stringfunctions import endsinschwa, endsinschwa_n, is_t_elision, punctuationchars, relative_edit_distance
from sastadev.synsel import extend_syns, parent_imperative_xpath, synsel, tag_s_xpath
from sastadev.tblex import get_aanloop_and_core
from sastadev.toe import x_isnominal, x_is_nominal_phrase
from sastadev.treebankfunctions import (adjacent, complrels, compoundsep, find1,
                                        get_ww_dependent_verbs, get_left_siblings,
                                        getattval, get_next_word, get_node, getnodeyield, get_word, getuttid,
                                        indextransform, mdbasedquery,
                                        mdnameonlyxpathtemplate, parent, getsentence, getorigutt, getxsid,
                                        omitted_er_is_expletive, trueclausecats, find_omitted_phrase)

gav = getattval

comma = ','

relative_edit_distance_threshold = 0.4

articles = ['de', 'een', 'het', "'t", "'n"]

infl_error_xpath = f""".//xmeta[@name="{correctionlabels.morphologicalerror}" and 
                                (@value="{overgen}" or @value="{wrongovergen}")]"""

morph_error_xpath = f""".//xmeta[@name="{correctionlabels.morphologicalerror}" ]"""


nietxpath = './/node[@lemma="niet"]'
wordxpath = './/node[@pt]'

def_det_xpath = expandmacros("""./node[%definite_det%]""")
verb_no_pv_xpath = """.//node[@pt="ww" and (@wvorm!="pv") and @positie!="vrij" and not(ancestor::alpino_ds/descendant::node[@wvorm="pv"])
      and @rel != "vc" and not(@rel="hd" and parent::node[@rel="vc"]) and not(parent/parent::node[@cat="oti" and @rel="vc"])
]"""



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

verklxpath = expandmacros(""".//node[(@pt="n" and @graad="dim" and not(%nodimlemma%)) or %extradimlemma%]""")
verklsuffixes = ['je', 'jes', 'ie', 'ies', 'ke', 'kes']

sva_error_xpath = f""".//xmeta[@name="{correctionlabels.grammarerror}" and @value="{correctionlabels.svaerror}"]"""
regional_pv_variants = [('heb', 'heeft'), ('heb', 'hebt'),  ('hebt', 'heb')]  # heef/heeft is considered a uitspraak_variant
regular_pv_variants = [ ('wou', 'wilde'), ('wilde', 'wou')]
conditional_regular_pv_variants = [('kun', 'kan'), ('zul', 'zal')]
sociolect_variants = [('hun', 'zij')]
congruentie_error_pairs = [('kant', 'kan'), ('zalt', 'zal')]
# words that differ grammatically but have the same features in dcoi
basic_dcoi_gap_pairs = [('hebt', 'heeft'), ('ben', 'is')]
dcoi_gap_pairs = basic_dcoi_gap_pairs + [(el2, el1) for (el1, el2) in basic_dcoi_gap_pairs]

no_copula_xpath = """.//node[@rel="predc" and not(../node[@rel="hd" and @pt="ww"])]"""

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
            theleftsibling = None
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
    """

    :param stree: the syntactic structure to be analysed
    :param pred: a predicate that the results found must satisfy
    :return: a list of matching nodes

    The function *auxvobij* finds nodes that are found by the *voslashbijxpath* and selects from these those
    that satisfy the predicate *pred*. It is used to distinguish cases of R-pronoun + adposition that are *adjacent*
    (which should be analysed as TARSP *Vobij*) from those that are not adjacent (which should be analysed as TARSP
    Vo/Bij).

    .. autodata:: sastadev.queryfunctions::voslashbijxpath

    """
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
    lastlemma = getattval(nodeyield[-1], 'lemma') if nodeyield != [] else ''
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

potentialqwords = ['wat']
def firstwordispotentialqword(stree: SynTree) -> bool:
    nodeyield = getnodeyield(stree)
    firstnode = nodeyield[0] if nodeyield != [] else None
    if firstnode is None:
        return False
    else:
        firstnodelemma = gav(firstnode, 'lemma')
        result = firstnodelemma in potentialqwords
        return result

into_xpath = """.//node[@cat="top" and 
       (not(.//node[@pt="ww" and @wvorm!="pt"]) or not(.//node[@cat="sv1" and (@rel="--" or @rel="nucl" or @rel="dp")])) and 
       node[@lemma="?"] and 
       .//node[@pt!="let" and @pt != "tsw"] and
       not(.//node[@rel="tag" and @cat="sv1"]) and
       not(.//node[@cat="whq"]) and
       not(.//node[@pt="vnw" and (@vwtype="vrag" or @vwtype="vb")]) and
       not(.//node[@lemma="he" or @lemma="hè"]) and
       not(.//node[contains(@frame, "wh_adjective") or contains(@frame, "waar_adverb")]) and
       not(.//node[@lemma="huh"])

]

"""
def into(stree: SynTree) -> List[SynTree]:
    wordnodes = stree.xpath('.//node[@word]')
    wrongwordnodes = [wordnode for wordnode in wordnodes
                        if gav(wordnode, 'lemma').startswith('waar') and
                           is_pronominal_adverb(gav(wordnode,'lemma'))
                      ]
    if wrongwordnodes == []:
        rawintos = stree.xpath(into_xpath)
        result = [rawintos[0]] if rawintos != [] else []
    else:
        result = []
    if firstwordispotentialqword(stree):
        result = []
    return result

stamxpath = """.//node[@pt="ww" and @pvtijd="tgw" and
                       not(%verbal_VU%) and not(%Tarsp_Kop%) and
 not(%Tarsp_hww% or
     @lemma = "hebben" or
     @lemma = "worden" or
     @lemma = "zijn"   
  )
and @pvagr="ev"  ]"""
#  and not(parent::node[%basicimperative%]) eruit gehaald

expandedstamxpath = expandmacros(stamxpath)

def stam(stree: SynTree) -> List[SynTree]:
    results  = []
    coreresults = stree.xpath(expandedstamxpath)
    for result in coreresults:
        resultparent = result.getparent()
        imps = imperatives(resultparent)
        if imps == []:
            results.append(result)
    return results

bx_xpath = """.//node[%Tarsp_BX%]"""
expanded_bx_xpath = expandmacros(bx_xpath)

def bx(stree: SynTree) -> List[SynTree]:
    raw_bx_results = stree.xpath(expanded_bx_xpath)
    results = []
    for result in raw_bx_results:
        wxresults = wx(result)
        if wxresults == []:
            results.append(result)
    return results




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

ov2_xpath = expandmacros(".//node[%Tarsp_ov2%]")
def ov2(stree: SynTree) -> List[SynTree]:
    """
    many more cases must be excluded, e.g. w(x), bv zn. die/dezezn etc, allow only two real words
    """
    bx_results = bx(stree)
    wx_results = wx(stree)
    if bx_results != [] or wx_results != []:
        return []
    results = stree.xpath(ov2_xpath)
    return results

zn_xpath = expandmacros(".//node[%Tarsp_Zn%]")

def tarsp_dellid(stree: SynTree) -> List[SynTree]:
    raw_results = get_missing_det(stree)
    zn_results = stree.xpath(zn_xpath)
    results = [result for result in raw_results if result not in zn_results]
    return results


def tarsp_sublid(stree: SynTree) -> List[SynTree]:
    results = stap_sublid(stree)
    return results

def stap_sublid(stree: SynTree) -> List[SynTree]:
    results = sublid(stree)
    # no duplicates
    results = list(set(results))

    return results

def adj_agreement_errors(stree:SynTree) -> List[SynTree]:
    # adjectives incorrect e not needed dealt with by corrector + metadata
    # results2 = wrong_adj_e(stree)
    results1 = mdbasedquery(stree, correctionlabels.agreementerror, correctionlabels.incorrect_e_suffix)

    # add cases where an e-suffix is incorrectly absent @@todo
    results2 = adj_no_e_error(stree)

    results = results1 + results2

    #no duplicates
    results = list(set(results))
    return results



def sublid(stree: SynTree) -> List[SynTree]:

    # deheterror
    deheterror_nodes = mdbasedquery(stree, correctionlabels.grammarerror, correctionlabels.deheterror)

    # hetdeerrors

    hetdeerror_nodes = mdbasedquery(stree, correctionlabels.grammarerror, correctionlabels.hetdeerror)

    other_nodes = sub_pt(stree, 'lid')
    results = deheterror_nodes + hetdeerror_nodes + other_nodes
    return results

def stap_congruentiefout(stree: SynTree) -> List[SynTree]:
    results = congruentiefout(stree)
    return results

def congruentiefout(stree: SynTree) -> List[SynTree]:
    errors, _, _, _ = congruentie_afwijkingen(stree)
    return errors

def pv_regionale_vorm(stree: SynTree) -> List[SynTree]:
    _, regionals, _, _ = congruentie_afwijkingen(stree)
    return regionals

def pv_t_elisions(stree: SynTree) -> List[SynTree]:
    _, _, _, t_elisions = congruentie_afwijkingen(stree)
    return t_elisions


def sociolect(stree: SynTree) -> List[SynTree]:
    results = pv_regionale_vorm(stree)


    replacement_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_replacement))
    explanation_as_replacement_metadata = (
        stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.explanationasreplacement)))
    noncompletion_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_wordnoncompletion))
    regional_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.regionalform))
    all_metadata = replacement_metadata + explanation_as_replacement_metadata + \
                   noncompletion_metadata + regional_metadata
    for replacement in all_metadata:
        new_node = get_node(stree, replacement)
        annotated = get_word(replacement, 'annotatedwordlist')
        annotation = get_word(replacement, 'annotationwordlist')
        if new_node is not None:
            if (annotated, annotation) in sociolect_variants:
                results.append(new_node)

    # no duplicates
    results = list(set(results))

    # exclude t-elisions
    t_elisions = pv_t_elisions(stree)
    results = [n for n in results if n not in t_elisions]

    return results

def is_regular_pv_variant(annotated: str, annotation:str, theverb: SynTree) -> bool:
    if (annotated, annotation) in regular_pv_variants:
        return True
    if (annotated, annotation) in conditional_regular_pv_variants:
        thesubject = find1(theverb, '../node[@rel="su"]')
        if thesubject is None:
            return False
        thesubject_lemma = gav(thesubject, 'lemma')
        thesubject_beginint = int(gav(thesubject, 'begin'))
        theverb_beginint = int(gav(theverb, 'begin'))
        result = thesubject_lemma in ['je', 'jij'] and theverb_beginint < thesubject_beginint
        return result


def congruentie_afwijkingen(stree: SynTree) -> Tuple[List[SynTree], List[SynTree], List[SynTree], List[SynTree]]:
    errors = []
    regionals = []
    variants = []
    t_elisions = []

    # part 1 based on CHAT-replacements
    replacement_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_replacement))
    explanation_as_replacement_metadata = (
        stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.explanationasreplacement)))
    noncompletion_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_wordnoncompletion))
    all_metadata = replacement_metadata + explanation_as_replacement_metadata + noncompletion_metadata
    for replacement in all_metadata:
        new_node = get_node(stree, replacement, xpath_cond=f'@pt="ww"', annotation=True)
        annotated = get_word(replacement, 'annotatedwordlist')
        annotation = get_word(replacement, 'annotationwordlist')
        if new_node is not None:
            if (annotated, annotation) in regional_pv_variants:
                regionals.append(new_node)
                continue
            if is_regular_pv_variant(annotated, annotation, new_node) :
                variants.append(new_node)
                continue
            next_node = get_next_word(new_node)
            next_word = gav(next_node, 'word')
            if is_t_elision(annotated, annotation, next_word):
                t_elisions.append(new_node)
                continue
            if (annotated, annotation) in congruentie_error_pairs:
                errors.append(new_node)
                continue
            # if newnode is not a pv, then ignore
            new_node_wvorm = gav(new_node, 'wvorm')
            if new_node_wvorm != 'pv':
                continue
            # determine the grammatical properties of annotated if it is a real word
            if informlexicon(annotated):
                annotated_word_infos = getwordposinfo(annotated, pos='ww')
                annotation_word_infos = getwordposinfo(annotation, pos='ww')
                for annotated_word_info in annotated_word_infos:
                    # determine its lemma, check if it is the same as the lemma for the annotation
                    annotated_lemma = annotated_word_info[3]
                    for annotation_word_info in annotation_word_infos:
                        annotation_lemma =annotation_word_info[3]
                        normalised_annotated_lemma = normaliselemma(annotated, annotated_lemma)
                        if not lemmas_differ(normalised_annotated_lemma, annotation_lemma):
                            # check whether the grammatical properties only differ in pvagr
                            if (annotated, annotation) in dcoi_gap_pairs:
                                ok = True
                            else:
                                annotated_celex_infl = annotated_word_info[2]
                                annotation_celex_infl = annotation_word_info[2]
                                if annotated_celex_infl in celex2dcoimap and annotation_celex_infl in celex2dcoimap:
                                   annotated_infl = celex2dcoimap[annotated_celex_infl]
                                   annotation_infl = celex2dcoimap[annotation_celex_infl]
                                   ok = annotation_infl['wvorm'] == annotated_infl['wvorm'] and \
                                        annotation_infl['pvtijd'] == annotated_infl['pvtijd'] and \
                                        annotation_infl['pvagr'] != annotated_infl['pvagr']
                                else:
                                    ok = False
                                    settings.LOGGER.error(f'Missing value in celex2dcoimap: {annotated_celex_infl}.')
                            if ok:

                                errors.append(new_node)
                                break

    # part 2: svaerrors
    sva_error_metadata = stree.xpath(sva_error_xpath)
    for sva_error_meta in sva_error_metadata:
        new_node = get_node(stree, sva_error_meta)
        if new_node is not None:
            annotated = get_word(sva_error_meta, 'annotatedwordlist')
            annotation = get_word(sva_error_meta, 'annotationwordlist')

            if (annotated, annotation) in regional_pv_variants:
                regionals.append(new_node)
                continue
            if is_regular_pv_variant(annotated, annotation, new_node):
                variants.append(new_node)
                continue
            next_node = get_next_word(new_node)
            next_word = gav(next_node, 'word')
            if is_t_elision(annotated, annotation, next_word):
                t_elisions.append(new_node)
                continue

        if new_node is not None:
            errors.append(new_node)
    # part 3 based on mismatch between predc and verb

    predc_errors = get_predc_v_mismatching_heads(stree)
    errors.extend(predc_errors)

    # we do not want duplicate nodes
    errors = list(set(errors))
    regionals = list(set(regionals))
    variants = list(set(variants))
    t_elisions = list(set(t_elisions))

    return errors, regionals, variants, t_elisions




def vt_fout(stree: SynTree) -> List[SynTree]:
    overgen_nodes = get_overgeneralisations(stree)
    replacement_nodes = get_replacement_nodes(stree, with_noncompletion=False)
    wrong_nodes = overgen_nodes + replacement_nodes
    results = [node for node in wrong_nodes if gav(node, 'wvorm') == 'pv' and gav(node, 'pvtijd') == 'verl']
    return results

def vd_fout(stree: SynTree) -> List[SynTree]:
    morph_error_nodes = get_morphological_errors(stree)
    replacement_nodes = get_replacement_nodes(stree)
    wrong_nodes = morph_error_nodes + replacement_nodes
    results = [node for node in wrong_nodes if gav(node, 'wvorm') == 'vd' ]
    return results


def get_replacement_metadata(stree: SynTree, with_noncompletion=True) -> List[SynTree]:
    replacement_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_replacement))
    explanation_as_replacement_metadata = (
        stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.explanationasreplacement)))
    noncompletion_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_wordnoncompletion)) \
        if with_noncompletion else []
    all_metadata = replacement_metadata + explanation_as_replacement_metadata + noncompletion_metadata
    return all_metadata


def get_replacement_nodes(stree: SynTree, with_noncompletion=True) -> List[SynTree]:
    all_metadata = get_replacement_metadata(stree, with_noncompletion=with_noncompletion)
    raw_result = [get_node(stree, meta, annotation=True) for meta in all_metadata]
    result = [node for node in raw_result if node is not None]
    return result



def get_morphological_errors(stree: SynTree) -> List[SynTree]:
    errors = []
    morph_error_metadata = stree.xpath(morph_error_xpath)
    for morph_error_meta in morph_error_metadata:
        new_node = get_node(stree, morph_error_meta)
        if new_node is not None:
            errors.append(new_node)

    errors = list(set(errors))
    return errors


def get_overgeneralisations(stree: SynTree) -> List[SynTree]:
    errors = []

    # based on corrections by SASTA
    infl_error_metadata = stree.xpath(infl_error_xpath)
    for infl_error_meta in infl_error_metadata:
        new_node = get_node(stree, infl_error_meta)
        # annotated = get_word(stree, infl_error_meta, 'annotatedwordlist')
        # annotation = get_word(stree, infl_error_meta, 'annotationwordlist')

        if new_node is not None:
            errors.append(new_node)

    # based on replacements
    replacement_overgeneralisation_nodes = get_overgeneralisation_replacement_nodes(stree)
    errors += replacement_overgeneralisation_nodes

    # we do not want duplicate nodes
    errors = list(set(errors))

    return errors


def get_overgeneralisation_replacement_nodes(stree: SynTree) -> List[SynTree]:
    errors = []

    # based on CHAT-replacements
    all_metadata = get_replacement_metadata(stree)
    for replacement in all_metadata:
        annotated = get_word(replacement, 'annotatedwordlist')
        annotation = get_word(replacement, 'annotationwordlist')
        corrected_inflections = []
        if not informlexicon(annotated):
            raw_corrected_inflections = correctinflection(annotated)
            corrected_inflections = [ci for ci in raw_corrected_inflections if ci[0] == annotation]
        if corrected_inflections != []:
            new_node = get_node(stree, replacement, xpath_cond='', annotation=True)
            errors.append(new_node)

    # no duplicates
    errors = list(set(errors))
    return errors





def wrong_adj_e(stree: SynTree) -> List[SynTree]:
    uttid = getuttid(stree)
    results = []
    leaves = getnodeyield(stree)
    cleanleaves = [leave for leave in leaves if getattval(leave, 'word') not in filledpauseslexicon]
    cleanwordlist = [getattval(leave, 'word') for leave in cleanleaves]
    matches = findmatches(ngram21, cleanleaves)
    # matches = sipvjpvjsi(cleanleaves, tree)
    for match in matches:
        adj_node = cleanleaves[match[0]+1]
        if not valid_adj_e(adj_node):
            results.append(adj_node)
    return results

def valid_adj_e(stree: SynTree) -> bool:
    adj_rel = gav(stree, 'rel')
    adj_parent = stree.getparent()
    adj_parent_cat = gav(adj_parent, 'cat')
    if adj_parent_cat == 'np':
        np_node =adj_parent
    elif adj_parent_cat == 'ap' and adj_rel == 'hd':
        np_node = adj_parent.getparent()
    elif adj_parent_cat == 'mwu':
        np_node = adj_parent.getparent()
    else:
        np_node = None
    if np_node is None:
        return False
    result = is_definite_np(np_node)
    return result

def is_definite_np(node: SynTree) -> bool:
    node_cat = gav(node, 'cat')
    if node_cat != 'np':
        return False
    dets = node.xpath(def_det_xpath)
    result = dets != []
    return result


adj_no_e = """(@pt="adj" and @buiging="zonder" and @positie!="nom" and @graad!="sup")"""
def_np_parent = expandmacros("""(parent::node[@cat="np" and node[%definite_det%]])""")
adj_no_e_in_def_np_xpath = f""".//node[@rel="mod" and {adj_no_e} and
                                       {def_np_parent}
                                      ]"""
ap_no_e_in_def_np_xpath = f""".//node[@rel="hd" and {adj_no_e} and 
                                      parent::node[@cat="ap" and @rel="mod" and {def_np_parent}]
                                      ]"""


def get_adj_n_pair(adj: SynTree) -> Tuple[str,str]:
    result = ('', '')
    adj_word = gav(adj, 'word')
    adj_parent = adj.getparent()
    adj_parent_cat = gav(adj_parent, 'cat')
    if adj_parent_cat == 'np':
        np_node = adj_parent
    elif adj_parent_cat == 'ap':
        np_node = adj_parent.getparent()
    else:
        np_node = None
    if np_node is not None:
        n_node = find1(np_node, './node[@rel="hd"]')
        if n_node is not None:
            n_word = gav(n_node, 'word')
            result = (adj_word, n_word)
    return result



def adj_no_e_error(stree: SynTree) -> List[SynTree]:
    cand_adjs1 = stree.xpath(adj_no_e_in_def_np_xpath)
    cand_adjs2 = stree.xpath(ap_no_e_in_def_np_xpath)
    cand_adjs = cand_adjs1 + cand_adjs2
    adjs = [cand_adj for cand_adj in cand_adjs
                if not endsinschwa_n(gav(cand_adj, 'word')) and
                   not endsinschwa(gav(cand_adj, 'word'))]
    results = [adj for adj in adjs if get_adj_n_pair(adj) not in type_I_adj_n_pairs]


    return results


def ww_pred_agr_error(stree: SynTree) -> List[SynTree]:
    results = mdbasedquery(stree, correctionlabels.agreementerror, correctionlabels.predc_v_agreement_error)
    return results

def regional_dim(stree: SynTree) -> List[SynTree]:
    results = mdbasedquery(stree, correctionlabels.regionalform, correctionlabels.iedim)
    return results

def regional_case_form(stree: SynTree) -> List[SynTree]:
    results = mdbasedquery(stree, correctionlabels.regionalform, correctionlabels.casevariant)
    return results

def wrong_morphology(stree: SynTree) -> List[SynTree]:
    results = mdbasedquery(stree, wrongmorph)
    return results



def verb_no_pv(stree: SynTree) -> List[SynTree]:
    results = stree.xpath(verb_no_pv_xpath)
    return results

def no_copula(stree: SynTree) -> list[SynTree]:
    results = stree.xpath(no_copula_xpath)
    return results


def is_iedim(word: str, replacement: str) -> bool:
    je_forms = getjeforms(word)
    result = replacement in je_forms
    return result


def test_iedims():
    test_pairs = [('kersie', 'kersje'), ('kleppie', 'klepje')]
    for word, replacement in test_pairs:
        ok = is_iedim(word, replacement)
        print(f'{word}: {ok}')

def er_replacement(word:str) -> bool:
    result = word in ervzvariants
    return result

def missing_er(word:str, replacement:str) -> bool:
    result = f'er{word}' == er_replacement
    return result

def sub_vz(stree: SynTree) -> List[SynTree]:
    results = sub_pt(stree, 'vz')
    return results

def overige_fouten(stree: SynTree) -> int:
# helemaal herformuleren als een post query
    errors = []

    errors += sub_vz(stree)

    result = 1 if errors != [] else 0
    return result


def sub_pt(stree: SynTree, pt: str, cond: Callable = lambda x: True) -> List[SynTree]:
    """
    finds substitutions of words where replacement and replacee have  part of speech == pt in stree
    It finds them on the basis of the metadata
    """
    results = []
    replacement_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_replacement))
    explanation_as_replacement_metadata = (
        stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.explanationasreplacement)))
    all_metadata = replacement_metadata + explanation_as_replacement_metadata
    pt_replacement_metadata = []
    for replacement in all_metadata:
        annotated_list = eval(gav(replacement, 'annotatedwordlist'))
        annotation_list = eval(gav(replacement, 'annotationwordlist'))
        annotationpos_list = eval(gav(replacement, 'annotationposlist'))
        annotation_begin = str(annotationpos_list[0])
        annotated_word = annotated_list[0] if annotated_list else None
        if not informlexicon(annotated_word):   # to avoid simple wrong pronunciations
            continue
        annotation_node = find1(stree, f'.//node[@word and @begin="{annotation_begin}"]')
        annotation_pt = gav(annotation_node, 'pt')
        annotated_wordinfos = []
        for annotated in annotated_list:
            annotated_wordinfos += getwordposinfo(annotated, pt)
        if annotated_wordinfos != [] and annotation_pt == pt:
            pt_replacement_metadata.append(replacement)
    for pt_replacement in pt_replacement_metadata:
        new_node = get_node(stree, pt_replacement, xpath_cond=f'@pt="{pt}"', annotation=True)
        if new_node is not None and cond(new_node):
            results.append(new_node)
    return results

def omitted_pt(stree: SynTree, pt: str,
               omitted_cond: Callable = lambda meta: True,
               associate_cond: Callable = lambda meta: True) -> List[SynTree]:
    """
    finds omitted words with part of speech = pt in stree, based on the CHAT metadata
    """
    results = []
    omitted_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_omittedword))
    associate_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.omitted_node_associate))
    for omitted_meta in omitted_metadata:
        if not omitted_cond(omitted_meta):
            continue
        associates = [associate_meta for associate_meta in associate_metadata
                      if gav(associate_meta, 'annotationposlist') == gav(omitted_meta, 'annotatedposlist') and
                      gav(associate_meta,'omitted_pt') == pt and associate_cond(associate_meta)]
        associate = associates[0] if associates else None
        if associate is not None:
            new_node = get_node(stree, associate, annotation=False)
            if new_node is not None:
                results.append(new_node)
    return results

def del_vz(stree: SynTree) -> List[SynTree]:
    results = omitted_pt(stree, 'vz')
    return results

def del_bw(stree: SynTree) -> List[SynTree]:
    results = omitted_pt(stree, 'bw')
    results += omitted_pt(stree, 'adj', associate_cond= lambda meta: is_meta_for_omitted_adverbial_word(meta))
    return results

def sub_bw(stree: SynTree) -> List[SynTree]:
    results = sub_pt(stree, 'bw')
    results += sub_pt(stree, 'adj', cond= lambda x: is_adverbial_word(x))
    return results

def sub_vnw(stree: SynTree) -> List[SynTree]:
    results = sub_pt(stree, 'vnw')
    return results

def sub_vg(stree: SynTree) -> List[SynTree]:
    results = sub_pt(stree, 'vg')
    return results

def del_vg(stree: SynTree) -> List[SynTree]:
    results = omitted_pt(stree, 'vg')
    return results


def del_er(stree: SynTree) -> List[SynTree]:
    results = omitted_pt(stree, 'vnw', omitted_cond=lambda meta: eval(gav(meta, 'annotationwordlist')) == ['er'])
    newresults = omitted_expletive_er(stree)
    results += newresults
    return results

def is_meta_for_omitted_adverbial_word(meta: SynTree) -> bool:
    meta_pt = gav(meta, 'omitted_pt')
    meta_rel = gav(meta, 'omitted_rel')
    if meta_pt == 'bw':
        return True
    elif meta_pt == 'adj' and meta_rel == "mod":  # except when it occurs in a NP
        return True
    elif meta_pt == 'adj' and meta_rel not in ['hd', 'predc']:
        return True
    else:
        return False


def is_adverbial_word(node: SynTree) -> bool:
    node_pt = gav(node, 'pt')
    node_rel = gav(node, 'rel')
    node_parent = node.getparent()
    node_parent_cat = gav(node_parent, 'cat')
    node_parent_rel = gav(node_parent, 'rel')
    node_grandparent = node_parent.getparent()
    node_grandparent_cat = gav(node_grandparent, 'cat')
    if node_pt == 'bw':
        return True
    elif node_pt == 'adj' and node_rel == "mod" and node_parent_cat not in ['np']:  # except when it occurs in a NP
        return True
    elif node_pt == 'adj' and node_rel not in ['hd', 'predc']:
        return True
    elif node_pt == 'adj' and node_rel in ['hd'] and node_grandparent_cat not in ['np']:
        return True
    elif node_pt == 'adj' and node_rel in ['hd'] and node_parent_rel not in ['predc']:
        return True
    else:
        return False



def get_lemma_nodes(stree: SynTree, lemmas: List[str]) -> List[SynTree]:
    xpath_conds1 = [f'@original_lemma ="{lemma}"' for lemma in lemmas]
    xpath_cond1 = f"@original_lemma and ({' or '.join(xpath_conds1)})"
    nodes1 = stree.xpath(f'.//node[{xpath_cond1}]')
    xpath_conds2 = [f'@lemma ="{lemma}"' for lemma in lemmas]
    xpath_cond2 = f"@lemma and ({' or '.join(xpath_conds2)})"
    nodes2 = stree.xpath(f'.//node[{xpath_cond2}]')

    nodes = nodes1 + nodes2
    # no duplicates
    nodes = list(set(nodes))
    return nodes

def dan_toen_fout(stree: SynTree) -> List[SynTree]:
    """
    Certain subordinate conjunctions must occur with past or perfect tenses, others cannot co-occur
    with past or perfect tense.

    * combines with past or perfect only: *toen*
    * combines with not(past or perfect) only:  *als*, *dan*, and *wanneer*.

    The words "wanneer" and "als" (in the meaning of "wanneer" can occur with past tense in the adults' language,
    but this involves generic statements that young children do not yet make.

    In a als...dan construction, both als and dan can occur with past and perfect tenses, so we exclude these.
    """
    results = []
    dan_nodes = get_lemma_nodes(stree, ["dan", "als", "wanneer"])
    for dan_node in dan_nodes:
        clause = get_dan_toen_clause(dan_node)
        if clause is not None and not is_als_dan(dan_node) and is_past_or_perfect(clause):
            results.append(dan_node)
    toen_nodes = get_lemma_nodes(stree, ["toen"])
    for toen_node in toen_nodes:
        clause = get_dan_toen_clause(toen_node)
        if clause is not None and  not is_past_or_perfect(clause):
            results.append(toen_node)
    return results

def has_corresponding_node(node, lemma, nodeyield, right=True) -> bool:
    result = False
    for ctr, n in enumerate(nodeyield):
        if n == node:
            if right:
                result = any([gav(nd, 'lemma') == lemma for nd in nodeyield[ctr+1:]])
            else:
                result = any([gav(nd, 'lemma') == lemma for nd in nodeyield[:ctr]])
    return result


def is_als_dan(node: SynTree) -> bool:
    result = False
    top_node = find1(node, 'ancestor::alpino_ds')
    if top_node is None:
        return False
    nodeyield = getnodeyield(top_node)
    node_lemma = gav(node, 'lemma')
    if node_lemma == 'als':
        result = has_corresponding_node(node, 'dan', nodeyield, right=True)
    elif node_lemma == 'dan':
        result = has_corresponding_node(node, 'als', nodeyield, right=False)
    return result

def get_dan_toen_clause(dan: SynTree) -> Optional[SynTree]:
    dan_parent = dan.getparent()
    dan_parent_cat = gav(dan_parent, 'cat')
    dan_pt = gav(dan, 'pt')
    dan_rel = gav(dan, 'rel')
    sister_cp = find1(dan, '../node[@cat="ssub" or @cat="cp"]' )
    if dan_parent_cat == 'advp' and sister_cp is not None:
        result = sister_cp
    elif dan_pt == 'vg' and sister_cp is not None:
        result = sister_cp
    elif dan_rel == 'rhd' and sister_cp is not None:
        result = sister_cp
    elif dan_pt == 'bw':
        result = get_finite_ancestor(dan)
    else:
        result = None
    return result

def get_finite_ancestor(node: SynTree) -> Optional[SynTree]:
    node_parent = node.getparent()
    if node_parent is None:
        return None
    pv = find1(node_parent, './node[@pt="ww" and @wvorm="pv"]')
    if pv is None:
        result = get_finite_ancestor(node_parent)
        return result
    else:
        return node_parent

def is_past_or_perfect(stree: SynTree) -> bool:
    thehead = find1(stree, './node[@rel="hd"]')
    head_tense = gav(thehead, 'pvtijd')
    head_lemma = gav(thehead, 'lemma')
    vc_ppart = find1(stree, './node[@rel="vc" and @cat="ppart" ]')
    if head_tense == 'verl':
        return True
    elif head_lemma in ['hebben', 'zijn'] and vc_ppart is not None:
        return True
    else:
        return False

def sub_tijd(stree: SynTree) -> List[SynTree]:
    results = []
    replacement_metadata = get_replacement_metadata(stree)
    for replacement_meta in replacement_metadata:
        annotated_list = eval(gav(replacement_meta, 'annotatedwordlist'))
        annotation_list = eval(gav(replacement_meta, 'annotationwordlist'))
        if len(annotation_list) > 1:
            continue
        annotated = annotated_list[0]
        if not informlexicon(annotated):
            continue
        annotation = annotation_list[0]
        annotated_node = get_node(stree, replacement_meta, annotation=True)
        annotated_pt = gav(annotated_node, 'pt')
        if annotated_pt != 'ww':
            continue
        annotated_pvtijd = gav(annotated_node, 'pvtijd')
        annotation_wordinfos = getwordposinfo(annotation, annotated_pt)
        replacement_results = []
        for annotation_wordinfo in annotation_wordinfos:
            infl = annotation_wordinfo[2]
            annotation_featdict = celex2dcoimap[infl] if infl in celex2dcoimap else {}
            annotation_pvtijd = annotation_featdict['pvtijd'] if 'pvtijd' in annotation_featdict else ''
            if annotation_wordinfo[0] == annotated_pt and \
                annotation_pvtijd != '' and \
                annotated_pvtijd != '' and \
                annotation_pvtijd != annotated_pvtijd:
                replacement_results = [annotated_node]
            if annotation_wordinfo[0] == annotated_pt and \
                annotation_pvtijd != '' and \
                annotated_pvtijd != '' and \
                annotation_pvtijd == annotated_pvtijd:
                replacement_results = []
                break
        results.extend(replacement_results)


    return results

def get_base_lemma(lemma: str) -> str:
    lemma_parts = lemma.split(compoundsep)
    result = lemma_parts[-1]
    return result

def lemmas_differ(lemma1:str, lemma2:str) -> bool:
    lemma1_parts = lemma1.split(compoundsep)
    lemma2_parts = lemma2.split(compoundsep)
    if len(lemma1_parts) == 1 and  len(lemma2_parts) > 1:
        result = lemma1 != lemma2_parts[-1]
    elif len(lemma1_parts) > 1 and  len(lemma2_parts) == 1:
        result = lemma2 != lemma1_parts[-1]
    else:
        result = lemma1 != lemma2
    return result

lexical_error_pts = ['n', 'adj', 'ww', 'bw']
# next now imported from lexicon as a set
# known_pronunciation_variants = [('boon', 'gewoon'), ('doe', 'toen'),('es', 'eens'),
#                                 ('gun', 'ging'), ('his', 'wist'), ('me', 'maar'), ('na', 'dan'),
#                                 ('sas', 'zag'), ('teek', 'betekent'), ('tof', 'toch'), ('wa', 'had')]
def sub_lexical(stree: SynTree) -> List[SynTree]:
    results = []
    replacement_metadata = get_replacement_metadata(stree, with_noncompletion=False)
    for replacement_meta in replacement_metadata:
        annotated_list = eval(gav(replacement_meta, 'annotatedwordlist'))
        annotation_list = eval(gav(replacement_meta, 'annotationwordlist'))
        annotated = annotated_list[0]
        annotation = annotation_list[0]
        # exclude uninterpreable speech codes
        if annotated in ['x', 'xx', 'xxx']:
            continue
        # exclude dan/toen
        if (annotated, annotation) in [('dan', 'toen'), ('toen', 'dan')]:
            continue
            # try basicreplacements voor annotated and check again vklstap  STAP_02, 22 dee/was
        if not informlexicon(annotated):
            if annotated in basicreplacements:
                annotated = basicreplacements[annotated][0][0] if basicreplacements[annotated][0] != [] else annotated
            else:
                continue
        # exclude pronunciation variants
        if is_pronunciation_variant(annotated, annotation):
            continue
        annotated_node = get_node(stree, replacement_meta, annotation=True)
        annotated_pt = gav(annotated_node, 'pt')
        annotated_lemma = gav(annotated_node, 'original_lemma')
        annotation_lemma = gav(annotated_node, 'lemma')
        if (annotated_lemma != '' and annotation_lemma != '' and
                lemmas_differ(annotation_lemma, annotated_lemma) and annotated_pt in lexical_error_pts):
            results.append(annotated_node)
    return results

def is_pronunciation_variant(annotated:str, annotation:str) -> bool:
    # realword1 = informlexicon(annotated)
    # realword2 = informlexicon(annotation)
    # if realword1 and not realword2:
    #     return True
    # if not realword1 and realword2:
    #     return True
    # next includes cases of noncompletion of a word
    if annotated in ['x', 'xx', 'xxx']:
        return False
    len_diff_ok = abs(len(annotation) - len(annotated)) <= min(len(annotation), len(annotated)) # to exclude tik/tikkertje
    if len_diff_ok  and (annotated in annotation or annotation in annotated):
        return True
    if (annotated, annotation) in known_pronunciation_variants:
        return True
    if relative_edit_distance(annotated, annotation) < relative_edit_distance_threshold:
        return True
    return False

def select_wordinfos(word_infos, criterion: Callable) -> List[WordInfo]:
    results = []
    for word_info in word_infos:
        infl = word_info[2]
        props = celex2dcoimap[infl]
        if criterion(props):
            results.append(word_info)
    return results

def is_past_tense(props) -> bool:
    result = ('pt' in props and props['pt'] == 'ww' and
              'pvtijd' in props and props['pvtijd'] == 'verl' )
    return result

def vt_fout(stree: SynTree) -> List[SynTree]:
    results = []
    raw_overgen_nodes = get_overgeneralisations(stree)
    overgen_nodes = [nd for nd in raw_overgen_nodes if gav(nd, 'pvtijd') == 'verl']
    results += overgen_nodes
    replacement_metadata = get_replacement_metadata(stree, with_noncompletion=False)
    for replacement_meta in replacement_metadata:
        annotated_list = eval(gav(replacement_meta, 'annotatedwordlist'))
        annotation_list = eval(gav(replacement_meta, 'annotationwordlist'))
        annotated = annotated_list[0]
        annotation = annotation_list[0]
        annotated_node = get_node(stree, replacement_meta, annotation=True)
        annotated_pt = gav(annotated_node, 'pt')
        annotated_tijd = gav(annotated_node, 'pvtijd')
        annotated_pvagr = gav(annotated_node, 'pvagr')
        annotated_lemma = gav(annotated_node, 'original_lemma')
        annotation_lemma = gav(annotated_node, 'lemma')
        if annotated_pt != "ww":
            continue
        annotation_wordinfos = getwordposinfo(annotation, 'ww')
        if not informlexicon(annotated):
            if annotated in basicreplacements:
                annotated = basicreplacements[annotated][0][0] if basicreplacements[annotated][0] != [] else annotated
            else:
                continue
        # if the annotated word is an existing verb form, it is not a vt_fout
        # but an alternative form (wou/wilde), a different person/number (wou/wouden),
        # an ov:sub_tijd (viel/valt) or sub_lexical (was/ging), or identical (dee->deed/deed)
        if informlexicon(annotated) and annotation_wordinfos != []:
            continue
        # the next is covered by the preceding and therefore put in comments
        # # exclude correct different past forms of the same lemma: # to exclude wou /wouden STAPVoorbeeld10042026, 39
        # relevant_wordinfos = select_wordinfos(annotation_wordinfos,
        #                 lambda wi: not is_past_tense(wi) )
        # if relevant_wordinfos != []:
        #     continue
        # if annotated_pt != 'ww' or annotated_tijd != 'verl':
        #     continue
        # exclude uninterpreable speech codes
        if annotated in ['x', 'xx', 'xxx']:
            continue
        # next notrelevant for verbs
        # # exclude dan/toen
        # if (annotated, annotation) in [('dan', 'toen'), ('toen', 'dan')]:
        #     continue
            # try basicreplacements voor annotated and check again vklstap  STAP_02, 22 dee/was
        # exclude pronunciation variants
        if is_pronunciation_variant(annotated, annotation):
            continue
        results.append(annotated_node)

    return results

alpino_replacements_lexicon = {('me', 'mijn')}
def get_alpino_replacements(stree: SynTree) -> List[SynTree]:
    results = []
    word_nodes = stree.xpath('.//node[@word]')
    for word_node in word_nodes:
        word = gav(word_node, 'word')
        lemma = gav(word_node, 'lemma')
        if (word, lemma) in alpino_replacements_lexicon:
            results.append(word_node)
    return results

def get_known_pronunciation_variants_nodes(stree: SynTree) -> List[SynTree]:
    results = []
    word_nodes = stree.xpath('.//node[@word]')
    for word_node in word_nodes:
        word = gav(word_node, 'word')
        if word in known_pronunciation_variants_map and not informlexicon(word):
            results.append(word_node)
    return results


def get_pronunciation_variants(stree: SynTree) -> List[SynTree]:
    results = []
    informal_pronunciation_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.informalpronunciation))
    pronunciation_variant_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.pronunciationvariant))
    all_pronunciation_variant_metadata = informal_pronunciation_metadata + pronunciation_variant_metadata
    for ipm in all_pronunciation_variant_metadata:
        ipm_node = get_node(stree, ipm)
        if ipm_node is None:
            annotated, annotation = get_meta_pair(ipm)
            report_missing_node(stree, annotated, annotation)
        else:
            results.append(ipm_node)

    # alpino replacements
    alpino_replacements = get_alpino_replacements(stree)
    results.extend(alpino_replacements)

    overgeneralisation_nodes = get_overgeneralisation_replacement_nodes(stree)
    # SASTA noncompletion
    noncompletion_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.noncompletion))
    for ncm in noncompletion_metadata:
        if have_same_lemma(ncm, annotation=False):
            continue
        annotated, annotation = get_meta_pair(ncm)
        annotated_node = get_node(stree, ncm, annotation=False)
        if annotated_node in overgeneralisation_nodes:
            continue
        if annotated_node is None:
            report_missing_node(stree, annotated, annotation)
        elif is_pronunciation_variant(annotated, annotation):
            results.append(annotated_node)


    # known pronunciation variants of which the original string is not a valid word
    new_results = get_known_pronunciation_variants_nodes(stree)
    results.extend(new_results)

    # CHAT noncompletion
    noncompletion_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=CHAT_wordnoncompletion))
    for ncm in noncompletion_metadata:
        if have_same_lemma(ncm, annotation=False):
            continue
        if is_vd_morph_error(ncm, annotation=False):
            continue
        annotated, annotation = get_meta_pair(ncm)
        annotated_node = get_node(stree, ncm, annotation=False)
        if annotated_node in overgeneralisation_nodes:
            continue
        if annotated_node is None:
            report_missing_node(stree, annotated, annotation)
        elif  is_pronunciation_variant(annotated, annotation):
            results.append(annotated_node)



    # replacements that are pronunciation variants
    raw_replacement_metadata = get_replacement_metadata(stree, with_noncompletion=False)
    replacement_metadata = []
    for replacement_meta in raw_replacement_metadata:
        if have_same_lemma(replacement_meta, annotation=True):
            continue
        if is_vd_morph_error(replacement_meta, annotation=True):
            continue
        annotated, annotation = get_meta_pair(replacement_meta)
        annotated_node = get_node(stree, replacement_meta, annotation=True)
        if annotated_node in overgeneralisation_nodes:
            continue
        if annotated_node is None:
            report_missing_node(stree, annotated, annotation)
        elif is_pronunciation_variant(annotated, annotation):
            results.append(annotated_node)

    # add basic replacements that are informal pronunciations
    basic_replacement_metadata = stree.xpath('.//xmeta[@cat="{basicreplacements.pron}"]')
    for brm in basic_replacement_metadata:
        nd = get_node(stree, brm)
        if nd is None:
            annotated, annotation = get_meta_pair(brm)
            report_missing_node(stree, annotated, annotation)
        else:
            results.append(nd)

    # do something for contractions? ???

    # exclude congruentie_fouten
    agreement_errors = congruentiefout(stree)
    results = [result for result in results if result not in agreement_errors]

    # no duplicates
    results = list(set(results))

    return results

def report_missing_node(stree: SynTree, annotated: str, annotation: str) -> None:
    origutt = getorigutt(stree)
    sentence = getsentence(stree)
    uttid = getxsid(stree)
    settings.LOGGER.error(
        f'Node not found for ({annotated}, {annotation}) in utterance {uttid}:\nsentence: {sentence}\norigutt:  {origutt}')


def get_meta_pair(meta: SynTree) -> Tuple[str, str]:
    annotated_list = eval(gav(meta, 'annotatedwordlist'))
    annotation_list = eval(gav(meta, 'annotationwordlist'))
    annotated = annotated_list[0] if annotated_list != [] else ''
    annotation = annotation_list[0] if annotation_list != [] else ''
    return annotated, annotation


def is_vd_morph_error(meta: SynTree, annotation=False) -> bool:
    stree = find1(meta, 'ancestor::alpino_ds')
    annotated, annotation = get_meta_pair(meta)
    annotated_node = get_node(stree, meta, annotation=annotation)
    if annotated_node is not None:
        annotated, annotation = get_meta_pair(meta)
        annotated_pt = gav(annotated_node, 'pt')
        annotated_lemma = gav(annotated_node, 'lemma')
        annotated_wvorm = gav(annotated_node, 'wvorm')
        annotated_word = gav(annotated_node, 'word')
        normalised_lemma = normaliselemma(annotated_word, annotated_lemma)
        if annotated_wvorm == 'vd':
            annotation_wordinfos = getwordposinfo(annotation, annotated_pt)
            result = annotation_wordinfos == [] or any([wordinfo[3] == normalised_lemma for wordinfo in annotation_wordinfos])
        else:
            result = False
    else:
        result = False
    return result


def get_annotated_lemma(meta: SynTree, pt: str) -> str:
    annotated_list = eval(gav(meta, 'annotatedwordlist'))
    annotated = annotated_list[0] if annotated_list != [] else ''
    wordinfos = getwordposinfo(annotated, pt)
    result = wordinfos[0][3] if wordinfos != [] else None
    return result

def have_same_lemma(meta: SynTree, annotation=False) -> bool:
    stree = find1(meta, 'ancestor::alpino_ds')
    annotated, annotation = get_meta_pair(meta)
    annotated_node = get_node(stree, meta, annotation=annotation)
    if annotated_node is not None:
        annotated, annotation = get_meta_pair(meta)
        annotated_pt = gav(annotated_node, 'pt')
        annotation_word_list = eval(gav(meta, 'annotationwordlist'))
        if len(annotation_word_list) > 1:
            return False
        annotated_lemma = None
        if 'original_lemma' in annotated_node.attrib:
            original_lemma = gav(annotated_node, 'original_lemma')
            lemma = gav(annotated_node, 'lemma')
            if lemma != original_lemma:
                return False
                # annotated_lemma = original_lemma
            else:
                annotated_lemma = get_annotated_lemma(meta, annotated_pt)
        if annotated_lemma is None:
            annotated_lemma = gav(annotated_node, 'word')
        annotation_wordinfos = getwordposinfo(annotation, annotated_pt)
        result = any([not lemmas_differ(wordinfo[3], annotated_lemma) for wordinfo in annotation_wordinfos])
    else:
        result = False
    return result


def is_3p_sg(node: SynTree) -> bool:
    pvagr = gav(node, 'pvagr')
    pvtijd = gav(node, 'pvtijd')
    word = gav(node, 'word')
    result = word in ['kan', 'wil', 'mag', 'heeft', 'is'] and word not in ['hebt', 'bent']
    if not result:
        result = pvagr != 'mv' and (not(pvagr=='ev' and pvtijd == 'tgw') or word[-1] == 't')
    return result

def is_topic_drop_verb(hd: SynTree, include_subjects=False) -> bool:
    ww_lemma = gav(hd, 'lemma')
    parent = hd.getparent()
    obj1 = find1(parent, 'node[@rel="obj1"]')
    su = find1(parent, 'node[@rel="su"]')
    vc = find1(parent, 'node[@rel="vc"]')
    vc_head = find1(vc, 'node[@rel="hd"]') if vc is not None else None
    vc_head_lemma = gav(vc_head, 'lemma')
    cond1 = obj1 is None and su is not None and vc is None and ww_lemma in dat_obj1_verbs
    cond2 = su is None and vc is None and ww_lemma in dat_su_verbs and is_3p_sg(hd) if include_subjects else False
    cond3 = su is None and ww_lemma in dat_su_verbs and vc_head_lemma in dat_su_verbs and is_3p_sg(hd) \
        if include_subjects else False

    topic_drop_found = cond1 or cond2 or cond3
    return topic_drop_found


def is_dp_dp_sv1(node: SynTree) -> bool:
    """
    determines whether dp/sv1 node us immediately preceded by a dp/ node
    """
    node_rel = gav(node, 'rel')
    node_cat = gav(node, 'cat')
    node_parent = node.getparent()
    node_siblings = sorted([n for n in node_parent], key = lambda n: int(gav(n, 'begin')))
    node_pred = pred(node, node_siblings)
    node_pred_rel = gav(node_pred, 'rel')
    result = node_cat == 'sv1' and node_rel == 'dp' and node_pred is not None and node_pred_rel == 'dp'
    return result

def is_declarative(node: SynTree) -> bool:
    declarative_clauses = node.xpath(expandmacros('self::node[%declarative%]'))
    result = node in declarative_clauses
    return result

sv1_topic_drop_xpath = expandmacros('.//node[@cat="sv1" and @rel!="body" and %declarative%]')

def get_main_clause(verb:SynTree) -> Optional[SynTree]:
    clause_found = False
    cur_node = verb
    while not clause_found:
        if cur_node is not None:
            cand = cur_node.getparent()
        else:
            return None
        cur_node = cand
        clause_found = True
        cand_cat = gav(cand, 'cat')
        cand_rel = gav(cand, 'rel')
        if cand_cat in trueclausecats:
            clause_found = True
        if ((cand_cat == 'smain' and cand_rel == '--') or         # condition on rel becasue smain with rel=nucl
                                                                  # preceded by dlink vg must be excluded
            (cand_cat == 'sv1' and cand_rel != 'body')):
            result = cand
        else:
            result = None
        cur_node =cand
    return result

def topic_drop(stree: SynTree) -> List[SynTree]:
    results = []
    # case 1:  declarative and v.sentype = topicdrop or no obj1 or vc but su and verb transitive

    nodeyield = getnodeyield(stree)

    verbs = stree.xpath('.//node[@rel="hd" and @pt="ww"]')
    for verb in verbs:
        main_clause = get_main_clause(verb)
        if main_clause is None:
            continue
        if not is_declarative(main_clause):
            continue
        if is_dp_dp_sv1(main_clause):
            continue
        main_clause_cat = gav(main_clause, 'cat')
        main_clause_rel = gav(main_clause, 'rel')
        if main_clause_cat == 'sv1' and main_clause_rel != 'tag':
            if main_clause == verb.getparent():
               pred_node = pred(verb, nodeyield)
               pred_node_pt = gav(pred_node, 'pt') # we want to exclude case where an adverb immediately precedes the verb vklstap, stap_04:22
            else:
                pred_node_pt = ''
            if is_topic_drop_verb(verb) and pred_node_pt not in ['bw']:
                results.append(verb)
        if main_clause_cat == 'smain':
            main_clause_yield = getnodeyield(main_clause)
            main_clause_yield_first = main_clause_yield[0] if main_clause_yield != [] else None
            main_clause_yield_first_pt = gav(main_clause_yield_first, 'pt')
            main_clause_yield_first_wvorm = gav(main_clause_yield_first, 'wvorm')
            if (main_clause_yield_first_pt == 'ww' and main_clause_yield_first_wvorm == 'pv' and
                is_topic_drop_verb(verb) ):
                results.append(verb)

    # remove vrwond+ cases
    vrwondplus_cases = stree.xpath(expandmacros(".//node[%vrwondplus%]"))
    results = [n for n in results if n.getparent() not in vrwondplus_cases]

    return results



def omitted_phrase(in_stree: SynTree) -> List[SynTree]:
    results = []
    stree = indextransform(in_stree)
    heads = stree.xpath('.//node[@word and @rel="hd"]')
    for head in heads:
        # exclude imperatives
        imperatives = head.xpath(parent_imperative_xpath)
        if imperatives != []:
            continue
        # head_lemma = gav(head, 'original_lemma') if gav(head, 'original_lemma') != '' else gav(head, 'lemma')- dit is fout
        head_lemma = gav(head, 'lemma')
        head_pt = gav(head, 'pt')
        if (head_lemma, head_pt) in synsel:
            base_syns = synsel[(head_lemma, head_pt)]
            syns = extend_syns(base_syns, head)
            overall_ok = False
            for syn in syns:
                all_items_found_so_far = True
                for item in syn:
                    rel = item.rel
                    cond = f'and {expandmacros(item.cond)}' if item.cond != "" else ""
                    item_nodes1 = head.xpath(f'../node[@rel="{rel}" {cond}]')
                    item_nodes = [n for n in item_nodes1 if item.python_cond(n)]
                    item_result = item_nodes != []
                    all_items_found_so_far = all_items_found_so_far and item_result
                    if not all_items_found_so_far:
                        continue
                if all_items_found_so_far:
                    overall_ok = True
                    break
            if not overall_ok:
                results.append(head)

        # include CHAT-omitted cases but exclude er (covered by ov:del_er)
        associate_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.omitted_node_associate))
        for associate_meta in associate_metadata:
            if gav(associate_meta, 'omitted_rel') in complrels:
                the_node = get_node(stree, associate_meta)
                if the_node is not None and gav(the_node, 'lemma') != 'er':
                    results.append(the_node)

        #remove duplicates
        results = list(set(results))


        # remove topic drop cases
        topic_drop_cases = topic_drop(stree)
        results = [n for n in results if n not in topic_drop_cases]

        # remove tag/sv1 cases
        tag_sv1_cases = stree.xpath(tag_s_xpath)
        results = [n for n in results if n not in tag_sv1_cases]

        # remove vrwond+ cases
        vrwondplus_cases = stree.xpath(expandmacros(".//node[%vrwondplus%]"))
        results = [n for n in results if n.getparent() not in vrwondplus_cases]

    return results



locadv_condition = expandmacros('%new_STAP_BB_p%')
def get_preceding_locadvs(subject: SynTree) -> List[SynTree]:
    parent = subject.getparent()
    locadvs = parent.xpath(f'.//node[{locadv_condition}]') if parent is not None else []
    for locadv in locadvs:
        locadv_int_end = int(gav(locadv, 'end'))
        subject_int_begin = int(gav(subject, 'begin'))
        if locadv_int_end <= subject_int_begin:
            return True
    return False

r_p_xpath = expandmacros(f'.//node[@cat="pp"]/node[@rel="obj1" and %Rpronoun%]')
def get_preceding_r_p(subject: SynTree) -> List[SynTree]:
    parent = subject.getparent()
    r_ps = parent.xpath(r_p_xpath)
    for r_p in r_ps:
        r_p_int_end = int(gav(r_p, 'end'))
        subject_int_end = int(gav(subject, 'begin'))
        if r_p_int_end <= subject_int_end:
            return True
    return False


def su_precedes_pv_in_smain(subject, pv, single_word_only=False) -> bool:
    su_pt = gav(subject, 'pt')
    su_parent = subject.getparent()
    su_parent_cat = gav(su_parent, 'cat')
    must_be_done = su_pt in ['n', 'vnw'] if single_word_only else True
    if must_be_done and su_parent_cat == 'smain':
        su_end_int = int(gav(subject, 'end'))
        pv_begin_int = int(gav(pv, 'begin'))
        result = su_end_int <= pv_begin_int
    else:
        result = False
    return result


weak_indefinite_subject_xpath = expandmacros('self::node[@rel="su" and (%weak_indefinite_np% or %weak_indefinite_single_word%) ]')
strong_obj_xpath = expandmacros('../node[@rel="obj1" and %strong_phrase%]')
def omitted_expletive_er(stree: SynTree) -> List[SynTree]:
    results = []
    pvs = stree.xpath('.//node[@pt="ww" and @rel="hd" and @wvorm="pv"]')
    for pv in pvs:
        subject = find1(pv, '../node[@rel="su"]')
        if subject is None:
            pass
            # results.append(pv) # only in impersonal passives but not in imperatives, omitted subjects
        else:
            raw_wi_subject = find1(subject, weak_indefinite_subject_xpath)
            if raw_wi_subject is not None:
                wi_subject = None if is_phrase_with_omitted_def_det(raw_wi_subject) else raw_wi_subject
            else:
                wi_subject = raw_wi_subject
            if wi_subject is not None and not su_precedes_pv_in_smain(wi_subject, pv):
                left_locadvs = get_preceding_locadvs(wi_subject)
                left_r_ps = get_preceding_r_p(wi_subject)
                dependent_verbs = get_ww_dependent_verbs(pv)
                strong_objs = pv.xpath(strong_obj_xpath)
                omitted_strong_objects = get_omitted_strong_objects(pv)
                for ww in dependent_verbs:
                    ww_strong_objs = ww.xpath(strong_obj_xpath)
                    strong_objs += ww_strong_objs
                    ww_omitted_strong_objs = get_omitted_strong_objects(ww)
                    omitted_strong_objects += ww_omitted_strong_objs
                omitted_strong_object_found = omitted_strong_objects != []
                predc = find1(pv, '../node[@rel="predc"]')
                if (predc is not None and
                        (x_isnominal(predc) or
                         x_is_nominal_phrase(predc) or
                         gav(predc, 'cat') == 'cp')):
                    continue
                if not left_locadvs  and not left_r_ps and strong_objs == [] and not omitted_strong_object_found:
                    results.append(pv)

    return results

self_strong_phrase_xpath = expandmacros('self::omitted_node[%strong_phrase%]')
def get_omitted_strong_objects(ww: SynTree) -> List[SynTree]:
    results = []
    omitted_objs = find_omitted_phrase(ww, lambda x: gav(x, 'rel') == 'obj1')
    for omitted_object in omitted_objs:
        is_strong = omitted_object.xpath(self_strong_phrase_xpath) != []
        if is_strong:
            results.append(omitted_object)
    return results

self_definite_det_xpath = expandmacros('self::omitted_node[%definite_det%]')
def is_phrase_with_omitted_def_det(phrase: SynTree) -> bool:
    if 'cat' in phrase.attrib:
        hd = find1(phrase, './node[@rel="hd"]')
    elif 'word' in phrase.attrib:
        hd = phrase
    else:
        return False
    omitted_dets = find_omitted_phrase(hd, lambda n: gav(n, 'rel') == 'det')
    for omitted_det in omitted_dets:
        is_definite = omitted_det.xpath(self_definite_det_xpath) != []
        if is_definite:
            return True
    return False

def get_retracing_position(cleanedtoken_annotationposlist: List[int], retracing_annotationposlist: List[int]) -> int:
    # it is presupposed that these lists are sorted
    last_retracing_position = retracing_annotationposlist[-1]
    for pos in cleanedtoken_annotationposlist:
        if pos > last_retracing_position:
            return pos
    return 0

def false_start(stree: SynTree) -> List[SynTree]:
    results = retracing(stree, mode=false_start_mode)
    return results


def retracing(stree: SynTree, mode=None) -> List[SynTree]:
    results = []
    retracings = stree.xpath(f'.//xmeta[@name="{CHAT_retracing}"]')
    cleanedtokenpositions_meta = find1(stree, './/xmeta[@name="cleanedtokenpositions"]')
    cleanedtokenisation = find1(stree, './/xmeta[@name="cleanedtokenisation"]')
    if cleanedtokenpositions_meta is not None:
        cleanedtokens_annotationposlist = eval(gav(cleanedtokenpositions_meta, 'annotationposlist'))
        cleanedtokens_wordlist = eval(gav(cleanedtokenisation, 'annotationwordlist'))
        for retracing in retracings:
            retracing_annotationposlist = eval(gav(retracing, 'annotationposlist'))
            if mode is false_start_mode:
                cond = is_false_start(retracing, cleanedtokenisation, cleanedtokenpositions_meta)
            elif mode == self_correction_mode:
                cond = is_self_correction(retracing, cleanedtokenisation, cleanedtokenpositions_meta)
            elif mode == repetition_mode:
                cond = is_repetition_retracing(retracing, cleanedtokenisation, cleanedtokenpositions_meta)
            else:
                cond = True
            if cond:
                position = get_retracing_position(cleanedtokens_annotationposlist, retracing_annotationposlist)
                result = find1(stree, f'.//node[@word and @begin="{position}"]')
                if result is None:
                    stree_nodeyield = getnodeyield(stree)
                    result = stree_nodeyield[0]
                results.append(result)
    return results

def self_correction(stree: SynTree) -> List[SynTree]:
    results = retracing(stree, mode=self_correction_mode)
    return results


def repetition(stree: SynTree) -> List[SynTree]:
    results = []
    repetitions = stree.xpath(f'.//xmeta[@name="{CHAT_repetition}"]')
    cleanedtokenpositions_meta = find1(stree, './/xmeta[@name="cleanedtokenpositions"]')
    if cleanedtokenpositions_meta is not None:
        cleanedtokens_annotationposlist = eval(gav(cleanedtokenpositions_meta, 'annotationposlist'))
        for repetition in repetitions:
            retracing_annotationposlist = eval(gav(repetition, 'annotationposlist'))
            position = get_retracing_position(cleanedtokens_annotationposlist, retracing_annotationposlist)
            result = find1(stree, f'.//node[@word and @begin="{position}"]')
            if result is None:
                stree_nodeyield = getnodeyield(stree)
                result = stree_nodeyield[0]
            results.append(result)

    # add retracings that are actually repetitions
    new_results = retracing(stree, mode=repetition_mode)

    results += new_results

    return results

def is_repetition_retracing(retracing: SynTree, cleanedtokenisation: SynTree, cleanedtokenpositions: SynTree) -> bool:
    retracing_wordlist = eval(gav(retracing, 'annotationwordlist'))
    retracing_annotationposlist = eval(gav(retracing, 'annotationposlist'))
    cleanedtokenisation_annotationwordlist = eval(gav(cleanedtokenisation, 'annotationwordlist'))
    cleanedtokenpositions_annotationposlist = eval(gav(cleanedtokenpositions, 'annotationposlist'))
    fulltree = find1(retracing, 'ancestor::alpino_ds')
    xsid = 0 if fulltree is None else getxsid(fulltree)
    for i, pos in enumerate(cleanedtokenpositions_annotationposlist):
        if retracing_annotationposlist == []:
            settings.LOGGER.error(f'Empty retracingannotationposlist in {xsid}, probably due to an annotation error, e.g. <&de> [/] ')
            break
        if pos > retracing_annotationposlist[-1]:
            break
    end_pos = i + len(retracing_wordlist)
    if end_pos < len(cleanedtokenisation_annotationwordlist):
        result = cleanedtokenisation_annotationwordlist[i:end_pos] == retracing_wordlist
    else:
        result = False
    return result

def is_false_start(retracing, cleanedtokenisation, cleanedtokenpositions_meta) -> bool:
    retracing_annotationposlist = eval(gav(retracing, 'annotationposlist'))
    cleanedtokens_annotationposlist = eval(gav(cleanedtokenpositions_meta, 'annotationposlist'))
    result = (cleanedtokens_annotationposlist != [] and retracing_annotationposlist != [] and
            not (cleanedtokens_annotationposlist[0] < retracing_annotationposlist[0]) and
            not is_repetition_retracing(retracing, cleanedtokenisation, cleanedtokenpositions_meta))
    return result

def is_self_correction(retracing, cleanedtokenisation, cleanedtokenpositions_meta) -> bool:
    retracing_annotationposlist = eval(gav(retracing, 'annotationposlist'))
    cleanedtokens_annotationposlist = eval(gav(cleanedtokenpositions_meta, 'annotationposlist'))
    result = (cleanedtokens_annotationposlist != [] and retracing_annotationposlist != [] and
                cleanedtokens_annotationposlist[0] < retracing_annotationposlist[0] and
                not is_repetition_retracing(retracing, cleanedtokenisation, cleanedtokenpositions_meta))
    return result

def is_repetition(retracing, cleanedtokenisation, cleanedtokenpositions_meta) -> bool:
    retracing_annotationposlist = eval(gav(retracing, 'annotationposlist'))
    cleanedtokens_annotationposlist = eval(gav(cleanedtokenpositions_meta, 'annotationposlist'))
    result = (cleanedtokens_annotationposlist != [] and retracing_annotationposlist != [] and
            not (cleanedtokens_annotationposlist[0] < retracing_annotationposlist[0]) and
            not is_repetition_retracing(retracing, cleanedtokenisation, cleanedtokenpositions_meta))
    return result


def get_retracing_word_count(stree: SynTree, mode=None) -> int:
    result = 0
    true_retracings = stree.xpath(f'.//xmeta[@name="{CHAT_retracing}"]')
    repetitions = stree.xpath(f'.//xmeta[@name="{CHAT_repetition}"]')
    retracings = true_retracings + repetitions
    cleanedtokenpositions_meta = find1(stree, './/xmeta[@name="cleanedtokenpositions"]')
    cleanedtokenisation = find1(stree, './/xmeta[@name="cleanedtokenisation"]')
    if cleanedtokenpositions_meta is not None:
        cleanedtokens_annotationposlist = eval(gav(cleanedtokenpositions_meta, 'annotationposlist'))
        cleanedtokens_wordlist = eval(gav(cleanedtokenisation, 'annotationwordlist'))
        for retracing in retracings:
            retracing_annotationposlist = eval(gav(retracing, 'annotationposlist'))
            if mode is false_start_mode:
                cond = is_false_start(retracing, cleanedtokenisation, cleanedtokenpositions_meta)
            elif mode == self_correction_mode:
                cond = is_self_correction(retracing, cleanedtokenisation, cleanedtokenpositions_meta)
            elif mode == repetition_mode:
                cond = is_repetition_retracing(retracing, cleanedtokenisation, cleanedtokenpositions_meta)
            else:
                cond = True
            if cond:
                result += len(retracing_annotationposlist)
    return result

def get_tb_retracing_word_counts(tb: TreeBank, mode=None) -> List[Tuple[UttId, int]]:
    results = []
    count = 0
    for stree in tb:
        xsid = getxsid(stree)
        verbose = False
        if verbose:
            print(xsid)
        if xsid != '0':
            count += 1
            fs_count = get_retracing_word_count(stree, mode=mode)
            if count <= 50:
                results.append((xsid, fs_count))
            else:
                settings.LOGGER.warning(f'More than 50 utterances encountered. Over 50 ignored for non communicative word analysis')
    return results

hoofdww_weg_xpath = """.//node[@rel="hd" and @pt="ww" and ../node[@rel="vc" and @cat="inf" and not(node[@rel="hd" and @pt="ww"])]]
"""
def hoofdww_weg(stree: SynTree) -> List[SynTree]:
    results = stree.xpath(hoofdww_weg_xpath)
    return results

