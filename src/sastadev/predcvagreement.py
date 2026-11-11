from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import find1, getattval as gav
from typing import List

measure_lemmas = ['euro', 'graad', 'dollar', 'pond', 'meter', 'centimeter']

def compatible(pvagr: str, getal: str) -> bool:
    result1 = getal == "ev" and pvagr in ["ev", 'met-t', '']
    result2 = getal == "mv" and pvagr in ["mv", '']
    result = result1 or result2
    return result

headverb = """(@rel="hd" and @pt="ww")"""
nppred = """(@cat="np" and @rel="predc" and 
             node[@rel="hd" and @pt="n" ])"""
npred = """(@rel="predc" and @pt="n")"""

predcvxpath1 = f""".//node[node[{headverb} ] and 
                          node[{nppred} and 
                          not(node[@rel="obj1"])  ]
                        ]"""

predcvxpath2 = f""".//node[node[{headverb} ] and 
                          node[ {npred}] and 
                          not(node[@rel="obj1"]) 
                         ]"""


def is_head_of_meas_phrase(noun: SynTree) -> bool:
    noun_frame = gav(noun, 'frame')
    is_meas_lemma = 'bare_meas' in noun_frame or 'meas_mod_noun' in noun_frame
    count_sisters = noun.xpath("""../node[(@pt="tw" and @numtype="hoofd") or (@pt="lid" and @lwtype="onbep")]""")
    result = is_meas_lemma and count_sisters != []
    return result


def get_predc_v_mismatches(stree: SynTree) -> List[SynTree]:
    results = []
    matches1 = stree.xpath(predcvxpath1)
    for match in matches1:
        theheadverb = find1(match, f'./node[{headverb}]')
        predc = find1(match, f'./node[{nppred}]/node[@rel="hd"]')
        if is_head_of_meas_phrase(predc):
            continue
        pvagr = gav(theheadverb, 'pvagr')
        getal = gav(predc, 'getal')
        if not compatible(pvagr, getal):
            results.append(match)

    matches2 = stree.xpath(predcvxpath2)
    for match in matches2:
        theheadverb = find1(match, f'./node[{headverb}]')
        predc = find1(match, f'./node[{npred}]')
        pvagr = gav(theheadverb, 'pvagr')
        getal = gav(predc, 'getal')
        if not compatible(pvagr, getal):
            results.append(match)
    return results

def get_predc_v_mismatching_heads(stree: SynTree) -> List[SynTree]:
    s_results = get_predc_v_mismatches(stree)
    v_results = []
    for s_result in s_results:
        theheadverb = find1(s_result, f'./node[{headverb}]')
        if theheadverb is not None:
            v_results.append(theheadverb)
        else:
            v_results.append(s_result)
    return v_results