from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import find1, getattval as gav
from typing import List



def compatible(pvagr: str, getal: str) -> bool:
    result1 = getal == "ev" and pvagr in ["ev", 'met-t', '']
    result2 = getal == "mv" and pvagr in ["mv", '']
    result = result1 or result2
    return result

headverb = """(@rel="hd" and @pt="ww")"""
nppred = """(@cat="np" and @rel="predc" and 
             node[@rel="hd" and @pt="n" ])"""
npred = """(@rel="predc" and @pt="n")"""

predcvxpath1 = f"""//node[node[{headverb} ] and 
                          node[{nppred} and 
                          not(node[@rel="obj1"])  ]
                        ]"""

predcvxpath2 = f"""//node[node[{headverb} ] and 
                          node[ {npred}] and 
                          not(node[@rel="obj1"]) 
                         ]"""



def get_predc_v_mismatches(stree: SynTree) -> List[SynTree]:
    results = []
    matches1 = stree.xpath(predcvxpath1)
    for match in matches1:
        theheadverb = find1(match, f'./node[{headverb}]')
        predc = find1(match, f'./node[{nppred}]/node[@rel="hd"]')
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

