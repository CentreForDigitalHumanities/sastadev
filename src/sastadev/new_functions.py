"""
scratch file to add new functions while the system is running so we do not want to change files that are in use
"""
from lxml import etree
import copy
from sastadev import correctionlabels
from sastadev.basicreplacements import wrongmorph, ervzvariants, basicreplacements
from sastadev.CHAT_Annotation import CHAT_replacement, CHAT_omittedword, CHAT_retracing
from sastadev.celexlexicon import celex2dcoimap
from sastadev.conf import settings
from sastadev.constants import false_start_mode, repetition_mode, self_correction_mode
from sastadev.deregularise import correctinflection, overgen, wrongovergen
from sastadev.filefunctions import get_corrected_tree_fullname
from sastadev.iedims import getjeforms
from sastadev.find_ngram import findmatches, is_def_det, ngram21
from sastadev.lexicon import getwordinfo, getwordposinfo, filledpauseslexicon, informlexicon
from sastadev.macros import expandmacros
from sastadev.metadata import Meta, bpl_delete, mkinsertmeta, mkSASTAMeta, defaultpenalty
from sastadev.missing_det import get_missing_det
from sastadev.normalise_lemma import normaliselemma
from sastadev.queryfunctions import get_replacement_metadata
from sastadev.sastatypes import Relation, SynTree, TreeBank, UttId
from sastadev import sastatok
from sastadev.sastatoken import Token
from sastadev.smallclauses import mkinsertmeta, realword, word
from sastadev.stringfunctions import obstruents, ends_in_fricative, starts_with_fricative
from sastadev.test_functions import test_f, get_stree, test_transform_f
from sastadev.tokenmd import TokenListMD
from sastadev.treebankfunctions import (find1, getattval, get_node, getnodeyield, getorigutt, getsentence,
                                        getxsid, getuttid, get_word,
                                        mktoken2nodemap, mdbasedquery,
                                        mdnameonlyxpathtemplate)
from typing import Callable, List, Optional, Tuple

gav = getattval



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
        for annotation_wordinfo in annotation_wordinfos:
            infl = annotation_wordinfo[2]
            annotation_featdict = celex2dcoimap[infl] if infl in celex2dcoimap else {}
            annotation_pvtijd = annotation_featdict['pvtijd'] if 'pvtijd' in annotation_featdict else ''
            if annotation_wordinfo[0] == annotated_pt and \
                annotation_pvtijd != '' and \
                annotated_pvtijd != '' and \
                annotation_pvtijd != annotated_pvtijd:
                results.append(annotated_node)
                break
    return results

lexical_error_pts = ['n', 'adj', 'ww']
def lexical_error(stree: SynTree) -> List[SynTree]:
    results = []
    replacement_metadata = get_replacement_metadata(stree)
    for replacement_meta in replacement_metadata:
        annotated_list = eval(gav(replacement_meta, 'annotatedwordlist'))
        annotation_list = eval(gav(replacement_meta, 'annotationwordlist'))
        annotated = annotated_list[0]
        if not informlexicon(annotated):
            continue
        annotation = annotation_list[0]
        annotated_node = get_node(stree, replacement_meta, annotation=True)
        annotated_pt = gav(annotated_node, 'pt')
        annotated_lemma = gav(annotated_node, 'original_lemma')
        annotation_lemma = gav(annotated_node, 'lemma')
        if annotated_lemma != '' and annotated_lemma != annotation_lemma and annotated_pt in lexical_error_pts:
            results.append(annotated_node)
    return results


lexical_error_triples = [('test_stap', 'test_stap', '16'),
           ('vklstap', 'STAP_04', '26'),
           ('vklstap', 'STAP_08', '31'),
           ('vklstap', 'STAP_07', '29'),
           ('vklstapfase2', 'STAP_024', '16'),
           ]

sub_tijd_triples = [ ('test_stap', 'test_stap', '11'),
                    ('vklstap', 'STAP_02', '11'),
                    ('vklstap', 'STAP_02', '17'),
                    ('vklstap', 'STAP_02', '34'),
                    ('vklstap', 'STAP_02', '47'),
                    ('vklstap', 'STAP_02', '48'),
                    ('vklstap', 'STAP_02', '47'),
                    ('vklstap', 'STAP_08', '3'),
                    ('vklstap', 'STAP_09', '41')]




main_with_als_xpath = './/node[@cat="smain" and node[@rel="mod" and @cat="cp" and node[@rel="cmp" and @lemma="als"]]]'
def transform_als_dan(in_stree: SynTree) -> SynTree:
    stree = copy.deepcopy(in_stree)
    als_dan_clauses = stree.xpath(main_with_als_xpath)

    for als_dan_clause in als_dan_clauses:
        cp_node = find1(als_dan_clause, './node[@rel="mod" and @cat="cp" and node[@rel="cmp" and @lemma="als"]]')
        cp_nodes = getnodeyield(cp_node)
        if cp_nodes != [] and gav(cp_nodes[-1], 'lemma') == 'dan':
            dan_node = cp_nodes[-1]
            dan_parent = dan_node.getparent()
            dan_parent.remove(dan_node)
            als_dan_clause.append(dan_node)
    return stree

als_dan_triples = [('vklstap', 'stap_04', '44'),
('vklstap', 'stap_05', '25'),
('vklstap', 'stap_05', '26'),
('vklstap', 'stap_08', '31'),
('vkltarsp', 'tarsp_07', '24'),
('handreiking4-12', 'handreiking4-12', '73'),
('handreiking4-12', 'handreiking4-12', '95'),
('handreiking4-12', 'handreiking4-12', '118'),
]

dependent_verb_xpath = ('../node[@rel="vc" and (@cat="inf" or @cat="ppart")]/node[@rel="hd" and @pt="ww"] |'
                        '../node[@rel="vc" and (@cat="ti"]/node[@cat="inf"]/node[@rel="hd" and @pt="ww"]')
def get_ww_dependent_verbs(ww: SynTree) -> List[SynTree]:
    dependent_verbs = ww.xpath(dependent_verb_xpath)
    results = dependent_verbs
    for dependent_verb in dependent_verbs:
        rec_dependent_verbs = get_ww_dependent_verbs(dependent_verb)
        results += rec_dependent_verbs
    return results

def get_retracing_word_count(stree: SynTree, mode=None) -> int:
    result = 0
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
                result += len(retracing_annotationposlist)
    return result

def get_tb_false_start_word_counts(tb: TreeBank) -> List[Tuple[UttId, int]]:
    results = []
    for stree in tb:
        xsid = getxsid(stree)
        fs_count = get_retracing_word_count(stree, mode=false_start_mode)
        results.append((xsid, fs_count))
    return results



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



def is_repetition_retracing(retracing, cleanedtokenisation, cleanedtokenpositions_meta) -> bool:
    return False

CHAT_repetition_code = '[/]'
CHAT_retracing_code = '[//]'
space = ' '

def correct_chat(utt:str) -> str:
    # tokenize the utt
    tokens = sastatok.sasta_tokenize(utt)
    words = [t.word for t in tokens]
    new_words = correct_chat_words(words)
    raw_new_utt = space.join(new_words)
    new_utt = space.join(raw_new_utt.split())
    return new_utt

def correct_chat_words(words:List[str]) -> List[str]:
    # detect (w+) < \1 > [/] different
    # (w+) = repeating_words
    #  \1 = repeated_words
    # different = following_words
    # transform to < \1 > [/] w+
    new_words = []
    for i, word in enumerate(words):
        if word in [CHAT_repetition_code]:
            CHAT_code = word
            repeated_words = find_repeated_words(words[:i])
            l_repeated_words = len(repeated_words)
            if repeated_words != []:
                end = len(i + 1 + l_repeated_words)
                if end < len(words):
                    following_words = [w for w in words[i + 1:end]]
                    following_differs = repeated_words != following_words
                else:
                    following_differs = True
                repeating_words_begin = i - 2 * l_repeated_words - 2
                repeating_words_end = i - l_repeated_words - 2
                if following_differs and repeating_words_begin >= 0:
                        repeating_words = [w for w in words[repeating_words_begin:repeating_words_end]]
                        if repeating_words == repeated_words:
                            new_repeated_words = ['<'] + repeating_words + ['>']
                            rest = correct_chat_words(words[i+1:])
                            new_words = new_words[:repeating_words_begin] + new_repeated_words + [CHAT_code] + repeated_words + rest
                        else:
                            new_words.append(word)
                else:
                    new_words.append(word)
            else:
                new_words.append(word)
        else:
            new_words.append(word)
    return new_words

def find_repeated_words(words:List[str]) -> List[str]:
    repeated_words = []
    if words[-2] != '>':
        return []
    i = len(words) - 2
    start = i
    while i >= 0:
        if words[i] != '<':
            start = i
            i = i - 1
        else:
            break
    result = words[start:-1]
    return result

def clean_utt(utt:str) -> str:
    utt_tokens = sastatok.sasta_tokenize(utt)
    utt_words = [t.word for t in utt_tokens]
    raw_result = space.join(utt_words)
    result = space.join(raw_result.split())
    return result

def test_correct_chat():
    for wrong, raw_correct in correction_tuples:
        correct = clean_utt(raw_correct)
        correction = correct_chat(correct)
        if correction == correct:
            print(f'OK: {wrong} correctly changed into {correction}')
        else:
            print(f'NO: {wrong} changed into \n{correction}\n{correct}')


correction_tuples = [
    ("ik denk van een <van een> [/] geheime kluis <geheime kluis> [/]. [+ VU]",
     "ik denk <van een> [/] van een   <geheime kluis> [/] geheime kluis. [+ VU]"),
    ("of van vroeger deze <deze> [/]? [+ VU]",
     "of van vroeger  <deze> [/] deze? [+ VU]"),
    ("<hij is> [//] hij <hij> [/] moest eigenlijk zeggen ik <ik> [/] doe het zelf. [+ VU]",
     "<hij is> [//]  <hij> [/] hij moest eigenlijk zeggen  <ik> [/] ik doe het zelf. [+ VU]"),
    ("er is <er is> [/] een paadje. [+ VU]",
     " <er is> [/] er is een paadje. [+ VU]"),
    ("dan ga <dan ga> [/] je ruilen. [+ VU]",
     "<dan ga> [/] dan ga je ruilen. [+ VU]"),
    ("<zo> [//] dan <dan> [/] is de andere op de <de> [/] zwarte. [+ VU]",
     "<zo> [//]  <dan> [/] dan is de andere op  <de> [/] de zwarte. [+ VU]")
   ]


def partition(wlist:List[str]) -> List[List[str]]:
    """
    split wlist into a number of identical sublists
    """
    no_sub_parts = [wlist]
    max =  len(wlist) // 2
    partition_found = False
    for i in range(max):
        diff_found = False
        if partition_found:
            return parts
        start = 0
        parts = []
        prev_part = None
        while start < len(wlist):
            new_part = wlist[start:start + i + 1]
            parts.append(new_part)
            if prev_part is not None and prev_part != new_part:
                diff_found = True
                break
            prev_part = new_part
            start += i + 1
        if not diff_found:
            partition_found = True
    if partition_found:
        return parts
    else:
        return no_sub_parts

def convert_partition(parts:List[List[str]]) -> List[str]:
    if parts == []:
        return []
#    elif len(parts) == 1:
#        return parts[0]
    l_part_1 = len(parts[0])
    if l_part_1 > 1:
        prefix = ['<']
        suffix = ['>']
    else:
        prefix = []
        suffix = []
    results = []
    for part in parts[:-1]:
        results += prefix + part + suffix + ['[/]']
    results += prefix + parts[-1] + suffix
    return results

def try_partition():
    the_lists = [['a', 'a', 'a', 'a', 'a'],
             ['a', 'b', 'a', 'b', 'a', 'b'],
             ['a', 'b', 'c', 'a', 'b', 'c'],
             ['a', 'b', 'c', 'd', 'e', 'f'],
             ]
    the_test_lists = the_lists
    for the_list in the_test_lists:
        the_partition = partition(the_list)
        print(the_partition)
        conversion = convert_partition(the_partition)
        print(conversion)
        print(space.join(conversion))





if __name__ == '__main__':
    pass
    # test_f(lexical_error_triples, lexical_error)
    # sub_tijd_triples = [sub_tijd_triples[0], sub_tijd_triples[7]]
    # test_f(sub_tijd_triples, sub_tijd)
    # test_transform_f(als_dan_triples, transform_als_dan)
    # test_correct_chat()
    try_partition()

