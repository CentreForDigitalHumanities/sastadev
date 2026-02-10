from collections import Counter, defaultdict
from dataclasses import dataclass
import os

from sastadev import allresults
from sastadev.allresults import AllResults, mkresultskey, showreskey
from sastadev.conf import settings
from sastadev.constants import resultsfolder
from sastadev.counterfunctions import counter2liststr
from sastadev.filefunctions import get_dataset_samplename, make_filelist
from sastadev.methods import Method
from sastadev.mismatches import exactmismatches, informcol, literalmissedmatches, samplecol, uttidcol
from sastadev.query import (Query, is_preorcore, post_process, query_exists,
                            query_inform)
from sastadev.reduceresults import exact2results, reduceexactgoldscores
from sastadev.rpf1 import getevalscores, getscores, sumfreq
from sastadev.sample_uttid_tuples import get_samplename_uttids_tuples
from sastadev.sastacore import dopostqueries
from sastadev.sastatypes import (ExactResultsDict, FileName, MatchesDict, QId, ResultsCounter, ResultsKey, Row, Table,
                                 UttId, UttWordDict)
from sastadev.stringfunctions import  sf
from typing import Any, Dict, List, Tuple

na = 'na'
tab = '\t'

@dataclass
class AnalysisTableParameters:
    allresults: AllResults
    exactgoldscores: ExactResultsDict
    exactsilverscores: ExactResultsDict
    themethod: Method
    invalidqueries: List[QId]
    platinuminfilefound: bool
    allannutts: UttWordDict
    infilename: FileName
    reffilename: FileName
    qid_reskeys:  List[Tuple[QId, ResultsKey]]

def erow(cnt: int) -> List[str]:
    result = []
    for i in range(cnt):
        result.append('')
    return result

def getpostval(qid, thepostresults):
    if qid in thepostresults:
        result = thepostresults[qid]
    else:
        result = ''
    return result


def getsortedgolduttscore(reskey: ResultsKey, goldscores) -> str:
    if reskey in goldscores:
        # (goldlevel, golditem, goldcounter) = goldscores[queryid]
        goldcounter = goldscores[reskey]
        goldcount = sumfreq(goldcounter)
        sortedgolduttstr = counter2liststr(goldcounter)
    else:
        goldcount = 0
        sortedgolduttstr = ''
    return sortedgolduttstr

# @@ added invalidqueries as an additional parameter
def updatequerycounts(queryid, themethod, invalidqcount, undefinedqcount, invalidqueries) -> Tuple[str, int, int]:
    thequery = themethod.queries[queryid]
    if query_exists(thequery):
        if queryid not in invalidqueries:
            qex = 'yes'
        else:
            qex = 'invalid'
            invalidqcount += 1
    else:
        qex = 'no'
        undefinedqcount += 1
    return qex, invalidqcount, undefinedqcount


def getfullscoreandplatinumstr(reskey, themethod, theresults, resultstr, goldscores,
                               platinuminfilefound, platinumresults, sortedgolduttstr, qex, invalidqueries) -> Tuple[Row, Row]:
    queryid = reskey[0]
    thequery = themethod.queries[queryid]
    if reskey in goldscores:
        goldcounter = goldscores[reskey]
        goldcount = sumfreq(goldcounter)
    else:
        goldcount = 0

    if query_exists(thequery) and queryid not in invalidqueries:
        # print(queryid, file=logfile)
        if reskey in goldscores:
            goldcounter = goldscores[reskey]
        else:
            goldcounter = Counter()
        (recall, precision, f1score) = getscores(theresults, goldcounter)
        liststargoldstr = counter2liststr(theresults & goldcounter)
        goldminustheresults = goldcounter - theresults
        goldminusliststr = counter2liststr(goldminustheresults)
        theresultsminusgold = theresults - goldcounter
        listminusgoldstr = counter2liststr(theresultsminusgold)
        if platinuminfilefound and reskey in platinumresults:
            theplatinumresults = platinumresults[reskey]
            sortedplatinumliststr = counter2liststr(theplatinumresults)
            liststarplatinumstr = counter2liststr(
                theresults & theplatinumresults)
            platinumminusliststr = counter2liststr(
                theplatinumresults - theresults)
            listminusplatinumliststr = counter2liststr(
                theresults - theplatinumresults)
            (platinumrecall, platinumprecision, platinumf1score) = getscores(
                theresults, theplatinumresults)

            goldstarplatinumstr = counter2liststr(
                goldcounter & theplatinumresults)
            platinumminusgoldstr = counter2liststr(
                theplatinumresults - goldcounter)
            goldminusplatinumstr = counter2liststr(
                goldcounter - theplatinumresults)
            (gprecall, gpprecision, gpf1score) = getscores(
                goldcounter, theplatinumresults)
        else:
            sortedplatinumliststr, liststarplatinumliststr, platinumminusliststr, \
                listminusplatinumliststr = '', '', '', ''
            (platinumrecall, platinumprecision, platinumf1score) = (na, na, na)

            goldstarplatinumstr, platinumminusgoldstr, goldminusplatinumstr = '', '', ''
            (gprecall, gpprecision, gpf1score) = (na, na, na)

    else:
        goldcounter = Counter()
        (recall, precision, f1score) = (na, na, na)
        liststargoldstr, goldminusliststr, listminusgoldstr = '', '', ''
        sortedplatinumliststr, liststarplatinumliststr, platinumminusliststr, listminusplatinumliststr = '', '', '', ''
        (platinumrecall, platinumprecision, platinumf1score) = (na, na, na)
        theresultsminusgold = {}
        goldminustheresults = {}
        goldstarplatinumstr, platinumminusgoldstr, goldminusplatinumstr = '', '', ''
        (gprecall, gpprecision, gpf1score) = (na, na, na)

    platinumoutresults = theresults | goldcounter
    platinumoutresultsstring = counter2liststr(platinumoutresults)
    reskeystr = showreskey(reskey)

    queryinforow = [reskeystr, themethod.queries[queryid].cat, themethod.queries[queryid].subcat,
                    themethod.queries[queryid].item]
    queryresultsrow = [str(sumfreq(theresults)), resultstr,
                       str(goldcount), sortedgolduttstr, qex]
    queryRGscorerow = [sf(recall), sf(precision), sf(
        f1score), liststargoldstr, goldminusliststr, listminusgoldstr]
    queryRPscorerow = [sortedplatinumliststr, sf(platinumrecall), sf(platinumprecision), sf(platinumf1score),
                       platinumminusliststr, listminusplatinumliststr]
    queryGPscorerow = [sf(gprecall), sf(gpprecision), sf(gpf1score), goldstarplatinumstr, platinumminusgoldstr,
                       goldminusplatinumstr]

    fullresultrow = queryinforow + queryresultsrow + \
        queryRGscorerow + queryRPscorerow + queryGPscorerow

    platinumrow = [reskeystr, themethod.queries[queryid].cat, themethod.queries[queryid].subcat,
                   themethod.queries[queryid].item, platinumoutresultsstring, listminusgoldstr, '', '']

    return fullresultrow, platinumrow


def get_qid_reskeys(allresults: AllResults, themethod: Method) -> List[Tuple[QId, ResultsKey]]:
    """
    We gather tuples (QId, reskeys) where reskeys is the list of result keys that belong to QId.
    Examples of reskeys: ('T001', [('T001', 'T001')]); ('A051', [('A051', 'boek'), ('A051', 'lezen')])
    """
    results = []
    reskeyindex = defaultdict(list)
    for reskey in allresults.exactresults:      ## this is especially needed for ASTA lemma
        reskeyindex[reskey[0]].append(reskey)

    for queryid in themethod.queries:
        if queryid not in reskeyindex:
            reskeys = [mkresultskey(queryid)]
        else:
            reskeys = reskeyindex[queryid]
        results.append((queryid, reskeys))
    return results

# statement to fill the atp object:
# atp = AnalysisTableParameters(allresults=allresults, exactgoldscores=exactgoldscores,
#                               exactsilverscores=exactsilverscores, themethod=themethod, invalidqueries=invalidqueries,
#                               platinuminfilefound=platinuminfilefound, infilename=infilename, allannutts=allannutts,
#                               reffilename=reffilename, sas=sas)

def mk_analysis_table(atp: AnalysisTableParameters) -> Table:

    goldscores = exact2results(atp.exactgoldscores)
    silverscores = exact2results(atp.exactsilverscores)

    (inbase, inext) = os.path.splitext(atp.infilename)
    basepath, basefilename = os.path.split(atp.infilename)
    corepath, lastfolder = os.path.split(basepath)
    resultspath = os.path.join(corepath, resultsfolder)

    analysis_table = []

    # add the results
    qcount = 0
    invalidqcount = 0
    undefinedqcount = 0
    results: Dict[ResultsKey, ResultsCounter] = atp.allresults.coreresults
    exact = True

    allrows = []

    analysedtreesdict = {uttid: stree for uttid, stree in atp.allresults.analysedtrees}

    for queryid, reskeys in atp.qid_reskeys:
        for reskey in reskeys:
            theresults = results[reskey] if reskey in results else Counter()
            resultstr = counter2liststr(theresults)

            sortedgolduttstr = getsortedgolduttscore(reskey, goldscores)

            qex, invalidqcount, undefinedqcount = updatequerycounts(queryid, atp.themethod, invalidqcount,
                                                                    undefinedqcount, atp.invalidqueries)

            fullresultrow, platinumrow = getfullscoreandplatinumstr(reskey, atp.themethod, theresults, resultstr,
                                                                    goldscores, atp.platinuminfilefound,
                                                                    silverscores, sortedgolduttstr, qex,
                                                                    atp.invalidqueries)

            analysis_table.append(fullresultrow)

    # compute the gold postresults
    goldpostresults: Dict[UttId, int] = {}
    goldcounters: Dict[QId, ResultsCounter] = {}
    allgoldmatches: MatchesDict = {}
    for reskey in goldscores:
        goldcounters[reskey] = goldscores[reskey]
    allgoldresults = AllResults(atp.allresults.uttcount, goldcounters, atp.exactgoldscores, goldpostresults,
                                allgoldmatches, atp.reffilename, [],
                                atp.allannutts, atp.allresults.annotationinput)
    postquerylist: List[QId] = [
        q for q in atp.themethod.postquerylist if atp.themethod.queries[q].process == post_process]
    dopostqueries(allgoldresults, postquerylist, atp.themethod.queries)

    # compute the platinum postresults

    platinumpostresults: Dict[ResultsKey, Any] = {}

    # print the postresults
    thepostresults = atp.allresults.postresults
    for queryid in postquerylist:
        resultposval = str(getpostval(queryid, thepostresults))
        goldpostval = str(getpostval(queryid, goldpostresults))
        platinumpostval = str(getpostval(queryid, platinumpostresults))
        if atp.themethod.queries[queryid].query != '':
            qex = 'yes'
        else:
            qex = 'no'

        queryreskey = mkresultskey(queryid)
        queryreskeystr = showreskey(queryreskey)
        queryinforow = [queryreskeystr, atp.themethod.queries[queryid].cat, atp.themethod.queries[queryid].subcat,
                        atp.themethod.queries[queryid].item]
        queryresultsrow = ['', resultposval, '', goldpostval,
                           qex] + erow(6) + [platinumpostval] + erow(11)

        postrow = queryinforow + queryresultsrow
        analysis_table.append(postrow)

    # gather overall results, 2 cases: (1)for defined original measure queries only; (2) for all original measure queries

    overallmethods = [(1, 'Overall (defined pre and core queries in the profile)',
                       lambda x: is_preorcore(x) and query_exists(x) and query_inform(x)),
                      (2, 'Overall (all pre and core queries in the profile)',
                       lambda x: is_preorcore(x) and query_inform(x)),
                      (3, 'Overall (original pre and core measures with defined queries only)',
                       lambda x: is_preorcore(x) and query_exists(x)),
                      (4, 'Overall (all original pre and core measures)', lambda x: is_preorcore(x))]



    for (ctr, message, queryfunction) in overallmethods:
        # gather resultscount
        resultscount = 0
        for reskey in results:
            queryid = reskey[0]
            thequery = atp.themethod.queries[queryid]
            if thequery.original and queryfunction(thequery):
                resultscount += sum(results[reskey].values())

        # gather goldcount
        goldcount = 0
        for reskey in goldscores:
            queryid = reskey[0]
            thequery = atp.themethod.queries[queryid]
            goldcounter = goldscores[reskey]
            if thequery.original and queryfunction(thequery):
                goldcount += sum(goldcounter.values())

        # gather platinumcount
        platinumcount = 0
        for reskey in silverscores:
            queryid = reskey[0]
            if queryid in atp.themethod.queries:
                thequery = atp.themethod.queries[queryid]
                if thequery.original and queryfunction(thequery):
                    platinumcount += sum(silverscores[reskey].values())
            else:
                settings.LOGGER.warning(
                    f'Query {reskey} found in silver scores but {queryid} not in queries')

        # resultsgoldintersectiocount
        resultsgoldintersectioncount = 0
        for reskey in results:
            queryid = reskey[0]
            thequery = atp.themethod.queries[queryid]
            if thequery.original and queryfunction(thequery):
                if reskey in goldscores:
                    goldcounter = goldscores[reskey]
                    intersection = results[reskey] & goldcounter
                    resultsgoldintersectioncount += sum(intersection.values())
                else:
                    pass
                    # settings.LOGGER.warning(f'Query {reskey} found in results but not in goldscores')

        # resultsplatinumintersectioncount
        resultsplatinumintersectioncount = 0
        for reskey in results:
            queryid = reskey[0]
            thequery = atp.themethod.queries[queryid]
            if thequery.original and queryfunction(thequery):
                if reskey in silverscores:
                    intersection = results[reskey] & silverscores[reskey]
                    resultsplatinumintersectioncount += sum(
                        intersection.values())
                else:
                    pass
                    # settings.LOGGER.warning('queryid {} not in silverscores'.format(queryid))

        # goldplatinumintersectioncount
        goldplatinumintersectioncount = 0
        for reskey in silverscores:
            queryid = reskey[0]
            if queryid in atp.themethod.queries:
                thequery = atp.themethod.queries[queryid]
                if thequery.original and queryfunction(thequery):
                    if reskey in goldscores:
                        goldcounter = goldscores[reskey]
                        intersection = goldcounter & silverscores[reskey]
                        goldplatinumintersectioncount += sum(
                            intersection.values())
                    else:
                        pass
                        # settings.LOGGER.warning('Query {} in silverscores but not in goldscores'.format(queryid))
            else:
                settings.LOGGER.warning(
                    f'Query {reskey} in silverscores but {queryid} not in queries')

        (recall, precision, f1score) = getevalscores(
            resultscount, goldcount, resultsgoldintersectioncount)
        (platinumrecall, platinumprecision, platinumf1score) = getevalscores(resultscount, platinumcount,
                                                                             resultsplatinumintersectioncount)
        (gprecall, gpprecision, gpf1score) = getevalscores(
            goldcount, platinumcount, goldplatinumintersectioncount)

        overallrow = ['', '', '', message, '', '', '', '', '', sf(recall), sf(precision), sf(f1score),
                      '', '', '', '', sf(platinumrecall), sf(
                platinumprecision), sf(platinumf1score), '', '',
                      sf(gprecall), sf(gpprecision), sf(gpf1score), '', '', '']

        analysis_table.append(overallrow)

    return analysis_table






