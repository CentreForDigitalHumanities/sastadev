from collections import defaultdict
from lxml import etree
from sastadev.methods import Method
from sastadev.resultsbyutterance import getexactbyutt
from sastadev.sas_meta import SAS_Meta, SAS_Result, SAS_Match_and_Meta, sas_matchmeta2result
from sastadev.sas_queries import criteria, sortorderfunction
from sastadev.sastatypes import ExactResultsDict, SynTree, TreeBank, UttId
from sastadev.treebankfunctions import (find1, getattval as gav, getcleanedutt, getnodeyield, getrealwordcount, origuttxpath,
                               parsedasquery, xsidxpath)
from typing import Callable, List, Tuple

space = ' '

def sample_sas(treebank: TreeBank, exactresults: ExactResultsDict, select_criterion: Callable,
               datasetname: str, xmlfilename:str, method: Method) -> List[SAS_Meta]:
    results = []
    metaresults = []
    for tree in treebank:
        if select_criterion(tree):
            singletree_treebank = etree.Element('treebank')
            singletree_treebank.append(tree)
            for criterion_name in criteria:
                criterion_function = criteria[criterion_name]

                richmatches = criterion_function(singletree_treebank, exactresults, method)
                for match, message, suggestedcodes in richmatches:
                    # print(f'unknown word: {gav(match, "word")}')
                    topnode = find1(match, 'ancestor::alpino_ds')

                    origutts = match.xpath(origuttxpath)
                    cleanedutt = getcleanedutt(match)
                    xsids = match.xpath(xsidxpath)
                    sentnodelist = getnodeyield(topnode)
                    sent = space.join([gav(n, 'word') for n in sentnodelist])
                    if xsids == []:
                        continue
                    else:
                        xsid = xsids[0]
                    # xsid = xsids[0] if xsids != [] else 'xx'
                    origutt = origutts[0] if origutts != [] else ''
                    parsedaslist = match.xpath(parsedasquery)
                    parsedas = parsedaslist[0] if parsedaslist != [] else cleanedutt
                    realwordcount = getrealwordcount(match)
                    sampleresults = getexactbyutt(exactresults)
                    codecount = len(sampleresults[xsid]) if xsid in sampleresults else 0
                    parsedasstr = f'parsed as <{parsedas}>' if parsedas != '' else ''
                    origuttstr = f'original utt <{origutt}>' if origutt != '' else ''
                    # print(f'found {datasetname}/{samplename}/{xsid}: <{sent}>; {origuttstr}; {parsedasstr}')
                    treebanksfolder = ''
                    meta = SAS_Meta(datasetname, treebanksfolder, xmlfilename, xsid, sentnodelist, origutt,
                                    parsedas, message, suggestedcodes, realwordcount, codecount)
                    metaresults.append((match, meta))

        # here compute the utt_crterion_score and the cause _count for each utterance / tree

    # sort the metaresults  # temporaririly put off
    sorted_metaresults = metaresults
    # sorted_metaresults = sort_sas_metalist(metaresults)

    # create a sorted list of uttids without duplicates
    uttidlist = getuniqueuttids(sorted_metaresults)

    # append entries for duplicates to the first one
    mergedmetaresults = mergemetaresults(sorted_metaresults)

    results = [(uttid,[sas_matchmeta2result((match, meta)) for match, meta in mergedmetaresults[uttid]])
               for uttid in uttidlist
                ]

    return results


def sort_sas_metalist(metaresults: List[SAS_Match_and_Meta]) -> List[SAS_Match_and_Meta]:
    sortedresults = sorted(metaresults,
                           key=lambda r: sortorderfunction(len(r[1].sentnodelist),
                                                               r[1].realwordcount,
                                                               r[1].codecount
                                                          ),
                           reverse=True
                          )
    return sortedresults

def getuniqueuttids(metaresults: List[SAS_Match_and_Meta]) -> List[UttId]:
    resultlist = []
    for match, metaresult in metaresults:
        if metaresult.xsid not in resultlist:
            resultlist.append(metaresult.xsid)
    return resultlist

def mergemetaresults(metaresults: List[SAS_Match_and_Meta]) -> dict:
    resultdict = defaultdict(list)
    for match, metaresult in metaresults:
        resultdict[metaresult.xsid].append((match, metaresult))
    return resultdict
