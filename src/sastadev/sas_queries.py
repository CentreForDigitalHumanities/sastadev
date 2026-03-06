"""
This module is intended for

* defining functions to select utterances for review by a human expert. These functions are stored in the variable
  *thefunctions*

* defining a function to order the selected utterances. The goal is to sort utterances by their expected impact on the
  performance (the greater, the earlier). Stored in the variable *sortorderfunction*

* defining a criterion to select the utterances that have been analysed. Stored in the variable *criterion*.

So far two criteria have been defined:

* .. autofunction:: synxsid

* .. autofunction:: syn

The variable *criterion* stores the criterion that is actually used for selecting the relevant utterances.

* .. autodata:: criterion

So far, three sortorderfunctions have been defined:

* .. autofunction:: sortorderfunction1

* .. autofunction:: sortorderfunction2

* .. autofunction:: sortorderfunction3


The variable *sortorderfunction* contains the actual value:

* .. autodata:: sortorderfunction


If one has a query, one can turn it into the appropriate function by applying the function *q2f* to the query,
and add a message, and where possible, suggested codes:

* .. autofunction :: q2f

The function *q2f* uses the function *queryf*:

* .. autofunction :: queryf

So far, the following functions for identifying likely mis-analysed utterances have been defined:

* .. autofunction:: checkvcombinationcodes

* .. autodata:: dpverbqueryf

* .. autodata:: postnommodqueryf

* .. autofunction:: getunknownwordnodes

The functions currently in use are stored in the variable *thefunctions*:

.. autodata:: thefunctions


"""
import copy
import re
from sastadev.allresults import mkresultskey, ResultsKey
from sastadev.ASTApostfunctions import mluxqid, samplesizeqid
from sastadev.CHAT_Annotation import CHAT_replacement, CHAT_wordnoncompletion
from sastadev.correctionlabels import (
    alpinoimprovement,
    codareduction,
    contextcorrection,
    dehyphenation,
    emphasis,
    error,
    finalndrop,
    explanationasreplacement,
    inflectionerror,
    informalpronunciation,
    lexicalerror,
    morphologicalerror,
    noncompletion,
    pronunciationvariant,
    regionalform,
    regionalvariantorlexicalerror,
    repetition,
    replacement,
    spellingcorrection,
    unknownword,
    unknownwordsubstitution,
    wrongpronunciation,
)
from sastadev.lexicon import informlexicon
from sastadev.parse_criteria import get_bad_category_nodes, get_multiple_main_clause_nodes, get_unknown_noun, \
    get_double_hyphen_nodes, get_not_known_by_alpino_nodes, get_ambiguous_word_nodes, get_single_character_noun_nodes, \
    get_basic_replacement_nodes, get_subjunctive_nodes, get_de_plus_neuter_nodes, get_adverbial_deze_nodes, \
    isvalidword, get_intransitive_obj, get_wrong_pos_word_nodes
from sastadev.macros import expandmacros
from sastadev.metadata import (
    Meta,
    ALLSAMPLECORRECTIONS,
    BASICREPLACEMENTS,
    SASTA,
    THISSAMPLECORRECTIONS,
)
from sastadev.methods import asta, tarsp
from sastadev.sas_confidence import low_avg_confidence
from sastadev.sas_filter import filterbymetadata, filterbymetadata2
from sastadev.sastatypes import (
    ExactResults,
    ExactResultsDict,
    MethodName,
    SAS_Result_List,
    SynTree,
    TreeBank,
    QId,
    XpathExpression,
    UttId,
)
from sastadev.semantic_compatibility import semincompatiblecount, get_semantically_incompatible_nodes
from sastadev.stringfunctions import consonants, is_interpunction_sequence, monosyllabic
from sastadev.treebankfunctions import ( find1,
    getattval as gav,
    getmeta,
    getxsid,
    getnodeyield,
    getposcat,
    getyieldstr,
)
from typing import Callable, Dict, List, Tuple
from sastadev.tarsp_codes import allVcombinations, allnoVcombinations
from sastadev.tarsp_wgcodes import all_wgnacodes, wgnacodes
from sastadev.methods import Method
from sastadev.suggestVcombinations import predictvcombinations


comma = ","


preferably_mod_words =['hierom', 'daarom']
frequent_infl_suffix_patterns = [fr'[{consonants}]en', fr'[{consonants}]er']


mlureskey = mkresultskey(mluxqid)
samplesizereskey = mkresultskey(samplesizeqid)

adverbial_deze_message = 'Adverbial deze'
ambiguous_word_message = 'Ambiguous word'
bad_categories_message = 'Bad categories'
basic_replacement_message = 'Basic replacement not applied'
de_plus_neuter_message = 'Non-neuter determiner with neuter noun'
inf_subj_message = 'Infinitive probably wrongly parsed as subject'
kijk_query_message = 'The word "kijk" has probably been analysed wrongly'
multiple_main_clause_message = 'Multiple main clauses'
not_known_by_alpino_message = 'Word unknown to the parser'
single_character_noun_message = 'Single character noun'
subjunctive_message = 'Subjunctive'
suspect_obj2_message = 'Likely wrong indirect object'
suspicious_compound_message = 'unlikely compound'
unknown_noun_message = "Unknown noun"
double_hyphen_message = 'Extragrammatical word'
vcombinationmessage = "Missing V-combination codes"
novcombinationmessage = "Missing non verb combination codes"
dpverbquerymessage = "Multiple discourse parts and a verb"
dpquerymessage = "Multiple discourse parts"
unknownwordmessage = "Unknown Word"
wrong_ld_message = "likely wrongly analysed as LD"
conjunct_mismatch_message = "Mismatching conjunct"
subject_less_nominal_ld_message = "Word incorrectly not analysed as a subject"
zijn_loc_predc_message = "likely wrong analysis as locative and nominal predicate"
gaan_obj1_query_message = "Suspect direct object with 'gaan'"
wrong_lemma_pt_message = "Wrong part of speech"
wrong_pt_rel_message = "Wrong grammatical relation"
wat_adj_n_message = "Incorrect modifier of adjective"
rpronoun_mee_adv_message = '"mee" incorrectly analysed as an adverb'
intransitive_obj_message = "Direct object with a (preferably) intransitive verb"
smain_no_subj_message = "No subject found"
wrong_subject_message = "Word wrongly identified as subject"
wrong_object_message = "Word wrongly identified as object"
elliptic_node_message = "Ellipsis applied incorrectly"
rpron_ld_n_vz_message = "Word probably incorrectly analysed as complement of the preposition"
wgnamessage = "Missing code for phrase"
postld_subject_message = "Subjet after a non-clause-initial locative-directional complement"
obj2_ld_message = "Suspect indirect object and locative-directional complement combination"
vz_inf_message = "Suspect preposition with infinitival complement in PP"
date_no_mod_message = "Date expression headed by word is not a modifier"
sem_incompatibility_message = "Semantic incompatibility found"
wrong_pos_word_message = "Wrong part of speech for this word"
wrongly_no_mod_message = "This word is probably incorrectly not analysed as a modifier"
suspicious_participle_message = "participle incorrectly analysed as adjective"


wordreplacementtypes = [
    alpinoimprovement,
    codareduction,
    contextcorrection,
    dehyphenation,
    emphasis,
    error,
    explanationasreplacement,
    finalndrop,
    inflectionerror,
    informalpronunciation,
    lexicalerror,
    morphologicalerror,
    noncompletion,
    regionalform,
    regionalvariantorlexicalerror,
    repetition,
    replacement,
    pronunciationvariant,
    spellingcorrection,
    unknownword,
    unknownwordsubstitution,
    wrongpronunciation,
    CHAT_replacement,
    CHAT_wordnoncompletion,
]


metadata_filter_functions = [get_unknown_noun, get_not_known_by_alpino_nodes, get_ambiguous_word_nodes,
                             get_single_character_noun_nodes, get_basic_replacement_nodes, get_adverbial_deze_nodes,
                             get_de_plus_neuter_nodes]

metadata_filter_function_names = [f.__name__ for f in metadata_filter_functions]

namecondition = " or ".join([f'@name="{wrt}"' for wrt in wordreplacementtypes])

sources = [BASICREPLACEMENTS, ALLSAMPLECORRECTIONS, THISSAMPLECORRECTIONS]
sourcecondition = "or ".join([f'@source="{SASTA}/{source}"' for source in sources])

fullcondition = f"({namecondition}) or ({sourcecondition})"

dpquery = './/[@cat="top" and .//node[@rel="dp"]]'
dpverbquery = './/node[@cat="top" and .//node[@rel="dp"] and .//node[@pt="ww"]]'

postnommodquery = """.//node[@cat="np" and node[@rel="hd" and 
                       @end<=../node[@rel="mod" and (@cat="pp" or @cat="advp" or @pt="bw" or @special="er_loc") 
                       ]/@begin] ]"""
postnommodquerymessage = "Utterance contains postnominal modifiers"


vcombinationsxpath = """.//node[@cat="top" and 
                                .//node[@pt="ww" and @word!="kijk"] and 
                                .//node[@pt!="ww" and @pt!="tsw" and @pt!="let" and 
                                        @pt!="vz" and @pt!="lid" and not(@pt and @rel="svp") ]
                               ]"""
novcombinationsxpath = """.//node[@cat="top" and
                                  not(.//node[@pt="ww"]) and
                                  count(.//node[@pt!="tsw" and @pt!="let" and @word!="kijk" and @pt!="vg"]) >= 2
                                 ]
                         """

kijk_query = './/node[@word="kijk" and (@rel!="tag" and @rel!="--" and @rel!="hd")]'

prefix = "ancestor::alpino_ds/"  # if the query searches for a cat=top node
# prefix = ''                       # if the query searches for alpino_ds

xsidxpath = f'{prefix}descendant::meta[@name="xsid"]/@value'
# synquery = f'{prefix}descendant::meta[@name="syn"] and descendant::meta[@name="role" and @value="Target_Child"]'
synquery = (
    f'{prefix}descendant::meta[@name="xsid"]'  # syn is niet overal, pas dit nog aan
)

compoundsep = "_"


def syn(x: SynTree) -> bool:
    """
    checks whether a syntactic structure has a syn metadata element (annotated for syn)

    :param x:
    :return:
    """
    qresults = x.xpath(synquery)
    result = qresults != []
    return result

def hasxsid(match: SynTree) -> bool:
    """
    checks whether a syntactic structure has  an xsid metadata element

    :param match:
    :return:
    """
    if match.tag == 'alpino_ds':
        xsids = match.xpath('.//meta[@name="xsid"]/@value')
    else:
        xsids = match.xpath(xsidxpath)
    sent = getyieldstr(match)
    xsid = xsids[0] if xsids != [] else '0'
    result = xsid != '0'
    return result



def synxsid(match: SynTree) -> bool:
    """
    checks whether a syntactic structure has a syn metadata element (annotated for syn) and an xsid metadata element

    :param match:
    :return:
    """
    if match.tag == 'alpino_ds':
        xsids = match.xpath('.//meta[@name="xsid"]/@value')
    else:
        xsids = match.xpath(xsidxpath)
    sent = getyieldstr(match)
    xsid = xsids[0] if xsids != [] else '0'
    synresult = syn(match)
    xsidresult = xsid != '0'
    result = synresult and xsidresult
    return result


def queryf(
    tb: TreeBank, query: XpathExpression, messagef: Callable, suggestedcodes: List[str]
) -> List[Tuple[SynTree, str, List[str]]]:
    """
    generic function that can be applied to a treebank given a query, a message and suggestedcodes
    used by *q2f*
    :param tb:
    :param query:
    :param messagef: function to generate a message that explains the reason why this utterance has been selected
    :param suggestedcodes: suggestions for codes
    :return:
    """
    matches = tb.xpath(query)
    results = [(match, messagef(match), suggestedcodes) for match in matches]
    return results


def q2f(query: XpathExpression, messagef: Callable, suggestedcodes: List[str]) -> Callable:
    """
    This function turns a query, message and suggestcodes into a function of the right signature that can be used to
    select utterances. It uses the function *query* for that purpose.
    :param query:
    :param message:
    :param suggestedcodes:
    :return:
    """
    result = lambda tb, uttresults, mn: queryf(tb, query, messagef, suggestedcodes)
    return result


def isrobustname(node: SynTree) -> bool:
    nodeword = gav(node, "word")
    nodept = gav(node, "pt")
    result = nodeword[0].isupper() and (nodept == "n" or nodept == "spec")
    return result


def oldgetnormalisedwnposition(wn: SynTree) -> int:
    topnodes = wn.xpath('./ancestor::alpino_ds/descendant::node[@cat="top"]')
    if topnodes != []:
        topnode = topnodes[0]
        theyield = getnodeyield(topnode)
        for i, node in enumerate(theyield):
            if node == wn:
                return i + 1
    return 0

def getnormalisedwnposition(wn: SynTree) -> int:
    topnodes = wn.xpath('./ancestor::alpino_ds/descendant::node[@cat="top"]')
    if topnodes != []:
        topnode = topnodes[0]
        theyield = getnodeyield(topnode)
        nodemap = {}
        for i, node in enumerate(theyield):
            nodebegin = gav(node, 'begin')
            nodemap[nodebegin] = i
    wnyield = getnodeyield(wn)
    if wnyield != []:
        wnfirstnodebegin = gav(wnyield[0], 'begin')
        result = nodemap[wnfirstnodebegin] + 1 if wnfirstnodebegin in nodemap else 0
        return result
    else:
        return 0


def wnisanASTAX(wn: SynTree, tree: SynTree, exactresult: ExactResults) -> bool:
    wnposition = getnormalisedwnposition(wn)
    if wnposition == 0:
        return False
    foundastax = [
        el
        for el in exactresult
        if el[1] == wnposition and el[0] in [mlureskey, samplesizereskey]
    ]
    result = foundastax != []
    return result


def isnumericordinal(wrd: str) -> bool:
    if wrd.endswith("ste"):
        return wrd[:-3].isnumeric()
    elif wrd.endswith("e"):
        return wrd[:-1].isnumeric()
    else:
        return False

# moved to sastadev.sas_filter
# def filterbymetadata(
#     rawunknownwordnodes: List[SynTree], exactresults: ExactResultsDict, method: Method
# ) -> List[SynTree]:
#     """
#     Removes nodes from a list of nodes if they have already been replaced by
#     SASTA. These can be found in the metadata of the utterance.
#     """
#     unknownwordnodes = []
#     for wn in rawunknownwordnodes:
#         fulltrees = wn.xpath("ancestor::alpino_ds")
#         fulltree = fulltrees[0] if fulltrees != [] else None
#         uttid = getxsid(fulltree)
#         session = getmeta(fulltree, "session")
#         wnbegin = gav(wn, "begin")
#         mdxpath = f"""./ancestor::alpino_ds/descendant::xmeta[({fullcondition}) and @annotationposlist="[{wnbegin}]"]"""
#         replacements = wn.xpath(mdxpath)
#         exactresult = exactresults[uttid] if uttid in exactresults else []
#         if exactresult == []:
#             print(
#                 f'{session}: Empty exactresult: {gav(wn, "word")} in {uttid}: {getyieldstr(fulltree)}'
#             )
#         isASTAX = (
#             wnisanASTAX(wn, fulltree, exactresult) if method.name == asta else False
#         )
#         if replacements == [] and not isASTAX:
#             unknownwordnodes.append(wn)
#     return unknownwordnodes

def get_wrongly_non_mod_nodes(nt: TreeBank, exactresults: ExactResultsDict, method: Method
) -> List[Tuple[SynTree, str, list]]:
    """
    identifies words that are most often modifiers but have been analysed with a different relation
    """
    mn = method.name
    results = []
    rawunknownwordnodes = []
    if nt.tag == 'alpino_ds':
        trees = [nt]
    else:
        trees = nt.xpath('.//alpino_ds')
    for tree in trees:
        uttid = getxsid(tree)
        if uttid == "0":
            continue
        session = getmeta(tree, "session")
        junk = 0
        wordnodes = [wn for wn in tree.xpath('.//node[@pt!="tsw"]')]
        for wordnode in wordnodes:
            lemma = gav(wordnode, 'lemma')
            rel = gav(wordnode, 'rel')
            if rel in ['pc'] and lemma in preferably_mod_words:
                results.append(wordnode)
    return results

suspicious_participles_xpath = """.//node[@pt="ww" and @wvorm="vd"  and @pos="adj"]
"""
def get_suspicious_participles(nt: TreeBank, exactresults: ExactResultsDict, method: Method
) -> List[Tuple[SynTree, str, list]]:
    """
    identifies nodes that are past participles analysed as adjectives
    :param nt:
    :param exactresults:
    :param method:
    :return:
    """
    # breakpoint()
    mn = method.name
    rawresults = []
    for tree in nt:
        uttid = getxsid(tree)
        if uttid == "0":
            continue
        session = getmeta(tree, "session")
        junk = 0
        suspicious_participle_nodes = [wn for wn in tree.xpath(suspicious_participles_xpath)]

        rawresults += [(suspicious_participle_node,
                        get_message_with_word_function(suspicious_participle_message)(suspicious_participle_node),
                        [])
                       for suspicious_participle_node in suspicious_participle_nodes
                      ]
    # exclude geboren for asta
    if mn == asta:
        results = [(n,m,s) for n,m, s in rawresults if gav(n, 'lemma') != 'geboren']
    else:
        results = rawresults
    # no filtering by filterbymetadata(rawresults, exactresults, method.name)
    return results



def getunknownwordnodes(
    nt: TreeBank, exactresults: ExactResultsDict, method: Method
) -> List[Tuple[SynTree, str, list]]:
    """
    identifies nodes that are unknown words and that have not been replaced by SASTA by known words
    :param nt:
    :param _:
    :param method:
    :return:
    """

    mn = method.name
    rawresults = []
    rawunknownwordnodes = []
    for tree in nt:
        uttid = getxsid(tree)
        if uttid == "0":
            continue
        session = getmeta(tree, "session")
        junk = 0
        wordnodes = [wn for wn in tree.xpath('.//node[@pt!="tsw"]')]
        rawunknownwordnodes = [
            wn
            for wn in wordnodes
            if not isvalidword(
                wn.attrib["word"].lower(), mn, includealpinonouncompound=False
            )
            and not compoundsep in wn.attrib["lemma"]
            and not is_interpunction_sequence(gav(wn, 'word'))
            and not isrobustname(wn)
            and gav(wn, "pt") != "tsw"
            and not gav(wn, "word").isnumeric()
            and not isnumericordinal(gav(wn, "word"))
        ]
    rawresults += [
        (unknownwordnode, f'{unknownwordmessage}: {gav(unknownwordnode, "word")}', [])
        for unknownwordnode in rawunknownwordnodes
    ]
    results = filterbymetadata(rawresults, exactresults, method.name)
    return results

# def apply_get_unknown_noun(tb: TreeBank, exact_results: ExactResultsDict, method: Method) -> SAS_Result_List:
#     results = []
#     for tree in tb:
#             hits = get_unknown_noun(tree, exact_results, method)
#             for hit in hits:
#                 wrd = gav(hit, 'word')
#                 message = f'{unknown_noun_message}: {wrd}'
#                 newresult = (hit, message , [])
#                 results.append(newresult)
#     return results

def apply_criterion(criterion: Callable, messagefunction: Callable, suggestfunction: Callable) -> Callable:
    def apply_crit(tb: TreeBank, exact_resultsdict: ExactResultsDict, method: Method) -> SAS_Result_List:
        rawresults = []
        results = []
        for tree in tb:
            hits = criterion(tree, [], method)
            for hit in hits:
                message = messagefunction(hit)
                suggestions = suggestfunction(hit)
                newresult = (hit, message, suggestions)
                rawresults.append(newresult)
            if criterion.__name__ in metadata_filter_function_names:
                results = filterbymetadata(rawresults, exact_resultsdict, method.name)
            else:
                results = filterbymetadata2(rawresults, exact_resultsdict, method.name)
        return results
    return apply_crit


wgnaxpath = """.//node[(@cat="np" or @cat="ap") and 
                       not(node[@rel="hd" and @pt="ww"]) and 
                       count(node) = 3   ]"""
def check_wgna_codes(
    tb: TreeBank, exact_results: ExactResultsDict, method: Method
) -> SAS_Result_List:
    """
    identifies utterances that contain a phrase for which no appropriate code is present
    :param tb:
    :param exact_results:
    :param method:
    :return:
    """
    mn = method.name
    results = []
    if mn != tarsp:
        return []
    for tree in tb:
        xsid = getxsid(tree)
        if xsid is not None and xsid in exact_results:
            sastaresults = exact_results[xsid]
            wgtrees = tree.xpath(wgnaxpath)
            remainingresults = copy.deepcopy(sastaresults)
            for wgtree in wgtrees:
                codesok, remainingresults = checkcodesprecise(remainingresults, all_wgnacodes)
                if not codesok:
                    suggestedcodes = predict_wgnacodes(wgtree, method)
                    messagefunction = get_message_with_word_function(wgnamessage)
                    message = messagefunction(wgtree)
                    results.append((wgtree, message, suggestedcodes))
    return results

def predict_wgnacodes(wgtree, method: Method,  qids=False) -> List[str]:
    if len(wgtree) == 2:
        qidresults = wgnacodes[2]
    elif len(wgtree) == 3:
        qidresults = wgnacodes[3]
    else:
        qidresults = []
    if qids:
        result = [qid for qid in qidresults if qid in method.queries]
    else:
        result = [method.queries[qid].item for qid in qidresults if qid in method.queries]
    return result

def get_suspicious_compounds(nt: TreeBank, exactresults: ExactResultsDict, method: Method) \
        -> List[Tuple[SynTree, str, list]]:
    """
    identifies nodes that are unknown words and that have been analysed as a compound but
    that contain as last component a single syllabel word ending in frequet inflectional suffixes such as -en, -er
    :param nt:
    :param _:
    :param method:
    :return:
    """
    rawresults = []
    for tree in nt:
        uttid = getxsid(tree)
        if uttid == "0":
            continue
        session = getmeta(tree, "session")
        junk = 0
        wordnodes = [wn for wn in tree.xpath('.//node[@pt!="tsw" and @pt!="let"]')]
        for wordnode in wordnodes:
            word = gav(wordnode, 'word')
            lcword = word.lower()
            lemma = gav(wordnode, 'lemma')
            pt = gav(wordnode, 'pt')
            if pt == 'n' and compoundsep in lemma and not informlexicon(lcword):
                parts = lemma.split(compoundsep)
                lastpart = parts[-1]
                if monosyllabic(lastpart):
                    for suffix_pattern in frequent_infl_suffix_patterns:
                        if re.search(suffix_pattern, lastpart):
                            messagefunction = get_message_with_word_function(suspicious_compound_message)
                            result = (wordnode, messagefunction(wordnode), [])
                            rawresults.append(result)
    results = filterbymetadata(rawresults, exactresults, method.name)
    return results


def checkvcombinationcodes(
    tb: TreeBank, exact_results: ExactResultsDict, method: Method
) -> SAS_Result_List:
    """
    identifies utterances that contain a verb and at least one word that can be or be part of a complement or modifier
    :param tb:
    :param exact_results:
    :param method:
    :return:
    """
    mn = method.name
    results = []
    if mn != tarsp:
        return []
    for tree in tb:
        xsid = getxsid(tree)
        if xsid is not None and xsid in exact_results:
            sastaresults = exact_results[xsid]
            wwtrees = tree.xpath(vcombinationsxpath)
            if wwtrees != []:
                codesok = checkcodes(sastaresults, allVcombinations)
                if not codesok:
                    suggestedcodes = predictvcombinations(tree, method)
                    results.append((wwtrees[0], vcombinationmessage, suggestedcodes))
    return results


def checknovcombinationcodes(
    tb: TreeBank, exact_results: ExactResultsDict, method: Method
) -> List[Tuple[SynTree, str, List[str]]]:
    """
    identifies utterances that do not contain a verb and at least two words and checks whether an appropriate code is present
    :param tb:
    :param exact_results:
    :param method:
    :return:
    """
    mn = method.name
    results = []
    if mn != tarsp:
        return []
    for tree in tb:
        xsid = getxsid(tree)
        if xsid is not None and xsid in exact_results:
            sastaresults = exact_results[xsid]
            wwtrees = tree.xpath(novcombinationsxpath)
            if wwtrees != []:
                codesok = checkcodes(sastaresults, allnoVcombinations)
                if not codesok:
                    suggestedcodes = []
                    results.append((wwtrees[0], novcombinationmessage, suggestedcodes))
    return results

def get_smain_without_subject(tree: SynTree, mds:List[Meta], method: Method) \
        -> List[Tuple[SynTree, str, List[str]]]:
    """
    identifies smain nodes containing a non-clause-initial finite verb but no subject
    e.g. vkltarsp, tarsp_01, 33 (kijk, ) die kippen hier staat
    :param tb:
    :param mds:
    :param method:
    :return:
    """
    mn = method.name
    results = []
    xsid = getxsid(tree)
    # smain nodes without a subject
    smains = tree.xpath(""".//node[@cat="smain" and not(node[@rel="su"]) and node[@pt="ww" and @wvorm="pv"]]""")
    for smain in smains:
        nodeyield = getnodeyield(smain)
        if nodeyield != []:
            firstnode = nodeyield[0]
            firstnode_pt = gav(firstnode, 'pt')
            firstnode_rel = gav(firstnode, 'rel')
            firstnode_wvorm = gav(firstnode, 'wvorm')
            if not(firstnode_pt == 'ww' and firstnode_rel == 'hd' and firstnode_wvorm == 'pv'):
                results.append(smain)
    return results

# revise this
# def semantic_incompatibility_criterion(tree: TreeBank, exact_results: ExactResultsDict, method: Method):
#     return sas_criterion(
#         get_semantically_incompatible_nodes(tree, exact_results, method),
#         "Semantic incompatibility",
#         [],
#     )


def checkcodes(
    sastaresults: ExactResults, checkset: List[QId]
) -> bool:  # @@ check dit!
    for result in sastaresults:
        resultqid = result[0][0]
        if resultqid in checkset:
            return True
    return False

def checkcodesprecise(
    sastaresults: ExactResults, checkset: List[QId]
) -> bool:  # @@ check dit!
    remainingresults = copy.deepcopy(sastaresults)
    for result in sastaresults:
        resultqid = result[0][0]
        if resultqid in checkset:
            remainingresults.remove(result)
            return True, remainingresults
    return False, remainingresults



def sortorderfunction1(realwordcount, sentlength, codecount):
    """
    The assumption is that the proportion between *codecount* and *realwordcount*, *realwordcount* and *sentlength* are
    relevant.
    This function sorts on (realwordcount / codecount, realwordcount, sentlength)

    :param realwordcount:
    :param sentlength:
    :param codecount:
    :return:
    """
    rwc_cc = realwordcount / codecount if codecount != 0 else realwordcount + 1
    resulttuple = (rwc_cc, realwordcount, sentlength)
    return resulttuple


def sortorderfunction2(realwordcount, sentlength, codecount):
    """
    The assumption is that the proportion between *codecount* and *realwordcount*, *realwordcount* and *sentlength* are
    relevant.
    This function sorts on (codecount / realwordcount, realwordcount, sentlength)

    :param realwordcount:
    :param sentlength:
    :param codecount:
    :return:
    """
    cc_rwc = codecount / realwordcount if realwordcount != 0 else 0
    resulttuple = (cc_rwc, realwordcount, sentlength)
    return resulttuple

def get_unknown_noun_message(node: SynTree) -> str:
    wrd = gav(node, 'word')
    result = f'{unknown_noun_message}: {wrd}'
    return result

def get_no_mod_message_function(message: str) -> Callable:
    return lambda node: f'{message}: {gav(node, 'word')}'


def get_message_with_word_function(message:str) -> Callable:
    return lambda node: f'{message}: {getyieldstr(node)} ({getnormalisedwnposition(node)})'

def get_governor_of(node: SynTree) -> SynTree:
    governor = find1(node, '../node[@rel="hd"]')
    return governor

def get_wrong_pos_word_message_function(message:str) -> Callable:
    return lambda node: f'{message}: {getyieldstr(node)} as {gav(node, "pt")}'

def get_sem_mismatch_message_function(message:str) -> Callable:
    return lambda node: f'{message}: {getposcat(node)} {getyieldstr(node)} as {gav(node, "rel")} to {gav(get_governor_of(node), 'word')}'

def sortorderfunction3(realwordcount, sentlength, codecount):
    """
    The assumption is that the proportion between *codecount* and *realwordcount*, *realwordcount* and *sentlength* are
    relevant.
    This function sorts on (-codecount / realwordcount, realwordcount, sentlength)

    :param realwordcount:
    :param sentlength:
    :param codecount:
    :return:
    """
    cc_rwc = codecount / realwordcount if realwordcount != 0 else 0
    resulttuple = (-cc_rwc, realwordcount, sentlength)
    return resulttuple

def get_message_function(message: str) -> Callable:
    return lambda m: f'{message}: {getyieldstr(m)}'

#: *dpverbqueryf* defines a search function based on the query *dpverbquery*
dpverbqueryf = q2f(dpverbquery, lambda m: dpverbquerymessage, [])

#: *kijk_queryf* defines a search function based on the query *kijk_query*
kijk_queryf = q2f(kijk_query, get_message_function(kijk_query_message), [])

suspect_obj2_query = """.//node[@rel="obj2" and 
                            not(../node[@rel="obj1"]) and 
                            not(../node[@rel="vc"]) and 
                            not(../node[@rel="su"])]"""

suspect_obj2_queryf = q2f(suspect_obj2_query, get_message_function(suspect_obj2_message), [])

inf_subj_query = """.//node[@pt="ww" and @rel="su" and @wvorm="inf" and @positie="nom"]"""
inf_subj_queryf = q2f(inf_subj_query, get_message_function(inf_subj_message), [])

#: *postnommodqueryf* defines a search function based on the query *postnommodquery*
postnommodqueryf = q2f(postnommodquery, lambda m: postnommodquerymessage, [])

# add: (@rel="cnj" and @pt and @lcat!=../node[@rel="cnj" and @cat!="mwu"]/@cat)
conjunct_mismatch_query = """.//node[(@rel="cnj" and @pt and @pt!=../node[@rel="cnj"]/@pt) or
                                     (@rel="cnj" and @cat and @cat!=../node[@rel="cnj" and @cat]/@cat) or
                                     (@rel="cnj" and @pt and @lcat!=../node[@rel="cnj" and @cat!="mwu"]/@cat)]"""
conjunct_mismatch_queryf = q2f(conjunct_mismatch_query, get_message_function(conjunct_mismatch_message), [])

subject_less_nominal_ld_query = """.//node[@rel="ld" and 
       (@pt="n" or (@pt="vnw" and (not(@special) or @special!="er_loc")) or @cat="np") and 
        not(../node[@rel="su"])]"""
subject_less_nominal_ld_queryf = q2f(subject_less_nominal_ld_query, get_message_function(
    subject_less_nominal_ld_message), [])

zijn_loc_predc_query = """.//node[node[@rel="hd" and @pt="ww" and @lemma="zijn"] and 
                  node[@rel="predc" and (@pt="n" or @cat="np")] and 
                  node[@rel="mod" and (@frame="loc_adverb" or  @frame="er_loc_adverb")]]"""
zijn_loc_predc_queryf = q2f(zijn_loc_predc_query, get_message_function(zijn_loc_predc_message), [])

gaan_obj1_query = """.//node[@pt="ww" and @lemma="gaan" and ../node[@rel="obj1"]]"""
gaan_obj1_queryf = q2f(gaan_obj1_query, get_message_function(gaan_obj1_query_message), [])




# transform trees that match this query
# beetje_count_query  = """//node[@cat="np" and node[@rel="det" and @lemma="een"] and node[@rel="hd" and @lemma="beet"
# and @end<= ../node[@rel="mod"]/@begin] and node[@rel="mod" and @pt and @graad="dim"]]"""


#: The variable *sortorderfunction* specifies the function that orders the selected utterances
sortorderfunction = sortorderfunction3

unexpanded_wrong_ld_query = """//node[@rel="ld" and 
                                      not(%Rpronoun%) and 
                                      (@pt="vnw" or @pt="n" or @cat="np") and 
                                      not(../node[@rel="su"])]"""
wrong_ld_query = expandmacros(unexpanded_wrong_ld_query)
wrong_ld_queryf = q2f(wrong_ld_query, get_message_function(wrong_ld_message), [])

wrong_lemma_pt_pairs = [('staat', 'n'), ('pas', 'n'), ('op_zitten', 'ww'), ('hoe', 'n'), ('maak', 'n')]
wrong_lemma_pt_condition_list = [f'(@pt="{pt}" and @lemma="{lemma}")' for lemma, pt in wrong_lemma_pt_pairs]
wrong_lemma_pt_condition = f'{" or ".join(wrong_lemma_pt_condition_list)}'
wrong_lemma_pt_query = f""".//node[{wrong_lemma_pt_condition}]"""
wrong_lemma_pt_queryf = q2f(wrong_lemma_pt_query, get_message_with_word_function(wrong_lemma_pt_message), [])

wrong_pt_rel_pairs = [('tw', 'ld')]
wrong_pt_rel_condition_list = [f'(@pt="{pt}" and @rel="{rel}")' for pt, rel in wrong_pt_rel_pairs]
wrong_pt_rel_condition = f'{" or ".join(wrong_pt_rel_condition_list)}'
wrong_pt_rel_query = f""".//node[{wrong_pt_rel_condition}]"""
wrong_pt_rel_queryf = q2f(wrong_pt_rel_query, get_message_with_word_function(wrong_pt_rel_message), [])
wat_adj_n_query = """.//node[@lemma="wat" and @rel="mod" and ../node[@rel="hd"] and parent::node[@rel="mod" and 
parent::node[@cat="np"]]]"""
wat_adj_n_queryf = q2f(wat_adj_n_query, get_message_with_word_function(wat_adj_n_message), [])

rpronoun_mee_adv_query = """.//node[@rel="mod" and @pt="bw" and @lemma="mee" and 
                                    ../node[@rel="hd" and @pt="ww"] and 
                                    ../node[@pt="vnw" and @lemma="hier"]]"""
rpronoun_mee_adv_queryf = q2f(rpronoun_mee_adv_query, get_message_with_word_function(rpronoun_mee_adv_message), [])

wrong_subject_query = """.//node[@rel="su" and (@pt="lid" or @pt="tsw")]"""
wrong_subject_queryf = q2f(wrong_subject_query, get_message_with_word_function(wrong_subject_message), [])

wrong_object_query = """.//node[@rel="obj1" and (@pt="lid" or @pt="tsw")]"""
wrong_object_queryf = q2f(wrong_object_query, get_message_with_word_function(wrong_object_message), [])

elliptic_node_query = expandmacros(""".//node[%ellipticgap%]""")
elliptic_node_queryf = q2f(elliptic_node_query, get_message_function(elliptic_node_message), [])

rpron_ld_n_vz_query = expandmacros(""".//node[node[@rel="mod" and %Rpronoun%] and 
                                              node[@rel="ld" and (@pt="vnw" or @pt="n")] and 
                                              node[@pt="vz"]]""")
rpron_ld_n_vz_queryf = q2f(rpron_ld_n_vz_query, get_message_with_word_function(rpron_ld_n_vz_message), [])

postld_subject_query = """.//node[@rel="su" and @begin >= ../node[@rel="ld" and (@cat or @word) and @begin != 
parent::node[@cat="smain"]/@begin]/@end]"""
postld_subject_queryf = q2f(postld_subject_query, get_message_with_word_function(postld_subject_message), [])

obj2_ld_query = """.//node[node[@rel="obj2"] and node[@rel="ld"]]"""
obj2_ld_queryf = q2f(obj2_ld_query, get_message_function(obj2_ld_message), [])

vz_inf_query = """.//node[@cat="pp" and node[@rel="hd" and @pt="vz"] and node[@rel="obj1" and @pt="ww"]]"""
vz_inf_queryf = q2f(vz_inf_query, get_message_with_word_function(vz_inf_message), [])

date_no_mod_query = expandmacros(""".//node[(%monthname% or %dayname%) and 
       (@rel!="mod" and 
	    not(@rel="obj1" and parent::node[@cat="pp"])	  and
		not(@rel="hd" and parent::node[@cat="np" and @rel="obj1" and parent::node[@cat="pp"]]) and
        not(@rel="hd" and parent::node[@rel="mod"]) and 
        not(@rel="cnj" and parent::node[@rel="mod"]) and 
        not(@rel="hd" and parent::node[@rel="cnj" and parent::node[@rel="mod"]]) and
		not(@rel="mwp" and parent::node[@rel="mod"]) and
		not(@rel="mwp" and parent::node[@rel="obj1" and parent::node[@cat="pp"]])
       )]""")
date_no_mod_queryf = q2f(date_no_mod_query, get_message_with_word_function(date_no_mod_message), [])

#: the constant *criteria* is a dictionary mapping names to functions to identify sentences that
#: must be selected for review by a human expert
criteria: Dict[str, Callable] =\
{
  "unknown_noun": apply_criterion(get_unknown_noun, get_message_with_word_function(unknown_noun_message),
                                   lambda x: []),
    "double_hyphen": apply_criterion(get_double_hyphen_nodes, get_message_with_word_function(
                       double_hyphen_message), lambda x: []),
    "multiple_main_clauses": apply_criterion(get_multiple_main_clause_nodes, lambda x: multiple_main_clause_message,
                                   lambda x: []),
    "bad_categories": apply_criterion(get_bad_category_nodes, lambda x: bad_categories_message, lambda x: []),
    "not_known_by_alpino": apply_criterion(get_not_known_by_alpino_nodes, lambda x: not_known_by_alpino_message,
                                     lambda x: []),
    "ambiguous_word": apply_criterion(get_ambiguous_word_nodes, get_message_with_word_function(ambiguous_word_message),
                     lambda x: []),
    "single_character_content_word": apply_criterion(get_single_character_noun_nodes, lambda x:
    single_character_noun_message, lambda x: []),
    "basic_replacement_word": apply_criterion(get_basic_replacement_nodes, get_message_with_word_function(
        basic_replacement_message), lambda x: []),
    "subjunctive": apply_criterion(get_subjunctive_nodes, lambda x: subjunctive_message, lambda x: []),
    "de_pls_neuter": apply_criterion(get_de_plus_neuter_nodes,  lambda x: de_plus_neuter_message, lambda x: []),
    "adverbial_deze": apply_criterion(get_adverbial_deze_nodes, lambda x: adverbial_deze_message, lambda x: []),
    "V_combinations": checkvcombinationcodes,
    "No_V_combinations": checknovcombinationcodes,
    "DP_verb": dpverbqueryf,
    "Post_nom_mod": postnommodqueryf,
    "unknown_word": getunknownwordnodes,
    "kijk_query": kijk_queryf,
    "suspect_obj2": suspect_obj2_queryf,
    "inf_subj": inf_subj_queryf,
    "conjunct_mismatch": conjunct_mismatch_queryf,
    "subjectless_nominal": subject_less_nominal_ld_queryf,
    "zijn_loc_predc": zijn_loc_predc_queryf,
    # "gaan_obj1": gaan_obj1_queryf,    # covered by get_intransitive_obj
    "wrong_lemma_pt": wrong_lemma_pt_queryf,
    "wrong_pt_rel": wrong_pt_rel_queryf,
    "wat_adj_n": wat_adj_n_queryf,           # still to be tested
    "rpronoun_mee_adv": rpronoun_mee_adv_queryf,
    "intransitive_obj": apply_criterion(get_intransitive_obj, lambda x: intransitive_obj_message, lambda x: []),
    "smain_no_subj": apply_criterion(get_smain_without_subject, lambda x: smain_no_subj_message, lambda x: []),
    "wrong_subject": wrong_subject_queryf,
    "wrong_object": wrong_object_queryf,
    "elliptic_node": elliptic_node_queryf,
    "rpron_ld_n_vz": rpron_ld_n_vz_queryf,
    "postld_subject": postld_subject_queryf,
    "obj2_ld": obj2_ld_queryf,
    "vz_inf" : vz_inf_queryf,
    "date_no_mod": date_no_mod_queryf,
"semincompatibilitycount": apply_criterion(get_semantically_incompatible_nodes,
                                                       get_sem_mismatch_message_function(sem_incompatibility_message),
                                                       lambda x: []),
    "wrong_pos": apply_criterion(get_wrong_pos_word_nodes, get_wrong_pos_word_message_function(wrong_pos_word_message),
                                 lambda x: []),
    "preferably_mod": apply_criterion(get_wrongly_non_mod_nodes, get_message_with_word_function(wrongly_no_mod_message),
                                      lambda x: []),
    "unlikely_compound": get_suspicious_compounds,
    "suspicious participle": get_suspicious_participles

   # "Low Confidence": low_avg_confidence  # temporarily put off gives too many unwanted results

}

# for testing

# criteria = {                      "suspicious participle": get_suspicious_participles
#
#  }

# from Xander:
# {
# "checkvcombinationcodes": checkvcombinationcodes,
# "dpverbquery": dpverbqueryf,
# "postnommodquery": postnommodqueryf,
# "unknownwordnodes": unknown_word_criterion, # Very slow!
# "maar_adv_count": maar_adv_count_criterion,
# "Alpinounknownword": alpino_unknown_word_criterion,
# "wrongposwordcount": wrong_pos_word_criterion,
# "unknownnouncount": unknown_noun_criterion,
# "unknownnamecount": unknown_name_criterion,
# "semincompatibilitycount": semantic_incompatibility_criterion,
# "ambigcount": ambiguous_words_criterion,
# "dpcount": dp_criterion,
# "dhyphencount": double_hyphen_criterion
# "postcomplsucount": post_complement_in_subordinate_clause
# "relativemainsuborder": main_relative_clause_with_subordinate_order_criterion,
# "lonelytoecount": lonely_toe_criterion,
# "noun1c_count": single_character_noun_criterion,
# "mainclausecount": multiple_main_clause_criterion,
# "badcatcount": bad_categories_criterion,
# "basicreplaceecount": basic_replacement_criterion,
# "hyphencount": hyphen_criterion,
# "subjunctivecount": subjunctive_criterion,
# "smainsucount": smain_with_subject_criterion,
# "deplusneutcount": de_plus_neuter_criterion,
# "dezebwcount": adverbial_deze_criterion,
# }


# criteria = { "preferably_mod": apply_criterion(get_wrongly_non_mod_nodes,
#                                                get_no_mod_message_function(wrongly_no_mod_message),
#                                                lambda x: [])}   # for # testing

#: *criterion* contains a function to select the utterances that have been analysed
criterion = synxsid
