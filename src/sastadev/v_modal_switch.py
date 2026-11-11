import copy

from sastadev import correctionlabels
from sastadev.find_ngram import findmatches, ngram23
from sastadev.lexicon import filledpauseslexicon
from sastadev.metadata import bpl_switch_order, Meta, defaultpenalty, SASTA
from sastadev.sastatypes import SynTree, UttId
from sastadev.tokenmd import TokenListMD
from sastadev.treebankfunctions import getattval, getnodeyield
from typing import List, Tuple


def v_modal_switch(uttmd: TokenListMD, stree: SynTree, uttid: UttId) -> List[TokenListMD]:
    leaves = getnodeyield(stree)
    cleanleaves = [leave for leave in leaves if getattval(leave, 'word') not in filledpauseslexicon]
    cleanwordlist = [getattval(leave, 'word') for leave in cleanleaves]
    matches = findmatches(ngram23, cleanleaves)
    results = switch_v_modal(uttmd, matches)
    return results


def switch_v_modal(uttmd: TokenListMD, matches: List[Tuple[int, int]]) -> List[TokenListMD]:
    if matches == []:
        return []
    metadata = uttmd.metadata
    tokens = uttmd.tokens
    m0 = matches[0][0] + 1
    newtokens = []
    for i, token in enumerate(tokens):
        if m0 == i:
            newtoken = copy.deepcopy(token)
            newtoken.pos = tokens[i+1].pos
            newtokens.append(newtoken)
        elif m0 + 1 == i:
            newtoken = copy.deepcopy(token)
            newtoken.pos = tokens[i-1].pos
            newtokens.append(newtoken)
        else:
            newtokens.append(token)
    sortednewtokens = sorted(newtokens, key=lambda x: x.pos)
    newmetadata = copy.deepcopy(metadata)
    # @@ make new meta and add it to newmetadata
    newmeta = Meta(name=correctionlabels.order_switch, value=correctionlabels.v_modal_switch_label,
                   annotatedwordlist=[tokens[m0].word, tokens[m0+1].word],
                   annotatedposlist=[tokens[m0].pos, tokens[m0+1].pos],
                   annotationwordlist = [sortednewtokens[m0].word, sortednewtokens[m0+1].word],
                   annotationposlist=[sortednewtokens[m0].pos, sortednewtokens[m0+1].pos],
                   cat=correctionlabels.syntax,
                   source= SASTA,
                   backplacement=bpl_switch_order,
                   penalty = defaultpenalty
    )
    newmetadata.append(newmeta)
    newuttmd = TokenListMD(sortednewtokens, newmetadata)
    rest_results1 = switch_v_modal(uttmd, matches[1:])
    rest_results2 = switch_v_modal(newuttmd, matches[1:])
    all_results = [newuttmd] + rest_results1 + rest_results2
    return all_results
