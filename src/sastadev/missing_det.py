from collections import defaultdict
from lxml import etree
import os

from sastadev.CHAT_Annotation import CHAT_omittedword
from sastadev.anonymization import sasta_pseudonyms
from sastadev.conf import settings
from sastadev.constants import datafolder, outtreebanksfolder
from sastadev import correctionlabels
from sastadev.lexicon import beroepen, both_exceptions, chatspecial, mass_exceptions, n_v_expression_list, vz_count_n_combinations, \
    cardinallexicon, detless_count_nouns, predc_detless_count_nouns, color_names
from sastadev.readcsv import readcsv
from sastadev.stringfunctions import compoundsep
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import (find1, get_associate_meta, getattval as gav, get_node,
                                        getnodeyield, getxsid, mdnameonlyxpathtemplate)
from typing import List, Tuple

eps = ''

treesfolder = 'trees'

# moved to lexicon
# beroepenfilename = 'beroepen.txt'
# beroepenfullname = os.path.join(settings.SD_DIR, datafolder, 'filledpauseslexicon', beroepenfilename)
# beroepenlist = readcsv(beroepenfullname)
# beroepen = {beroep[0] for _, beroep in beroepenlist}

robust_pseudonyms = ['BUURMAN', 'BUURVROUW', 'CLUB', 'CLUBNAAM', 'JUF', 'KLASGENOOT', 'KLASGENOTE',
                     'NAAM', 'Sastagroep',
                     'STAD', 'TEAMGENOOT', 'TEAMGENOTE', 'VRIEND', 'VRIENDIN']

# moved to lexicon
# wellformed_vz_n_combinations = [
# ('aan', 'tafel'),
#     ('aan', 'zee'),
#     ('boven', 'baas'),
#     ('boven', 'wonder'),
#     ('in', 'bad'),
# ('in', 'bed'),
# ('in', 'brand'),
# ('in', 'coma'),
# ('in', 'galop'),
#     ('in', 'huis'),
#     ('in', 'kas'),
#     ('in', 'principe'),
#     ('in', 'werking'),
#     ('in', 'zee'),
#     ('na', 'school'),
# ('naar', 'bed'),
# ('naar', 'huis'),
# ('naar', 'school'),
#     ('naar', 'zee'),
#     ('op', 'bed'),
# ('op', 'bezoek'),
# ('op', 'brood'),
# ('op', 'goal'),
# ('op', 'kool'),
#     ('op', 'kop'),
# ('op', 'reis'),
# ('op', 'school'),
#     ('op', 'school_reis'),
# ('op', 'schoot'),
# ('op', 'slot'),
#     ('op', 'stal'),
# ('op', 'straat'),
# ('op', 'tafel'),
# ('op', 'televisie'),
# ('op', 'tv'),
# ('op', 'vakantie'),
#     ('op', 'volgorde'),
#     ('op', 'zee'),
#     ('op', 'zolder'),
#     ('uit', 'bad'),
#     ('uit', 'bed'),
#     ('uit', 'huis'),
#     ('van', 'huis'),
#     ('van', 'slag'),
#     ('van', 'school'),
#     ('van', 'stapel'),
#
#     ('van', 'tafel')
# ]

wellformed_vz_n_combinations = [tuple(el.split()) for el in vz_count_n_combinations]

# moved to lexicon
# n_v_expression_list = ['stage lopen', 'rekening houden']
n_v_expression_pairs = [tuple(el.split()) for el in n_v_expression_list]

count_exceptions = []
excluded_nouns = [ 'boem', 'hop', 'klik', 'piep', 'plons', 'stop', 'tik', 'facilitair']

volgend_vorig_nouns = ['jaar','keer', 'maand', 'week', 'seizoen', 'semester', 'weekend']


special_vzs = ['zonder', 'per', 'ter', 'ten']

s_possessives = ['mijnes', 'jouwes', 'zijnes', 'hares', 'onzes', 'hunnes']

bare_noun_xpath = """.//node[@pt="n" and @getal="ev"  and 
                             not(@rel="hd" and parent::node[@cat="np"]) and
                             not(@rel="mwp" and parent::node[@cat="mwu" and @rel="hd" and parent::node[@cat="np"]])]"""
count_noun = """(@pt="n" and contains(@frame, 'count') and @getal="ev")"""
in_detless_np = """(parent::node[@cat="np" ] and not(../node[@rel="det"]))"""
bare_noun_in_np_xpath = f""".//node[(({count_noun}  and @rel="hd" and {in_detless_np}) or
                                     ({count_noun} and parent::node[@cat="mwu" and @rel="hd" and {in_detless_np}]))] 
                         """

core_app_cat = '(@pt="tw" or (@pt="n" and @ntype="eigen"))'
app_xpath = f'../node[@rel="app" and ({core_app_cat} or (@cat="conj" and node[@rel="cnj" and {core_app_cat}]))]'

sup_tw_mijne_xpath = """.//node[@positie="nom" and 
       ((((@pt="vnw" and @vwtype="bez") ) and not(../node[@rel="det"])) or
        (@pt="adj" and @aform="super" and not(../node[@rel="mwp" and @pt="lid"]) and not(../node[@rel="det"])) or
        (@pt="tw" and @numtype="rang"  and not(../node[@rel="det"]) and not(@rel="predc" or @rel="dp" or @rel="--"))
       )]"""


def predc_mwu_parent(n: SynTree) -> bool:
    parent = n.getparent()
    result = gav(parent, 'cat') == 'mwu' and gav(parent, 'rel') == 'predc'
    return result

def get_missing_det(stree: SynTree) -> List[SynTree]:
    """
    finds count nouns that occur incorrectly without a determiner
    """
    bare_nouns = stree.xpath(bare_noun_xpath)
    bare_count_nouns = [n for n in bare_nouns if
                        not is_mass(n) and
                        not is_both(n) and
                        not chatspecial(gav(n, 'word')) and
                        not is_numeral(gav(n, 'lemma')) and
                        gav(n, 'lemma') not in detless_count_nouns + excluded_nouns and
                        len(gav(n, 'lemma')) != 1 and
                        gav(n, 'lemma') not in s_possessives and
                        'count' in gav(n, 'frame') and
                        not((gav(n, 'rel') == "predc" or no_verb_around(n) or predc_mwu_parent(n)) and
                            (is_beroep_pred(n)  or gav(n, 'lemma') in predc_detless_count_nouns)) and
                        not is_pseudonym(gav(n, 'word')) and
                        not robust_is_pseudonym(gav(n, 'word')) and
                        not volgend_vorig(n) and
                        really_no_det(n) and
                        not keeropkeer(n) and
                        not is_part_of_n_v_expressions(n) and
                        not is_part_of_fixed_expression(n) and
                        not in_als_cp(n) and
                        not is_begin_vz(n)]

    bare_sup_tw_mijnes = stree.xpath(sup_tw_mijne_xpath)
    bare_count_nouns += bare_sup_tw_mijnes

    # exclude legal vz+ n pairs and n's governed by special vzs
    gov_prep_xpath = "./parent::node[@cat='pp']/node[@pt='vz' and @rel='hd']"
    wrong_bare_count_nouns = []
    for bare_noun in bare_count_nouns:
        vz_lemmas = []
        n_begin = gav(bare_noun, 'begin')
        nlemma = gav(bare_noun, 'lemma')
        gov_prep = find1(bare_noun, gov_prep_xpath)
        vz_lemma = ''
        if gov_prep is not None:
            vz_lemma = gav(gov_prep, 'lemma')
        else:
            associate_metadata = get_associate_meta(bare_noun)
            for associate_meta in associate_metadata:
                annotatedposlist = eval(gav(associate_meta, 'annotatedposlist'))
                associate_begin = annotatedposlist[0]
                if associate_begin == n_begin:
                    vz_pt = gav(associate_meta, 'omitted_pt')
                    vz_rel = gav(associate_meta, 'rel')
                    if vz_pt == 'vz' and vz_rel == 'hd':
                        vz_lemma = gav(associate_meta, 'omitted_lemma')
        if (vz_lemma, nlemma) not in wellformed_vz_n_combinations and \
                vz_lemma  not in special_vzs and \
                    nlemma not in detless_count_nouns and \
                    not keeropkeer(bare_noun) and \
                    not volgend_vorig(bare_noun) and \
                    not is_soort_van(bare_noun):
                wrong_bare_count_nouns.append(bare_noun)

    bare_nouns_in_np = stree.xpath(bare_noun_in_np_xpath)
    for bare_noun in bare_nouns_in_np:
        nlemma = gav(bare_noun, 'lemma')
        nword = gav(bare_noun, 'word')
        np = find1(bare_noun, 'parent::node[@cat="np"]')
        if np is None:
            np = find1(bare_noun, 'parent::node[@cat="mwu"]/parent::node[@cat="np"]')
        np_rel = gav(np, 'rel') if np is not None else ''
        app = find1(bare_noun, app_xpath)
        if is_modified_by_heel(bare_noun):
            wrong_bare_count_nouns.append(bare_noun)
        if (not is_mass(bare_noun) and not is_both(bare_noun) and
            nlemma not in  detless_count_nouns + excluded_nouns and
            not is_numeral(gav(bare_noun, 'lemma')) and
            not((np_rel == "predc" or no_verb_around(bare_noun)) and (is_beroep(nlemma) or nlemma in predc_detless_count_nouns)) and
                len(nlemma) != 1) and \
                app is None and \
                not is_pseudonym(nword) and \
                not robust_is_pseudonym(gav(bare_noun, 'word')) and \
                not volgend_vorig(bare_noun) and \
                not is_part_of_n_v_expressions(bare_noun) and \
                not is_part_of_fixed_expression(bare_noun) and \
                not in_als_cp(bare_noun) and\
                not is_begin_vz(bare_noun) and \
                not is_soort_van(bare_noun):
            wrong_bare_count_nouns.append(bare_noun)

    # find examples of CHAT-omitted articles
    associate_nodes = get_associate_word_nodes(stree, omitted_pts=['lid'])
    for associate_node in associate_nodes:
        # we only want to include the ones that are articles and have not been found yet
        if associate_node not in wrong_bare_count_nouns:
            wrong_bare_count_nouns.append(associate_node)

    # no duplicates
    wrong_bare_count_nouns = list(set(wrong_bare_count_nouns))

    return wrong_bare_count_nouns

def is_mass(node: SynTree) -> bool:
    result = is_class_member(node, mass_exceptions)
    return result

def is_both(node: SynTree) -> bool:
    result = is_class_member(node, both_exceptions)
    return result

def is_class_member(node: SynTree, theclass) -> bool:
    node_lemma = gav(node, 'lemma')
    if node_lemma in theclass:
        return True
    parts = node_lemma.split(compoundsep)
    if len(parts) > 1 and parts[-1] in theclass:
        return True
    return False

subj_xpath = """../node[@rel="su"]"""
def is_beroep_pred(noun: SynTree) -> bool:
    noun_lemma = gav(noun, 'lemma')
    if not is_beroep(noun_lemma):
        return False
    subject = find1(noun, subj_xpath)
    if subject is None:
        return True
    subject_lemma = gav(subject, 'lemma')
    if subject_lemma in ['dit', 'dat', 'het']:
        return False
    else:
        return True


def is_beroep(lemma: str) -> bool:
    result = lemma in beroepen
    if result:
        return True
    cleanlemma = eps.join([c for c in lemma if c != compoundsep])
    result = cleanlemma in beroepen
    if result:
        return True
    return False

def is_numeral(lemma: str) -> bool:
    if lemma in cardinallexicon:
        return True
    parts = lemma.split(compoundsep)
    if len(parts) > 1 and all([part in cardinallexicon for part in parts]):
        return True
    return False

als_cmp = """parent::node[@cat="cp" and node[@rel="cmp" and @lemma="als" ]]"""
def in_als_cp(node: SynTree) -> bool:
    results = node.xpath(f'./{als_cmp}')
    if results == []:
        results = node.xpath(f'./parent::node[@cat="np" and {als_cmp}]')
    return results != []

def is_begin_vz(node: SynTree) -> bool:
    node_frame = gav(node, 'frame')         # ['begin', 'eind', 'midden', 'medio', 'eerder']
    if node_frame == 'tmp_app_noun':
        return True
    node_lemma = gav(node, 'lemma')
    if node_lemma not in ['begin', 'eind']:
        return False
    pps = node.xpath('../node[@cat="pp"  and @rel="mod"]')
    for pp in pps:
        pp_obj_bare_head = find1(pp, './node[@rel="obj1" and @pt="n"]')
        if pp_obj_bare_head is not None:
            result = 'tmp_noun' in gav(pp_obj_bare_head, 'frame')
            return result
        else:
            pp_obj_np_head = find1(pp, './node[@rel="obj1" and @cat="np"]/node[@rel="hd" and @pt="n"]')
            if pp_obj_np_head is not None:
                result = 'tmp_noun' in gav(pp_obj_np_head, 'frame')
                return result
    return False

def really_no_det(node: SynTree) -> bool:
    top = find1(node, 'ancestor::alpino_ds')
    if top is None:
        return False
    wordnodelist = getnodeyield(top)
    for ctr, wordnode in enumerate(wordnodelist):
        prevn = wordnodelist[ctr - 1] if ctr > 0 else None
        if wordnode == node:
            prevn_pt = gav(prevn, 'pt')
            prevn_lemma = gav(prevn, 'lemma')
            if prevn_pt in ['lw', 'tw'] or prevn_lemma in cardinallexicon:
                return False
    return True

def keeropkeer(node: SynTree) -> bool:
    top = find1(node, 'ancestor::alpino_ds')
    if top is None:
        return False
    node_lemma = gav(node, 'lemma')
    wordnodelist = getnodeyield(top)
    for ctr, n in enumerate(wordnodelist):
        prevn = wordnodelist[ctr - 1] if ctr >0 else None
        prevprevn = wordnodelist[ctr - 2] if ctr > 1 else None
        nextn = wordnodelist[ctr + 1]  if ctr < len(wordnodelist) - 1 else None
        nextnextn = wordnodelist[ctr + 2] if ctr < len(wordnodelist) - 2 else None
        if n == node:
            prevn_pt = gav(prevn, 'pt')
            prevprevn_lemma = gav(prevprevn, 'lemma')
            result1 = prevn_pt == 'vz' and prevprevn_lemma == node_lemma
            if result1:
                return result1
            nextn_pt = gav(nextn, 'pt')
            nextnextn_lemma = gav(nextnextn, 'lemma')
            result2 = nextn_pt == 'vz' and nextnextn_lemma == node_lemma
            if result2:
                return result2
    return False

def no_verb_around(n: SynTree) -> bool:
    fulltree = find1(n, 'ancestor::alpino_ds')
    if fulltree is None:
        return True
    wordnodelist = getnodeyield(fulltree)
    result = all([gav(wn, 'pt') != 'ww' or gav(wn, 'positie') == 'prenom' for wn in wordnodelist])
    return result

def robust_is_pseudonym(lemma: str) -> str:
    return lemma in robust_pseudonyms or lemma[:-1] in robust_pseudonyms

def is_pseudonym(lemma:str) -> bool:
    result = lemma in sasta_pseudonyms or lemma[:-1] in sasta_pseudonyms
    return result

def volgend_vorig(node: SynTree) -> bool:
    node_lemma = gav(node, 'lemma')
    if node_lemma not in volgend_vorig_nouns:
        return False
    mods = node.xpath('../node[@rel="mod" and (@lemma="vorig" or (@lemma="volgen" and @wvorm = "od")) ]')
    if mods == []:
        return False
    return True


def is_part_of_fixed_expression(node: SynTree) -> bool:
    stree  = find1(node, 'ancestor::alpino_ds')
    wordnodelist = getnodeyield(stree)
    wordnodelemmalist =[gav(n, 'lemma') for n in wordnodelist]
    node_position = wordnodelist.index(node)
    node_lemma = gav(node, 'lemma')
    node_expression_position_pairs = get_fixed_expressions(node_lemma)
    for expression, position in node_expression_position_pairs:
        right_node_count = len(expression) - position
        cand_exp_list = wordnodelist[node_position-position:node_position] + \
                   [wordnodelist[node_position]] +\
                   wordnodelist[node_position + 1: node_position + right_node_count]
        cand_exp_lemma_list = [gav(n, 'lemma') for n in cand_exp_list]
        if cand_exp_lemma_list == expression:
            return True
    return False

def is_part_of_n_v_expressions(node: SynTree) -> bool:
    node_lemma = gav(node, 'lemma')
    verb_node = find1(node, '../node[@rel="hd" and @pt="ww"]')
    if verb_node is not None:
        verb_lemma =  gav(verb_node, 'lemma')
        result = (node_lemma, verb_lemma) in n_v_expression_pairs
        return result
    return False

def get_fixed_expressions(lemma:str) -> List[Tuple[List[str], int]]:
    results = []
    expressions = fixed_expression_dict[lemma] if lemma in fixed_expression_dict else []
    for expression in expressions:
        for ctr, token in enumerate(expression):
            if token == lemma:
                newtuple = (expression, ctr)
                results.append(newtuple)
    return results

def get_fixed_expression_dict(fixed_expression_list) -> dict:
    fixed_expression_dict = defaultdict(list)
    for expression in fixed_expression_list:
        expression_words = expression.split()
        for word in expression_words:
            expression_word_list = expression.split()
            fixed_expression_dict[word].append(expression_word_list)
    return fixed_expression_dict

soort_van_n_xpath = """parent::node[@cat="pp" and node[@rel="hd" and @lemma="van"]]/parent::node[node[@rel="hd" and @lemma="soort"]]"""
soort_van_np_xpath = """parent::node[@cat="np"]/parent::node[@cat="pp" and node[@rel="hd" and @lemma="van"]]/parent::node[node[@rel="hd" and @lemma="soort"]]"""
soort_n_xpath = """parent::node[@cat="np" and node[@rel="hd" and @lemma="soort"]]"""
soort_np_xpath = """parent::node[@cat="np"]/parent::node[@cat="np" and node[@rel="hd" and @lemma="soort"]]"""

def is_soort_van(noun: SynTree) -> bool:
    noun_rel = gav(noun, 'rel')
    result1 = noun_rel == 'obj1' and noun.xpath(soort_van_n_xpath) != []
    result2 = noun_rel == 'hd' and noun.xpath(soort_van_np_xpath) != []
    result3 = noun_rel == 'mod' and noun.xpath(soort_n_xpath) != []
    result4 = noun_rel == 'hd' and noun.xpath(soort_np_xpath) != []
    result = result1 or result2 or result3 or result4
    return result

modified_by_heel_xpath = """../node[@rel="mod" and @lemma="heel"]"""
def is_modified_by_heel(noun: SynTree) -> bool:
    result = noun.xpath(modified_by_heel_xpath) != []
    return result


fixed_expression_list = ['dag en nacht', 'van lief en Lee']   # Alpino ontleed "lee" als de eigennaam "Lee"
fixed_expression_dict = get_fixed_expression_dict(fixed_expression_list)

test_utts = [('tarsp_01', '038'),
             ('tarsp_04', '022'),
             ('tarsp_06', '015'), # ; naar huis
             ('tarsp_02', '004')]
def tryme():

    vkltarsp_path = os.path.join(settings.DATAROOT, 'vkltarsp', outtreebanksfolder, treesfolder)
    for samplename, uttid in test_utts:
        fullname = os.path.join(vkltarsp_path, f'{samplename}_corrected', f'{samplename}_corrected_{uttid}.xml')
        fullstree = etree.parse(fullname)
        stree = fullstree.getroot()
        xsid = getxsid(stree)
        wrong_nouns = get_missing_det(stree)
        print(f'xsid={xsid}')
        for wrong_noun in wrong_nouns:
            wrong_noun_lemma = gav(wrong_noun, 'lemma')
            print(wrong_noun_lemma)

def get_associate_word_nodes(stree: SynTree, omitted_pts: List[str]) -> List[SynTree]:
    results = []
    associate_word_metadata = stree.xpath(mdnameonlyxpathtemplate.format(mdname=correctionlabels.omitted_node_associate))
    for associate_word_meta in associate_word_metadata:
        if gav(associate_word_meta, 'omitted_pt') in omitted_pts:
            thenode = get_node(stree, associate_word_meta)
            if thenode is not None:
                results.append(thenode)
    return results






if __name__ == '__main__':
    tryme()
