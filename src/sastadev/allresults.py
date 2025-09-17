from collections import defaultdict
from typing import Any, Callable, Counter, Dict, List, Tuple, Union

from sastadev.sastatypes import (ExactResult, ExactResults, FileName, Matches,
                                 QId, Query, ResultsCounter, ResultsKey, SynTree, UttId,
                                 UttWordDict)
from sastadev.treebankfunctions import getattval as gav

slash = '/'
reskeysep = slash



# class ResultsKey:  # we do not use it anymore because two instantiations with the same value are dfferent objects
#     def __init__(self, qid: QId, value: str = None):
#         self.qid: QId = qid
#         self.value: str = str(qid) if value is None else value
#
#     def __str__(self):
#         return f'{self.qid}/{self.value}'
#
#     def __repr__(self):
#         return f"ResultsKey('{self.qid}','{self.value}')"


def mkresultskey(qid: QId, value: str = None) -> Tuple[QId, str]:
    if value is None:
        return (qid, str(qid))
    else:
        return (qid, value)


def showreskey(reskey):
    return f'{reskey[0]}{reskeysep}{reskey[1]}'


def reskeystr2reskey(reskeystr: str) -> ResultsKey:
    parts = reskeystr.split(reskeysep)
    result = tuple(parts)
    return result


def getqueryid(reskeystr: str) -> QId:
    reskey = reskeystr2reskey(reskeystr)
    result = reskey[0]
    return result


class AllResults:
    def __init__(self, uttcount, coreresults, exactresults, postresults, allmatches, filename, analysedtrees, allutts, annotationinput=False):
        self.uttcount: int = uttcount
        self.coreresults: Dict[ResultsKey, ResultsCounter] = coreresults
        self.exactresults: ExactResultsDict = exactresults
        self.postresults: Dict[ResultsKey, Any] = postresults
        self.allmatches: MatchesDict = allmatches
        self.filename: FileName = filename
        self.analysedtrees: List[Tuple[UttId, SynTree]] = analysedtrees
        self.allutts: UttWordDict = allutts
        self.annotationinput: bool = annotationinput


CoreQueryFunction = Callable[[SynTree], List[SynTree]]
PostQueryFunction = Callable[[AllResults, SynTree], List[SynTree]]
QueryFunction = Union[CoreQueryFunction, PostQueryFunction]


def scores2counts(scores: Dict[ResultsKey, Counter]) -> Dict[QId, int]:
    '''
    input is a dictionary of Counter()s
    output is a dictionary of ints
    '''
    counts = {}
    for el in scores:
        countval = len(scores[el])
        counts[el] = countval
    return counts


CoreQueryFunction = Callable[[SynTree], List[SynTree]]
PostQueryFunction = Callable[[AllResults, SynTree], List[SynTree]]
QueryFunction = Union[CoreQueryFunction, PostQueryFunction]

MatchesDict = Dict[Tuple[ResultsKey, UttId], Matches]
ExactResultsDict = Dict[ResultsKey, ExactResults]  # qid
ExactResultsFilter = Callable[[Query, ExactResultsDict, ExactResult], bool]


def matches2exactresults(matchesdict: MatchesDict) -> ExactResultsDict:
    exactresultsdict = defaultdict(list)
    for resultskey, uttid in matchesdict:
        for match in matchesdict[(resultskey, uttid)]:
            position = getposition(match[0])
            exactresultsdict[resultskey].append((uttid, position))
    return exactresultsdict


def getposition(node: SynTree) -> int:
    result = int(gav(node, 'begin')) + 1
    return result
