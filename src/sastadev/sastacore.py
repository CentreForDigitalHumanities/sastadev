from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from lxml import etree

from sastadev.allresults import (AllResults, ExactResultsDict, MatchesDict,
                                 ResultsKey, mkresultskey)
from sastadev.ASTApostfunctions import getastamaxsamplesizeuttidsandcutoff
from sastadev.conf import settings
from sastadev.external_functions import str2functionmap
from sastadev.grammarerrors import find_grammar_errors_in_allresults
from sastadev.imply import removeimplies
from sastadev.macros import expandmacros
from sastadev.methods import Method, astamethods, stapmethods, tarspmethods
from sastadev.mismatches import getmarkposition
from sastadev.query import (Query, form_process, is_core, is_literal, is_pre,
                            post_process, query_exists)
from sastadev.reduceresults import exact2results, reduceallresults
from sastadev.sasta_explanation import finalexplanation_adapttreebank
from sastadev.sastatypes import (FileName, MethodName, Position, QId,
                                 QueryDict, SampleSizeTuple, SynTree, TreeBank,
                                 UttId)
from sastadev.stringfunctions import getallrealwords
from sastadev.targets import get_mustbedone
from sastadev.treebankfunctions import (getattval, getnodeendmap,
                                        getxmetatreepositions, getxsid,
                                        getyield, showtree, topcat)

singlewordWquery = """//node[@pt="ww"]/ancestor::node[@cat="top" and count(.//node[@pt!="let" and @pt!="tsw"]) = 1 ] """


@dataclass
class SastaCoreParameters:
    annotationinput: bool = False
    corr: str = 'corrn'
    themethod: Method = None
    includeimplies: bool = False
    infilename: FileName = None
    targets: int = None


def doauchann(intreebank: SynTree) -> SynTree:

    # deal with final explanations
    fexplanations = True
    if fexplanations:
        outtreebank = finalexplanation_adapttreebank(intreebank)
    else:
        outtreebank = intreebank

    # for tree in treebank1:
    #     showtree(tree, 'na fexplanations')

    # deal with %xlit, %xint
    # @@ to be implemented @@

    return outtreebank


def sastacore(origtreebank: Optional[TreeBank], correctedtreebank: TreeBank,
              annotatedfileresults: Optional[AllResults],
              scp: SastaCoreParameters) -> Tuple[AllResults, SampleSizeTuple]:
    invalidqueries = {}

    annotationinput = scp.annotationinput
    if annotationinput:
        if not (origtreebank is None and annotatedfileresults is not None):
            pass  # report an error and exit
    else:
        if not (origtreebank is not None and annotatedfileresults is None):
            pass  # report an error and exit

    corr = scp.corr
    themethod = scp.themethod
    methodname = themethod.name
    altcodes = themethod.altcodes
    includeimplies = False
    infilename = scp.infilename
    nodeendmap = {}
    targets = scp.targets

    rawexactresults: ExactResultsDict = {}
    allmatches: MatchesDict = {}

    # @vanaf nu gaat het om een treebank, dus hier een if statement toevoegen-done
    if annotationinput:
        allutts = annotatedfileresults.allutts
        uttcount = len(allutts)
        exactresults = annotatedfileresults.exactresults
        analysedtrees = annotatedfileresults.analysedtrees
        uttcount = annotatedfileresults.uttcount
        coreresults = annotatedfileresults.coreresults
        postresults = annotatedfileresults.postresults
        allmatches = annotatedfileresults.allmatches
        infilename = annotatedfileresults.filename
    else:
        if origtreebank.tag != 'treebank':
            settings.LOGGER.error(
                "Input treebank file does not contain a treebank element")
            exit(-1)
        allutts = {}
        uttcount = 0
        # if includeimplies:   # not needed anymore, now part of the Tarsp Index
        #    themethod.queries['T120'].query = singlewordWquery

        # analysedtrees consists of (uttid, syntree) pairs in the order in which they come in
        analysedtrees: List[(UttId, SynTree)] = []
        for syntree in correctedtreebank:
            uttcount += 1

            mustbedone = get_mustbedone(syntree, targets)
            if mustbedone:
                # uttid = getuttid(syntree)
                # analysedtrees consists of (uttid, syntree) pairs in order
                uttid = getxsid(syntree)
                analysedtrees.append((uttid, syntree))

                doprequeries(syntree, themethod.queries,
                             rawexactresults, allmatches, invalidqueries)
                docorequeries(syntree, themethod.queries,
                              rawexactresults, allmatches, invalidqueries)

                # showtree(syntree)
                if uttid in nodeendmap:
                    settings.LOGGER.error(
                        'Duplicate uttid in sample: {}'.format(uttid))
                nodeendmap[uttid] = getnodeendmap(syntree)

                # uttno = getuttno(syntree)
                # allutts[uttno] = getyield(syntree)
                allutts[uttid] = getyield(syntree)


        # determine exactresults and apply the filter to catch interdependencies between prequeries and corequeries
        # rawexactresults = getexactresults(allmatches)
        rawexactresults2 = passfilter(rawexactresults, themethod)
        exactresults = rawexactresults2

        # pas hier de allutts en de rawexactresults2 aan om expansies te ontdoen, gebseerd op de nodeendmap
        # @@to be implemented @@ of misschien in de loop hierboven al?

    # @ en vanaf hier kan het weer gemeenschappelijk worden; er met dus ook voor de annotatiefile een exactresults opgeleverd worden
    # @d epostfunctions for lemma's etc. moeten mogelijk wel aangepast worden

    if includeimplies:
        pass
        # allmatches, rawexactresults = removeimplies(allmatches, exactresults, themethod)
    else:
        rawexactresults = exactresults

    # adapt the exactresults  positions to the reference
    if annotationinput:
        exactresults = rawexactresults
    else:
        exactresults = adaptpositions(rawexactresults, nodeendmap)

    coreresults = exact2results(exactresults)

    postresults: Dict[ResultsKey, Any] = {}
    allresults = AllResults(uttcount, coreresults, exactresults, postresults, allmatches, infilename,
                            analysedtrees,
                            allutts, annotationinput)

    samplesizefunction = getsamplesizefunction(methodname)
    samplesizetuple: SampleSizeTuple = samplesizefunction(allresults)

    postquerylist: List[QId] = [
        q for q in themethod.postquerylist if themethod.queries[q].process == post_process]
    formquerylist: List[QId] = [
        q for q in themethod.postquerylist if themethod.queries[q].process == form_process]

    # we assume the reduction must be done before the postqueries
    allresults = reduceallresults(allresults, samplesizetuple, methodname)

    dopostqueries(allresults, postquerylist, themethod.queries)

    dopostqueries(allresults, formquerylist, themethod.queries)

    allresults = find_grammar_errors_in_allresults(allresults)

    return allresults, samplesizetuple


def getexactposition(m: SynTree) -> int:
    mcat = getattval(m, 'cat')
    if mcat == topcat:
        result = 0
    else:
        result = int(getattval(m, 'begin')) + 1
    return result


def doqueries(syntree: SynTree, queries: QueryDict, exactresults: ExactResultsDict, allmatches: MatchesDict,
              criterion: Callable[[Query], bool], invalidqueries):
    # global invalidqueries
    uttid = getxsid(syntree)
    # uttid = getuttidorno(syntree)
    omittedwordpositions = getxmetatreepositions(
        syntree, 'Omitted Word', poslistname='annotatedposlist')
    # print(uttid)
    # core queries
    for queryid in queries:  # @@ dit aanpassen voor literals en voor Resultskey; check read_referencefile
        # if queryid not in exactresults: # not needed becaysetaken care of below
        #     exactresults[queryid] = []
        thequeryobj = queries[queryid]
        if criterion(thequeryobj):
            if query_exists(thequeryobj):
                thelistedquery = thequeryobj.query
                if isxpathquery(thelistedquery):
                    expandedquery = expandmacros(thelistedquery)
                    thequery = "." + expandedquery
                    try:
                        matches = syntree.xpath(thequery)
                    except etree.XPathEvalError as e:
                        invalidqueries[queryid] = e
                        matches = []
                else:
                    thef = str2functionmap[thelistedquery]
                    matches = thef(syntree)
            else:
                matches = []
                exactresults[mkresultskey(queryid)] = []
            # matchingids = [uttid for x in matches]
            for m in matches:
                # showtree(m)
                reskey = getreskey(queryid, m, queries)
                if m is None:
                    showtree(syntree, text='in doqueries: Nonematch')
                if (reskey, uttid) in allmatches:
                    allmatches[(reskey, uttid)].append((m, syntree))
                else:
                    allmatches[(reskey, uttid)] = [(m, syntree)]
                exactresult = (uttid, getexactposition(m))
                if reskey in exactresults:
                    exactresults[reskey].append(exactresult)
                else:
                    exactresults[reskey] = [exactresult]
            # if queryid in results:
            #    results[queryid].update(matchingids)
            # else:
            #    results[queryid] = Counter(matchingids)


def docorequeries(syntree: SynTree, queries: QueryDict, results: ExactResultsDict, allmatches: MatchesDict, invalidqueries):
    doqueries(syntree, queries, results, allmatches, is_core, invalidqueries)


def doprequeries(syntree: SynTree, queries: QueryDict, results: ExactResultsDict, allmatches: MatchesDict, invalidqueries):
    doqueries(syntree, queries, results, allmatches, is_pre, invalidqueries)


def dopostqueries(allresults: AllResults, postquerylist: List[QId], queries: QueryDict):
    # post queries
    for queryid in postquerylist:
        thequeryobj = queries[queryid]
        if query_exists(thequeryobj):
            thelistedquery = thequeryobj.query

            # it is assumed that these are all python functions
            thef = str2functionmap[thelistedquery]
            result = thef(allresults, queries)
            allresults.postresults[queryid] = result


def passfilter(rawexactresults: ExactResultsDict, method: Method) -> ExactResultsDict:
    """
    let only those through that satisfy the filter
    :param rawexactresults: dictionary with ResultsKey as key and a Counter as value, exact results
    :param method: Method object
    :return: a filtered version of rawexactresults: results that pass the filter
    """
    #    exactresults: ExactResultsDict = defaultdict(list)  # hiermee ontstaat een probleem: dictionary size changed in iteration
    exactresults: ExactResultsDict = {}
    queries = method.queries
    for reskey in rawexactresults:
        queryid = reskey[0]
        query = queries[queryid]
        queryfilter = query.filter
        thefilter = method.defaultfilter if queryfilter is None or queryfilter == '' else str2functionmap[
            queryfilter]
        exactresults[reskey] = [r for r in rawexactresults[reskey]
                                if reskey in rawexactresults and thefilter(query, rawexactresults, r)]
    return exactresults


def adaptpositions(rawexactresults: ExactResultsDict, nodeendmap) -> ExactResultsDict:
    newexactresults: ExactResultsDict = {}
    for qid in rawexactresults:
        newlist = []
        for (uttid, position) in rawexactresults[qid]:
            newposition = getmarkposition(position, nodeendmap, uttid)
            newtuple = (uttid, newposition)
            newlist.append(newtuple)
        newexactresults[qid] = newlist
    return newexactresults


def isxpathquery(query: str) -> bool:
    cleanquery = query.lstrip()
    return cleanquery.startswith('//')


def getreskey(qid: QId, m: SynTree, queries: QueryDict) -> ResultsKey:
    if m is None:
        return mkresultskey(qid)
    thequery = queries[qid]
    if is_literal(thequery):
        litfunc = str2functionmap[thequery.literal]
        thevalue = litfunc(m)
        return mkresultskey(qid, thevalue)
    else:
        return mkresultskey(qid)


def getsamplesizefunction(methodname: MethodName) -> Callable:
    if methodname in astamethods:
        result = getastamaxsamplesizeuttidsandcutoff
    elif methodname in tarspmethods:
        # @@to be implemented
        result = getmaxsamplesizeuttidsandcutoff
    elif methodname in stapmethods:
        # @@to be implemented
        result = getmaxsamplesizeuttidsandcutoff
    return result


def getmaxsamplesizeuttidsandcutoff(allresults: AllResults) -> Tuple[List[UttId], int, Position]:
    cutoffpoint = None
    words = getallrealwords(allresults)
    cumwordcount = 0
    wordcounts: Dict[UttId, Tuple[int, int, int]] = {}
    uttidlist = []
    for uttid in allresults.allutts:
        basewordcount = sum(words[uttid].values())
        ignorewordcount = 0  # getignorewordcount(allresults, uttid)
        wordcount = basewordcount - ignorewordcount
        wordcounts[uttid] = (basewordcount, ignorewordcount, wordcount)
        uttidlist.append(uttid)
        cumwordcount += wordcount
    result = (uttidlist, cumwordcount, cutoffpoint)
    return result
