""""
The module sas_impact ..(to be completed)
"""
import copy
from collections import Counter
from typing import Dict, List, Tuple

from sastadev.allresults import AllResults
from sastadev.conf import settings
from sastadev.methods import Method
from sastadev.resultsbyutterance import getresultsbyutt, getscoresbyutt2
from sastadev.rpf1 import getevalscores, getscores, sumfreq
from sastadev.sastatypes import ResultsDict, UttId

# maximum nuber of utterances to be reviewed
maxutt = 15
n = maxutt
f1target = 95


def sas_impact(results: ResultsDict, silverrefscores: ResultsDict, method: Method):

    # results = allresults.coreresults
    resultsbyutt = getresultsbyutt(results, method)
    silverbyutt = getresultsbyutt(silverrefscores, method)
    silverscoresbyutt = getscoresbyutt2(resultsbyutt, silverbyutt)

    #  compute the comparisonscores and reverse sort them by comparisonscores
    comparisonscoredict = getcomparisonscores(resultsbyutt, silverbyutt)
    silverscorebyuttlist = [(uttid, comparisonscoredict[uttid]) for uttid in silverscoresbyutt if uttid in comparisonscoredict]
    sortedsilverscorebyutt = sorted(silverscorebyuttlist, key= lambda x: x[1], reverse=True)

    originalscores = getscoresallutts(resultsbyutt, silverbyutt)
    # resultscount, refcount, intersectioncount = getcomparisoncounts(resultsbyutt, silverbyutt)
    # originalscores = getevalscores(resultscount, refcount, intersectioncount)

    sasresultsbyutt = copy.deepcopy(resultsbyutt)
    allscores = [('', originalscores)]
    for i in range(n):

        # change the results to the silver reference
        curruttid = sortedsilverscorebyutt[i][0]
        sasresultsbyutt[curruttid] = silverbyutt[curruttid]

        # compute the overall score
        newscores = getscoresallutts(sasresultsbyutt, silverbyutt)
        # resultscount, refcount, intersectioncount = getcomparisoncounts(sasresultsbyutt, silverbyutt)
        # newscores = getevalscores(resultscount, refcount, intersectioncount)
        newf1increase = newscores[2] - allscores[-1][1][2]
        # if newf1increase != sortedsilverscorebyutt[i][1]:
        #    settings.LOGGER.warning(f'Difference in increase: expected {sortedsilverscorebyutt[i][1]}, newf1 = {newf1increase}')
        allscores.append((curruttid, newscores))
        if newscores[2] >= f1target:
            break
    return allscores


def getcomparisonscores(resultsbyutt, refbyutt) -> dict:
    basescore = getscoresallutts(resultsbyutt, refbyutt)
    basef1  = basescore[2]
    resultdict = {}
    for uttid in resultsbyutt:
        if uttid in refbyutt:
            ref = refbyutt[uttid]
        else:
            settings.LOGGER.error(f'Utterance {uttid} in results but not in reference')
            ref = Counter()
        improvedresults = copy.deepcopy(resultsbyutt)
        improvedresults[uttid] = ref
        improvedoverallscore = getscoresallutts(improvedresults, refbyutt)
        improvedf1 = improvedoverallscore[2]
        score = improvedf1 - basef1
        resultdict[uttid] = score

    for uttid in refbyutt:
        if uttid not in resultsbyutt:
            settings.LOGGER.error(f'Utterance {uttid} in reference but not in results')
            ref = refbyutt[uttid]
            improvedresults = copy.deepcopy(resultsbyutt)
            improvedresults[uttid] = ref
            improvedoverallscore = getscoresallutts(improvedresults, refbyutt)
            improvedf1 = improvedoverallscore[2]
            score = improvedf1 - basef1
            resultdict[uttid] = score
    return resultdict

CodesByUtt = Dict[UttId, Counter]
def getscoresallutts(results: CodesByUtt, reference: CodesByUtt) -> Tuple[float, float, float]:
    totaltoomuch = 0
    totaltoofew = 0
    totalok = 0
    for uttid in results:
        if uttid in reference:
            intersection = results[uttid] & reference[uttid]
            toomuch = results[uttid] - intersection
            toofew = reference[uttid] - intersection
            debug = False
            if debug:
                print(uttid, sumfreq(intersection), sumfreq(toomuch), sumfreq(toofew) )
            totalok += sumfreq(intersection)
            totaltoomuch += sumfreq(toomuch)
            totaltoofew += sumfreq(toofew)
        else:
            settings.LOGGER.error(f'Utterance {uttid} in results but not in reference')
            totaltoomuch += sumfreq(results[uttid])
    for uttid in reference:
        if uttid not in results:
            settings.LOGGER.error(f'Utterance {uttid} in reference but not in results')
            totaltoofew += sumfreq(reference[uttid])
    resultscount = totaltoomuch + totalok
    referencecount = totaltoofew + totalok
    overallscore = getevalscores(resultscount, referencecount, totalok)
    return overallscore


def mksas_impactrows(allscores: List[Tuple[str, Tuple[float]]], not100count:int) -> List[str]:
    # a list of the uttides, the F1 scores, plus a header
    uttrow = [score[0] for score in allscores]
    scorerow = [''] + [score[1][2] for score in allscores]
    lrow = len(scorerow) - 2
    header = ['not100count', 'original'] + [f'{str(i+1)} utts reviewed' for i in range(lrow)]
    rows = [[not100count] + uttrow, scorerow]
    return header, rows


def getcomparisoncounts(results: Dict[str, Counter], reference: Dict[str, Counter]) -> Tuple[int, int, int]:
   resultscount = 0
   referencecount = 0
   intersectioncount = 0

   for key in results:
       resultscount += sum(results[key].values())

   for key in reference:
       referencecount += sum(reference[key].values())

   for key in results:
       if key in reference:
           intersection = results[key] & reference[key]
           intersectioncount += sum(intersection.values())
   return resultscount, referencecount, intersectioncount
