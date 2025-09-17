from editdistance import distance
from sastadev.basicreplacements import basicreplacements
from sastadev.conf import settings
from sastadev.corrector import (disambiguationdict, initialmaarvgxpath)
from sastadev.lexicon import de, dets, nochildword, preferably_intransitive_verbs, tsw_non_words, validnouns, \
    validword, \
    wordsunknowntoalpinolexicondict, wrongposwordslexicon
from sastadev.macros import expandmacros
from sastadev.metadata import (Meta,  defaultpenalty,
                               ADULTSPELLINGCORRECTION, ALLSAMPLECORRECTIONS, BASICREPLACEMENTS, CONTEXT,
                               HISTORY, CHILDRENSPELLINGCORRECTION, THISSAMPLECORRECTIONS, replacementsubsources
                               )
from sastadev.methods import Method, asta, tarsp, supported_methods, tarsp2017
from sastadev.predcvagreement import get_predc_v_mismatches
from sastadev.readmethod import read_method

from sastadev.sastatypes import (
                                 MethodName, Penalty,
                                 SynTree, )
from sastadev.semantic_compatibility import semincompatiblecount
from sastadev.stringfunctions import digits, ispunctuation
from sastadev.sva import phicompatible
from sastadev.treebankfunctions import (clausecats, countav,
                                          find1,
                                        getattval,
                                        getcompoundcount, getnodeyield,
                                         getsentence,  getxsid,
                                        getyield, isdefdet, is_neut_sg)
from typing import Callable, List, Tuple


class Criterion():
    def __init__(self, name, getfunction, polarity, description):
        self.name: str = name
        self.getfunction: Callable[[SynTree], bool] = getfunction
        self.polarity: int = polarity
        self.description: str = description


positive = +1
negative = -1

subsourcesep = '/'
defaultmethod = read_method(tarsp, supported_methods[tarsp], variant=tarsp2017)


def splitsource(fullsource: str) -> Tuple[str, str]:
    parts = fullsource.split(subsourcesep, maxsplit=2)
    if len(parts) == 2:
        return (parts[0], parts[1])
    elif len(parts) == 1:
        return (parts[0], '')
    else:      #  == 0 or > 2
        # should never occur
        return ('', '')



post_complemental_subjects_xpath = """.//node[@rel="su"   and 
                parent::node[@cat="ssub" and not(parent::node[@cat="whsub" or @cat="whrel" or @cat="rel"])] and 
                @begin >= ../node[(@word or @cat) and 
                                  (not(@pdtype) or @pdtype!="adv-pron") and 
                                  (@rel="ld" or @rel="obj1" or @rel="pc" or @rel="obj2")]/@end]"""
def get_post_complemental_subject_nodes(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> List:
    return tree.xpath(post_complemental_subjects_xpath)

def getpostcomplsucount(tree: SynTree, mds: List[Meta], methodname: str='') -> int:
    post_complemental_subject_nodes = get_post_complemental_subject_nodes(tree)
    return len(post_complemental_subject_nodes)


def getstreereplacementpenalty(stree: SynTree) -> int:
    contextpositions = set()
    spellingcorrectionpositions = set()
    fullpenalty = 0
    metadatas = stree.xpath('.//metadata')
    if metadatas != []:
        metadata = metadatas[0]
        for meta in metadata:
            if meta.tag != 'xmeta':
                continue
            fullsource = meta.attrib['source'] if 'source' in meta.attrib else ''
            mainsource, subsource = splitsource(fullsource)
            if subsource in {BASICREPLACEMENTS, ALLSAMPLECORRECTIONS, HISTORY, CONTEXT, CHILDRENSPELLINGCORRECTION,
                             ADULTSPELLINGCORRECTION, THISSAMPLECORRECTIONS}:
                penalty = meta.attrib['penalty'] if 'penalty' in meta.attrib else 0
                fullpenalty += penalty
                annotatedposlist = meta.attrib['annotatedpositions'] if 'annotatedposlist' in meta.attrib else '[]'
                position = annotatedposlist[1:-1]
                if subsource in [ADULTSPELLINGCORRECTION, CHILDRENSPELLINGCORRECTION] and position != '':
                    spellingcorrectionpositions.add(position)
                if subsource == CONTEXT and position != '':
                    contextpositions.add(position)
        spellcontextintersection = contextpositions.intersection(spellingcorrectionpositions)
        reduction = len(spellcontextintersection) * defaultpenalty
        fullpenalty = fullpenalty - reduction

    return fullpenalty


def getreplacementpenalty(nt: SynTree, mds: List[Meta], method: Method = defaultmethod) -> int:
    contextpositions = set()
    spellingcorrectionpositions = set()
    fullpenalty = 0
    for meta in mds:
        fullsource = meta.source
        mainsource, subsource = splitsource(fullsource)
        if subsource in {BASICREPLACEMENTS, ALLSAMPLECORRECTIONS, HISTORY, CONTEXT, CHILDRENSPELLINGCORRECTION,
                         ADULTSPELLINGCORRECTION, THISSAMPLECORRECTIONS}:
            penalty = meta.penalty
            fullpenalty += penalty
            position = meta.annotatedposlist[0] if meta.annotatedposlist != [] else ''
            if subsource in [CHILDRENSPELLINGCORRECTION, ADULTSPELLINGCORRECTION] and position != '':
                spellingcorrectionpositions.add(position)
            if subsource == CONTEXT and position != '':
                contextpositions.add(position)
    spellcontextintersection = contextpositions.intersection(spellingcorrectionpositions)
    reduction = len(spellcontextintersection) * defaultpenalty
    fullpenalty = fullpenalty - reduction

    return fullpenalty


def getsvaokcount(nt: SynTree, mds: List[Meta], methodname: str='') -> int:
    subjects = nt.xpath('.//node[@rel="su"]')
    counter = 0
    for subject in subjects:
        pv = find1(subject, '../node[@rel="hd" and @pt="ww" and @wvorm="pv"]')
        if phicompatible(subject, pv):
            counter += 1
    return counter


def get_de_plus_neuter_nodes(tree: SynTree, mds: List[Meta], method: Method = defaultmethod) -> List:
    word_nodes = getnodeyield(tree)
    found_nodes = []
    # Consecutive pairs of nodes. (A, B), (B, C), (C, D), ...
    for node_1, node_2 in zip(word_nodes, word_nodes[1:]):
        word_1 = getattval(node_1, "word").lower()

        # Skip if the first node is not a 'de' determiner.
        if word_1 not in dets[de]:
            continue

        word_2 = getattval(node_2, "word").lower()
        verbose = False
        if verbose:
            xsid = getxsid(tree)
            sent = getsentence(tree)
            print(f'processing {xsid}: {sent}')
        if ispunctuation(word_2):  # punctuation needs no parsing and causes an error in the parsing URL
            continue
        parsed_word_2_tree = settings.PARSE_FUNC(word_2)
        parsed_word_2_node = find1(parsed_word_2_tree, ".//node[@pt]")
        if parsed_word_2_node is None:
            continue

        is_neuter = getattval(parsed_word_2_node, "genus") == "onz"
        is_singular = getattval(parsed_word_2_node, "getal") == "ev"
        if is_neuter and is_singular:
            found_nodes.append(node_1)

    return found_nodes


def getdeplusneutcount(
    tree: SynTree, mds: List[Meta], method: Method = defaultmethod) -> int:
    de_plus_neuter_nodes = get_de_plus_neuter_nodes(tree, mds, method)
    return len(de_plus_neuter_nodes)


validwords = {"z'n", 'dees', 'cool', "'k"}
punctuationsymbols = """.,?!:;"'"""


def isvalidword(w: str, mn: MethodName, includealpinonouncompound=True) -> bool:
    if nochildword(w):
        return False
    elif validword(w, mn, includealpinonouncompound=includealpinonouncompound):
        return True
    elif w in punctuationsymbols:
        return True
    elif w in validwords:
        return True
    else:
        return False


def get_ambiguous_word_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    if method.name == asta:
        return []
    nodes = getnodeyield(tree)
    ambiguous_word_nodes = [node for node in nodes if getattval(node, 'word').lower() in disambiguationdict]
    return ambiguous_word_nodes

def countambigwords(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    ambignodes = get_ambiguous_word_nodes(tree, mds, method)
    return len(ambignodes)

def getunknownwordcount(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> int:
    tsw_words = [w for w in tree.xpath('.//node[@pt="tsw"]/@word')]
    unknownwords = [w for w in tsw_words if w in tsw_non_words]
    words = [w for w in tree.xpath('.//node[@pt!="tsw"]/@word')]
    unknownwords += [w for w in words if not isvalidword(w.lower(), methodname) ]
    return len(unknownwords)

wrongposwordxpathtemplate = './/node[@lemma="{word}" and @pt="{pos}"]'
def get_wrong_pos_word_nodes(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> List:
    wrong_pos_words = []
    for word, pos in wrongposwordslexicon:
        wrong_pos_word_xpath = wrongposwordxpathtemplate.format(word=word, pos=pos)
        matches = tree.xpath(wrong_pos_word_xpath)
        for match in matches:
            wrong_pos_words.append(match)
    return wrong_pos_words

def getwrongposwordcount(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> int:
    wrong_pos_word_matches = get_wrong_pos_word_nodes(tree)
    return len(wrong_pos_word_matches)

sucountxpath = './/node[@rel="su" and not(@pt="ww" and @wvorm="inf") and not(node[@rel="hd" and @pt="ww" and @wvorm="inf"])] '
def getsucount(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> int:
    matches = tree.xpath(sucountxpath)
    return len(matches)

# d_hyphen_xpath = './/node[@rel="--" and @pt and @pt!="let"]'
# revised to:
d_hyphen_xpath = """.//node[@rel="--" and @pt!="let"  and @pt!="tsw" and @word!="kijk" and 
                 ancestor::node[@cat="top" and count(node[(@pt!="let" and @pt!="tsw" and @word!="kijk") or @cat]) > 1 
                 ]]"""
def get_double_hyphen_nodes(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> List:
    double_hyphen_nodes = tree.xpath(d_hyphen_xpath)
    return double_hyphen_nodes

def getdhyphencount(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> int:
    matches = get_double_hyphen_nodes(tree, mds, methodname)
    return len(matches)



def get_e_adj_neut_nouns(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> list:
    results = []
    thenodeyield = getnodeyield(tree)
    for i, node in enumerate(thenodeyield):
        nodept = getattval(node, 'pt')
        nodebuiging = getattval(node, 'buiging')
        if nodept == 'adj'and nodebuiging == 'met-e':
            nextnode = thenodeyield[i+1] if i < len(thenodeyield) - 1 else None
            prevnode = thenodeyield[i-1] if i > 0 else None
            if is_neut_sg(nextnode) and not isdefdet(prevnode):
                results.append(node)
    return results


def get_e_adj_neut_noun_count(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> int:
    return len(get_e_adj_neut_nouns(tree, mds, methodname))

localgetcompoundcount = lambda nt, md, mn: getcompoundcount(nt)
getdpcount = lambda nt, md, mn: countav(nt, 'rel', 'dp')
# getdhyphencount = lambda nt, md, mn: countav(nt, 'rel', '--')
getdimcount = lambda nt, md, mn: countav(nt, 'graad', 'dim')
getcompcount = lambda nt, md, mn: countav(nt, 'graad', 'comp')
getsupcount = lambda nt, md, mn: countav(nt, 'graad', 'sup')
# getsucount = lambda nt, md, mn: countav(nt, 'rel', 'su')
complsuxpath = expandmacros(""".//node[node[(@rel="ld" or @rel="pc")  and
                                             @end<=../node[@rel="su"]/@begin and @begin >= ../node[@rel="hd"]/@end] and
                                       not(node[%Rpronoun%])]""")
getcomplsucount = lambda nt, md, mn: len([node for node in nt.xpath(complsuxpath)])

# smainsuxpath = '//node[@cat="smain"  and @begin = node[@rel="su"]/@begin]' # yields unexpected errors (TD12:31; TARSP_08:31)
smainsuxpath =  './/node[@cat="smain" and node[@rel="su"]]'
def get_smain_with_subject_nodes(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> List:
    return tree.xpath(smainsuxpath)

def countsmainsu(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> int:
    matches = get_smain_with_subject_nodes(tree)
    return len(matches)


bad_category_xpath = './/node[@cat and (@cat="du") and node[@rel="dp"]]'
def get_bad_category_nodes(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> List:
    return tree.xpath(bad_category_xpath)


def getbadcatcount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    nodes = get_bad_category_nodes(tree)
    return len(nodes)

#: this is actually valid for all pts except let
noun_1_character_xpath = './/node[@pt!="let"  and string-length(@word)=1]'

def get_single_character_noun_nodes(
    tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    raw_single_character_noun_nodes = tree.xpath(noun_1_character_xpath)
    single_character_noun_nodes = [nd for nd in raw_single_character_noun_nodes if getattval(nd, 'word') not in
                                       digits]
    return single_character_noun_nodes

def getnoun1c_count(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    single_character_noun_nodes = get_single_character_noun_nodes(tree, mds, method)
    return len(single_character_noun_nodes)

adverbial_deze_xpath = './/node[@pt="bw" and @lemma="deze"]'
def get_adverbial_deze_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    adverbal_deze_nodes = tree.xpath(adverbial_deze_xpath)
    return adverbal_deze_nodes

def getdezebwcount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    adverbial_deze_nodes = get_adverbial_deze_nodes(tree, mds, method)
    return len(adverbial_deze_nodes)

unknown_noun_xpath = './/node[@pt="n" and @frame="noun(both,both,both)"]'
def get_unknown_noun(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    unknown_noun_nodes = tree.xpath(unknown_noun_xpath)
    unknown_lemma_nodes = [
        node
        for node in unknown_noun_nodes
        if getattval(node, "lemma") not in validnouns
    ]
    return unknown_lemma_nodes


def getunknownnouncount(nt: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    unknown_noun_nodes = get_unknown_noun(nt, mds, method)
    return len(unknown_noun_nodes)


unknown_name_xpath = './/node[@pt="n" and @frame="proper_name(both)"]'
def get_unknown_name_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    return [node for node in tree.xpath(unknown_name_xpath)]


def getunknownnamecount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    unknown_name_nodes = get_unknown_name_nodes(tree)
    return len(unknown_name_nodes)


main_clause_xpath = './/node[(@cat="smain" or @cat="whq" or (@cat="sv1" and @rel!="body")) and @rel!="cnj"]'
def get_multiple_main_clause_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    """
    Clauses with more than one main clause node are bad.
    """
    nodes = tree.xpath(main_clause_xpath)
    return nodes if len(nodes) > 1 else []


def getmainclausecount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    main_clause_nodes = get_multiple_main_clause_nodes(tree)
    return len(main_clause_nodes)


mainrelxpath = './/node[@rel="--" and (@cat="rel" or @cat="whrel")]'
def mainrelcount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    mainrels = tree.xpath(mainrelxpath)
    return len(mainrels)


topxpath = './/node[@cat="top"]'
def gettopclause(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    tops = tree.xpath(topxpath)
    if tops == []:
        return 0
    top = tops[0]
    realchildren = [child for child in top if getattval(child, 'pt') not in ['let', 'tsw']]
    if len(realchildren) != 1:
        return 0
    else:
       thechild = realchildren[0]
       thechildcat = getattval(thechild, 'cat')
       result = 1 if thechildcat in clausecats else 0
       return result


toe_xpath = './/node[@lemma="toe" or (@lemma="tot" and @vztype="fin")]'
naar_xpath = './/node[@lemma="naar"]'
def get_lonely_toe_nodes(tree: SynTree) -> List:
    toe_matches = tree.xpath(toe_xpath)
    naar_matches = tree.xpath(naar_xpath)
    if toe_matches == []:
        return []
    if len(toe_matches) > 0 and len(naar_matches) == 0:
        return toe_matches
    result = []
    for toe_match in toe_matches:
        if all(
            [
                int(getattval(naar_match, "begin")) > int(getattval(toe_match, "begin"))
                for naar_match in naar_matches
            ]
        ):
            result.append(toe_match)
    return result


def getlonelytoecount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    lonely_toe_matches = get_lonely_toe_nodes(tree)
    return len(lonely_toe_matches)


relative_main_clause_subordinate_order_xpath = """.//node[(@cat="rel" or @cat="whrel" )and @rel="--" and 
                            parent::node[@cat="top"] and 
                            node[@rel="body" and @cat="ssub" and .//node[@word]/@end<=node[@rel="hd" and @pt="ww"]/@begin] ]
"""


def get_relative_main_clause_subordinate_order_nodes(tree: SynTree) -> List:
    return tree.xpath(relative_main_clause_subordinate_order_xpath)


def getrelasmainsubordercount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    matches = get_relative_main_clause_subordinate_order_nodes(tree)
    return len(matches)

words_xpath = """.//node[@word]"""
def get_not_known_by_alpino_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    word_nodes = tree.xpath(words_xpath)
    unknown_word_nodes = [
        node
        for node in word_nodes
        if getattval(node, "word") in wordsunknowntoalpinolexicondict
    ]
    return unknown_word_nodes

def getnotknownbyalpinocount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    unknown_word_nodes = get_not_known_by_alpino_nodes(tree)
    return len(unknown_word_nodes)

def get_basic_replacement_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    word_nodes = tree.xpath(words_xpath)
    basic_replacement_nodes = [
        node
        for node in word_nodes
        if getattval(node, "word").lower() in basicreplacements
    ]
    return basic_replacement_nodes

def getbasicreplaceecount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    basic_replacement_nodes = get_basic_replacement_nodes(tree, mds, method)
    return len(basic_replacement_nodes)


hyphen_xpath = './/node[contains(@word, "-")]'
def get_hyphen_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    hyphen_nodes = tree.xpath(hyphen_xpath)
    return hyphen_nodes

def gethyphencount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    hyphen_nodes = get_hyphen_nodes(tree, mds, method)
    return len(hyphen_nodes)


subjunctive_xpath = './/node[@pvtijd="conj"]'
def get_subjunctive_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    return tree.xpath(subjunctive_xpath)

def getsubjunctivecount(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    subjunctive_nodes = get_subjunctive_nodes(tree)
    return len(subjunctive_nodes)


def gettotaleditdistance(tree: SynTree, metadata: List[Meta], method: Method = defaultmethod) -> int:
    wordlist = getyield(tree)
    totaldistance = 0
    for meta in metadata:
        fullsource = meta.source
        mainsource, subsource = splitsource(fullsource)
        if subsource in replacementsubsources and \
                len(meta.annotationwordlist) == 1 and \
                len(meta.annotatedwordlist) == 1:
            correctword = meta.annotationwordlist[0]
            wrongword = meta.annotatedwordlist[0]
            dst = distance(wrongword, correctword)
            totaldistance += dst
    return totaldistance


nominal_pp_modifier_xpath = """//node[@cat='pp' and node[@rel='hd' and @lemma!='van'] and parent::node[@cat='np']]"""
def get_postnominal_pp_modifier_nodes(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List:
    return tree.xpath(nominal_pp_modifier_xpath)

def getpostnominalppmodcount(
    tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    postnominal_pp_modifier_nodes = get_postnominal_pp_modifier_nodes(tree)
    return len(postnominal_pp_modifier_nodes)


def getmaaradvcount(
    tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod
) -> int:
    initialmaaradvs = tree.xpath(initialmaarvgxpath)
    return len(initialmaaradvs)


def get_predc_v_mismatch_count(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    predc_v_mismatches = get_predc_v_mismatches(tree)
    return len(predc_v_mismatches)


def compute_penalty(nt: SynTree, md: List[Meta], method: Method = defaultmethod) -> Penalty:
    totalpenalty = 0
    for meta in md:
        totalpenalty += meta.penalty
    return totalpenalty

condlist = [f'@lemma="{lemma}"' for lemma in preferably_intransitive_verbs]
cond = ' or '.join(condlist)
intransitive_obj_query = f'.//node[@pt="ww" and @rel="hd" and ({cond}) and ../node[@rel="obj1"]]'
def get_intransitive_obj(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> List[SynTree]:
    result = tree.xpath(intransitive_obj_query)
    return result

def get_intransitive_obj_count(tree: SynTree, mds: List[Meta] = [], method: Method = defaultmethod) -> int:
    intransitive_objs = get_intransitive_obj(tree, mds, method)
    return len(intransitive_objs)

# The constant *criteria* is a list of objects of class *Criterion* that are used, in the order given, to evaluate parses
criteria = [
    Criterion("unknownwordcount", getunknownwordcount, negative, "Number of unknown words"),
    Criterion('Alpinounknownword', getnotknownbyalpinocount, negative, "Number of words unknown to Alpino"),
    Criterion("wrongposwordcount", getwrongposwordcount, negative, "Number of words with the wrong part of speech"),
    Criterion("unknownnouncount", getunknownnouncount, negative, "Count of unknown nouns according to Alpino"),
    Criterion("unknownnamecount", getunknownnamecount, negative, "Count of unknown names"),
  # next one put off gives errors for small clauses in which a modal has been inserted
  #  Criterion("intransitive_obj_count", get_intransitive_obj_count, negative, "Count of number of "
  #                                                                                         "preferably intransitive "
  #                                                                                         "verbs with a direct "
  #                                                                                         "object"),
    Criterion('semincompatibilitycount', semincompatiblecount, negative, "Count of the number of semantic incompatibilities"),
    Criterion('maaradvcount', getmaaradvcount, negative, "Count of number of occurrences of clause initial 'maar' as an adverb"),
    Criterion("ambigcount", countambigwords, negative, "Number of ambiguous words"),
    Criterion("dpcount", getdpcount, negative, "Number of nodes with relation dp"),
    Criterion("dhyphencount", getdhyphencount, negative, "Number of nodes with relation --"),
    Criterion("postcomplsucount", getpostcomplsucount, negative,
              "Number of subjects to the right of a complement in a subordinate clause"),
    Criterion('Postnominal PP modifier count', getpostnominalppmodcount, negative, "Number of postnominal PP modifiers"),
    Criterion('RelativeMainSuborder', getrelasmainsubordercount, negative, 'Number of Main Relative Clauses with subordinate order'),
    Criterion("lonelytoecount", getlonelytoecount, negative, "Number of occurrences of lonely 'toe'"),
    Criterion("noun1c_count", getnoun1c_count, negative, "Number of nouns that consist of a single character"),
    Criterion("Predc - V mismatches", get_predc_v_mismatch_count, negative, "Number of mismatches between "
                                                                            "nominal predicate and copular verb"),
    Criterion("Wrong Adj-Noun agreement", get_e_adj_neut_noun_count, negative, "Adj-Noun agreement Error"),
    Criterion('ReplacementPenalty', getreplacementpenalty, negative, 'Plausibility of the replacement'),
    Criterion('Total Edit Distance', gettotaleditdistance, negative, "Total of the edit distances for all replaced words"),
    # Criterion('Subcatscore', getsubcatprefscore, positive,
    #          'Score based on the frequency of the subcategorisation pattern'),  # put off needs revision
    #    Criterion('mainrelcount', mainrelcount, negative, 'Dislike main relative clauses'),  # removed, leads to worse results
    Criterion("mainclausecount", getmainclausecount, negative, "Number of main clauses"),
    Criterion("topclause", gettopclause, positive, "Single clause under top"),
    Criterion("complsucount", getcomplsucount, negative, ""),
    Criterion("badcatcount", getbadcatcount, negative, "Count of bad categories: du that contains a node with relation dp"),
    Criterion("basicreplaceecount", getbasicreplaceecount, negative, "Number of words from the basic replacements"),
    Criterion("hyphencount", gethyphencount, negative, "Number of words that contain hyphens"),
    Criterion("subjunctivecount", getsubjunctivecount, negative, "Number of subjunctive verb forms"),
    Criterion("smainsucount", countsmainsu, positive, "Count of smain nodes that contain a subject"),
    Criterion("dimcount", getdimcount, positive, "Number of words that are diminutives"),
    Criterion("compcount", getcompcount, positive, "Number of words that are comparatives"),
    Criterion("supcount", getsupcount, positive, "Number of words that are superlatives"),
    Criterion("compoundcount", localgetcompoundcount, positive, "Number of nouns that are compounds"),
    Criterion("sucount", getsucount, positive, "Number of subjects"),
    Criterion("svaok", getsvaokcount, positive, "Number of time subject verb agreement is OK"),
    Criterion("deplusneutcount", getdeplusneutcount, negative, "Number of deviant configurations with de-determiner + neuter noun"),
    Criterion("dezebwcount", getdezebwcount, negative, "Count of 'deze' as adverb"),
    Criterion("penalty", compute_penalty, negative, "Penalty for the changes made")
]
