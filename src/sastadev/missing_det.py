from collections import defaultdict
from lxml import etree
import os
from sastadev.anonymization import sasta_pseudonyms
from sastadev.conf import settings
from sastadev.constants import datafolder, outtreebanksfolder
from sastadev.readcsv import readcsv
from sastadev.stringfunctions import compoundsep
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import find1, getattval as gav, getnodeyield, getxsid
from typing import List, Tuple

eps = ''

treesfolder = 'trees'

beroepenfilename = 'beroepen.txt'
beroepenfullname = os.path.join(settings.SD_DIR, datafolder, 'filledpauseslexicon', beroepenfilename)
beroepenlist = readcsv(beroepenfullname)
beroepen = {beroep[0] for _, beroep in beroepenlist}

robust_pseudonyms = ['BUURMAN', 'BUURVROUW', 'CLUB', 'JUF', 'KLASGENOOT', 'KLASGENOTE', 'Sastagroep',
                     'STAD', 'TEAMGENOOT', 'TEAMGENOTE', 'VRIEND', 'VRIENDIN']

wellformed_vz_n_combinations = [
('aan', 'tafel'),
    ('aan', 'zee'),
    ('boven', 'baas'),
    ('boven', 'wonder'),
    ('in', 'bad'),
('in', 'bed'),
('in', 'brand'),
('in', 'coma'),
('in', 'galop'),
    ('in', 'huis'),
    ('in', 'kas'),
    ('in', 'principe'),
    ('in', 'werking'),
    ('in', 'zee'),
    ('na', 'school'),
('naar', 'bed'),
('naar', 'huis'),
('naar', 'school'),
    ('naar', 'zee'),
    ('op', 'bed'),
('op', 'bezoek'),
('op', 'brood'),
('op', 'goal'),
('op', 'kool'),
    ('op', 'kop'),
('op', 'reis'),
('op', 'school'),
    ('op', 'school_reis'),
('op', 'schoot'),
('op', 'slot'),
    ('op', 'stal'),
('op', 'straat'),
('op', 'tafel'),
('op', 'televisie'),
('op', 'tv'),
('op', 'vakantie'),
    ('op', 'volgorde'),
    ('op', 'zee'),
    ('op', 'zolder'),
    ('uit', 'bad'),
    ('uit', 'bed'),
    ('uit', 'huis'),
    ('van', 'huis'),
    ('van', 'slag'),
    ('van', 'school'),
    ('van', 'stapel'),

    ('van', 'tafel')
]


n_v_expression_list = ['stage lopen', 'rekening houden']
n_v_expression_pairs = [tuple(el.split()) for el in n_v_expression_list]

detless_count_nouns = ['papa', 'mama', 'oma', 'opa', 'moeder', 'sinterklaas', 'mam'] + \
                       ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september',
                        'oktober', 'november', 'december'] + \
                       ['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag'] + \
                       ['morgen', 'overmorgen', 'gisteren'] + \
                       ['kerstmis', 'pasen', 'pinksteren'] +\
                       ['eentje']

predc_detless_count_nouns = ['avond', 'ochtend', 'middag', 'nacht']

color_names = ['rood', 'wit', 'blauw', 'oranje', 'zwart', 'geel', 'groen']
mass_exceptions = ['acquisitie', 'acte', 'appel_sap', 'begeleiding', 'bezoek', 'brood', 'buiten',
                   'cement', 'coördinatie', 'deeg', 'druk', 'goed', 'gym',
                   'klei', 'hout', 'geld',  'informatie', 'ijzer', 'kaas',  'kraak_been',
                   'kracht', 'last', 'logo', 'melk', 'migraine',
                   'pap', 'patat', 'plastic', 'plezier', 'pijn', 'productie',
                   'speelgoed', 'spul', 'suiker',  'thee', 'tijd', 'trek', 'uitzicht', 'vakantie', 'verf', 'visite', 'vloeistof',
                    'water', 'werk', 'yogi_drink', 'zeep' ] + color_names
both_exceptions = ['ananas', 'angst', 'beeld', 'familie', 'flapoor',
                   'geluid', 'geschiedenis',  'glas', 'groente', 'hersen_letsel',  'hulp', 'kip', 'onderzoek',
                   'pak_DIM_avond', 'pizza', 'ruzie', 'saxofoon', 'saxofoon_les', 'spons', 'straf', 'techniek',
                   'troep' , 'verkoop', 'vis', 'vuur',
                   'worst', 'zekerheid', 'zijde',  'zin', 'zwem_les']
count_exceptions = []
excluded_nouns = [ 'boem', 'hop', 'klik', 'piep', 'plons', 'stop', 'tik', 'facilitair']

volgend_vorig_nouns = ['jaar','keer', 'maand', 'week', 'seizoen', 'semester']


special_vzs = ['zonder', 'per', 'ter', 'ten']

small_tw_lemmas = ['nul', 'één', 'twee', 'drie', 'vier', 'vijf', 'zes', 'zeven', 'acht', 'negen', 'tien',
                   'elf', 'twaalf', 'dertien', 'veertien', 'vijftien', 'zestien', 'zeventien',
                   'achttien', 'negentien', 'twintig', 'dertig', 'veertig', 'vijftig', 'zestig',
                   'zeventig', 'tachtig', 'negentig', 'honderd', 'duizend']

bare_noun_xpath = """.//node[@pt="n" and @getal="ev"  and 
                             not(@rel="hd" and parent::node[@cat="np"]) and
                             not(@rel="mwp" and parent::node[@cat="mwu" and @rel="hd"]/parent::node[@cat="np"])]"""
count_noun = """(@pt="n" and contains(@frame, 'count') and @getal="ev")"""
in_detless_np = """(parent::node[@cat="np" ] and not(../node[@rel="det"]))"""
bare_noun_in_np_xpath = f""".//node[(({count_noun}  and @rel="hd" and {in_detless_np}) or
                                     ({count_noun} and parent::node[@cat="mwu" and @rel="hd" and {in_detless_np}]))] 
                         """

core_app_cat = '(@pt="tw" or (@pt="n" and @ntype="eigen"))'
app_xpath = f'../node[@rel="app" and ({core_app_cat} or (@cat="conj" and node[@rel="cnj" and {core_app_cat}]))]'


def get_missing_det(stree: SynTree) -> List[SynTree]:
    """
    finds count nouns that occur incorrectly without a determiner
    """
    bare_nouns = stree.xpath(bare_noun_xpath)
    bare_count_nouns = [n for n in bare_nouns if
                        not is_mass(n) and
                        not is_both(n) and
                        not is_numeral(gav(n, 'lemma')) and
                        gav(n, 'lemma') not in detless_count_nouns + excluded_nouns and
                        len(gav(n, 'lemma')) != 1 and
                        'count' in gav(n, 'frame') and
                        not((gav(n, 'rel') == "predc" or no_verb_around(n)) and
                            is_beroep((gav(n, 'lemma'))  or gav(n, 'lemma') in predc_detless_count_nouns)) and
                        not is_pseudonym(gav(n, 'word')) and
                        not robust_is_pseudonym(gav(n, 'word')) and
                        not volgend_vorig(n) and
                        really_no_det(n) and
                        not keeropkeer(n) and
                        not is_part_of_n_v_expressions(n) and
                        not is_part_of_fixed_expression(n) and
                        not in_als_cp(n) and
                        not is_begin_vz(n)]


    # exclude legal vz+ n pairs and n's governed by special vzs
    gov_prep_xpath = "./parent::node[@cat='pp']/node[@pt='vz' and @rel='hd']"
    wrong_bare_count_nouns = []
    for bare_noun in bare_count_nouns:
        gov_prep = find1(bare_noun, gov_prep_xpath)
        if gov_prep is not None:
            vzlemma = gav(gov_prep, 'lemma')
            nlemma = gav(bare_noun, 'lemma')
            if ((vzlemma, nlemma) not in wellformed_vz_n_combinations and
                    vzlemma not in special_vzs and
                    nlemma not in detless_count_nouns) and \
                    not keeropkeer(bare_noun) and \
                    not volgend_vorig(bare_noun):
                wrong_bare_count_nouns.append(bare_noun)
        else:
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
                not is_begin_vz(bare_noun):
            wrong_bare_count_nouns.append(bare_noun)


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
    result = lemma in small_tw_lemmas
    return result

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
            if prevn_pt in ['lw', 'tw'] or prevn_lemma in small_tw_lemmas:
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
    fulltree = n.xpath('ancestor::alpino_ds')
    wordnodelist = getnodeyield(n)
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
    mods = node.xpath('../node[@rel="mod" and (@lemma="vorig" or (@lemma="volgen" and @wtype = "od")) ]')
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



if __name__ == '__main__':
    tryme()
