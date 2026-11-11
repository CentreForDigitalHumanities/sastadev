from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from sastadev.methods import Method
from sastadev.resultsbyutterance import getresultsbyutt
from sastadev.sas_meta import SAS_Result
from sastadev.sastatypes import ResultsDict, UttId

def sas_adapt_results(coreresults: ResultsDict,
                     sasresults: List[Tuple[UttId, SAS_Result]],
                     silverresults: ResultsDict,
                     method: Method) -> ResultsDict:
    resultsbyuttid = getresultsbyutt(coreresults, method)
    silverresultsbyuttid = getresultsbyutt(silverresults, method)
    newresultsbyuttid = {}
    sasresults_uttids = [uttid for uttid, _ in sasresults]
    for uttid in resultsbyuttid:
        if uttid in sasresults_uttids:
            newresultsbyuttid[uttid] = silverresultsbyuttid[uttid]
        else:
            newresultsbyuttid[uttid] = resultsbyuttid[uttid]
    adapted_results = getresultsbyreskey(newresultsbyuttid)
    return adapted_results

def getresultsbyreskey(resultsbyuttid: Dict[UttId, Counter]) -> ResultsDict:
    resultsbyreskeydict = defaultdict(Counter)
    for uttid in resultsbyuttid:
        for reskey in resultsbyuttid[uttid]:
            newcounter = Counter({uttid: resultsbyuttid[uttid][reskey]})
            resultsbyreskeydict[reskey] += newcounter
    return resultsbyreskeydict


def tryme():
    resultsbyuttid = {'3': {('T001', 'T001'): 4, ('T002', 'T002'): 2}, '4': {('T001', 'T001'): 5, ('T002', 'T002'): 3}}
    resultsbyreskey = getresultsbyreskey(resultsbyuttid)
    print(resultsbyreskey)

if __name__ == '__main__':
    tryme()