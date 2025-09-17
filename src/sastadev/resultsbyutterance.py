'''

The module *resultsbyutterance* provides functions to compute the results and the scores per utterance
'''
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from sastadev.allresults import AllResults
from sastadev.conf import settings
from sastadev.methods import Method
from sastadev.query import query_inform, query_exists
from sastadev.rpf1 import getscores
from sastadev.sastatypes import ExactResultsDict, GoldResults, QId, ResultsDict, Table, UttId

silverf1col = 21

comma = ','
space = ' '

notapplicable = (0.0, 0.0, 0.0)

byuttheader = ['uttid', 'results', 'bronzeref', 'silverref'] + \
              ['binter', 'bresmini', 'brefmini'] + \
              ['cbinter', 'cbresmini', 'cbrefmini'] + \
              ['br', 'bp', 'bf1'] + \
              ['sinter', 'sresmini', 'srefmini'] + \
              ['cs_inter', 'cs_resmini', 'csrefmini'] + \
              ['sr', 'sp', 'sf1'] + ['utterance']

exactresultsbyuttheader = ['uttid', 'resultlist']

ResultsByUttDict = Dict[UttId, List[QId]]
ScoresByUttDict = Dict[UttId, List[Tuple[float, float, float]]]



def getresultsbyutt(results: ResultsDict, method: Method) -> ResultsByUttDict:
    resultsbyuttdict: ResultsByUttDict = defaultdict(Counter)
    for reskey in results:
        qid = reskey[0]
        if qid in method.queries:
            thequery = method.queries[qid]
            if query_inform(thequery) and query_exists(thequery):
                for uttid in results[reskey]:
                    newcounter = Counter({reskey: results[reskey][uttid]})
                    resultsbyuttdict[uttid] += newcounter
    return resultsbyuttdict


def getscoresbyutt2(results: ResultsByUttDict, reference: ResultsByUttDict) -> ScoresByUttDict:
    scores = {}
    doneuttids = []
    for uttid in results:
        doneuttids.append(uttid)
        if uttid in reference:
            scores[uttid] = getscores(results[uttid], reference[uttid])
        else:
            scores[uttid] = notapplicable
            settings.LOGGER.error(f'No reference data for uttid {uttid}')
    for uttid in reference:
        if uttid not in doneuttids:
            scores[uttid] = notapplicable
            settings.LOGGER.error(f'No results data for uttid {uttid}')
    return scores


def getreference(goldscores: GoldResults) -> ResultsDict:
    reference = {}
    for qid in goldscores:
        reference[qid] = goldscores[qid][2]
    return reference


def getscoresbyutt(results: ResultsDict, refscores: ResultsDict) -> ScoresByUttDict:
    debug = False
    resultsbyutt = getresultsbyutt(results)
    # reference = getreference(goldscores)
    referencebyutt = getresultsbyutt(refscores)
    scoresbyutt = getscoresbyutt2(resultsbyutt, referencebyutt)
    if debug:
        for uttid, triple in scoresbyutt.items():
            print(uttid, triple)
    return scoresbyutt


def mkscoresbyuttrows(allresults: AllResults, bronzerefscores: ResultsDict, silverrefscores: ResultsDict,
                      method: Method) -> Table:
    results = allresults.coreresults
    resultsbyutt = getresultsbyutt(results, method)
    bronzebyutt = getresultsbyutt(bronzerefscores, method)
    silverbyutt = getresultsbyutt(silverrefscores, method)
    bronzescoresbyutt = getscoresbyutt2(resultsbyutt, bronzebyutt)
    silverscoresbyutt = getscoresbyutt2(resultsbyutt, silverbyutt)
    resultsuttids = {uttid for uttid in resultsbyutt}
    bronzeuttids = {uttid for uttid in bronzebyutt}
    silveruttids = {uttid for uttid in silverbyutt}
    alluttids = resultsuttids.union(bronzeuttids.union(silveruttids))
    alluttidlist = list(alluttids)
    sortedalluttidlist = sorted(alluttidlist, key=lambda x: int(x))
    bronze_intersections = {uttid: bronzebyutt[uttid] & resultsbyutt[uttid] for uttid in alluttids}
    bronze_ref_minus_inter = {uttid: bronzebyutt[uttid] - bronze_intersections[uttid] for uttid in alluttids}
    bronze_results_minus_inter = {uttid: resultsbyutt[uttid] - bronze_intersections[uttid] for uttid in alluttids}
    silver_intersections = {uttid: silverbyutt[uttid] & resultsbyutt[uttid] for uttid in alluttids}
    silver_ref_minus_inter = {uttid: silverbyutt[uttid] - silver_intersections[uttid] for uttid in alluttids}
    silver_results_minus_inter = {uttid: resultsbyutt[uttid] - silver_intersections[uttid] for uttid in alluttids}
    rows = []
    for uttid in sortedalluttidlist:
        results = mklistelement(uttid, resultsbyutt, method)
        bronzeref = mklistelement(uttid, bronzebyutt, method)
        silverref = mklistelement(uttid, silverbyutt, method)
        bronze_inter = mklistelement(uttid, bronze_intersections, method)
        bronze_resultmin = mklistelement(uttid, bronze_results_minus_inter, method)
        bronze_refmin = mklistelement(uttid, bronze_ref_minus_inter, method)
        bronze_counters = [bronze_intersections[uttid], bronze_results_minus_inter[uttid],
                           bronze_ref_minus_inter[uttid]]
        silver_inter = mklistelement(uttid, silver_intersections, method)
        silver_resultmin = mklistelement(uttid, silver_results_minus_inter, method)
        silver_refmin = mklistelement(uttid, silver_ref_minus_inter, method)
        silver_counters = [silver_intersections[uttid], silver_results_minus_inter[uttid],
                           silver_ref_minus_inter[uttid]]
        bronze_compare_row = [bronze_inter,  bronze_resultmin, bronze_refmin ]
        bronze_size_row = [sum(c.values()) for c in bronze_counters]
        silver_compare_row = [silver_inter,  silver_resultmin, silver_refmin ]
        silver_size_row = [sum(c.values()) for c in silver_counters]


        if uttid in bronzescoresbyutt:
            r, p, f1 = bronzescoresbyutt[uttid]
            bronzescores = [r, p, f1]
        else:
            r, p, f1 = notapplicable
            bronzescores = [r, p, f1]
        if uttid in silverscoresbyutt:
            r, p, f1 = silverscoresbyutt[uttid]
            silverscores = [r, p, f1]
        else:
            r, p, f1 = notapplicable
            silverscores = [r, p, f1]
        utt = space.join(allresults.allutts[uttid]) if uttid in allresults.allutts else '@@'
        fullrow = [uttid, results, bronzeref, silverref] + \
                  bronze_compare_row + bronze_size_row + bronzescores + \
                  silver_compare_row + silver_size_row + silverscores + \
                  [utt]
        rows.append(fullrow)
    return rows


def mklistelement(uttid, acounter, method):
    if uttid in acounter:
        result = counter2str(acounter[uttid], method)
    else:
        result = ''
    return result


def counter2itemlist(scores: Counter, method: Method) -> List[str]:
    resultlist = []
    for reskey in scores:
        qid = reskey[0]
        thequery = method.queries[qid]
        theitem = thequery.item if reskey[0] == reskey[1] else f'{thequery.item}={reskey[1]}'
        sublist = scores[reskey] * [theitem]
        resultlist += sublist
    sortedresultlist = sorted(resultlist)
    return sortedresultlist

def counter2str(scores: Counter, method: Method) -> str:
    resultlist = counter2itemlist(scores, method)
    result = comma.join(resultlist)
    return result

def getexactbyutt(exactresults: ExactResultsDict):
    resultdict = defaultdict(list)
    for qid in exactresults:
        for (uttid, position) in exactresults[qid]:
            resultdict[uttid].append((qid, position))
    return resultdict

def exactbyuttdict2table(exactbyuttdict) -> Table:
    table = []
    for uttid in exactbyuttdict:
        newrow = [uttid, str(exactbyuttdict[uttid])]
        table.append(newrow)
    sortedtable = sorted(table, key=lambda row: int(row[0]))
    return sortedtable

def table2exactbyuttdict(table: Table) -> dict:
    resultdict = {}
    for row in table:
        if len(row) == 2:
            resultdict[str(row[0])] = eval(row[1])
        else:
            # report an error
            pass
    return resultdict
