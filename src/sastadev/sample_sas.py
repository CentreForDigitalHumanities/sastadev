from methods import Method
from resultsbyutterance import getexactbyutt
from sas_meta import SAS_Meta
import sas_queries
from sastatypes import ExactResultsDict, TreeBank
from treebankfunctions import (find1, getcleanedutt, getnodeyield, getrealwordcount, origuttxpath,
                               parsedasquery, xsidxpath)
from typing import Callable, List

def sample_sas(treebank: TreeBank, exactresults: ExactResultsDict, select_criterion: Callable,
               datasetname: str, xmlfilename:str, method: Method) -> List[SAS_Meta]:
    results = []
    for named_criterion in sas_queries.criteria:
        criterion_name, criterion_function = named_criterion

        richmatches = criterion_function(treebank, exactresults, method)
        for match, message, suggestedcodes in richmatches:
            if select_criterion(match):
                # print(f'unknown word: {gav(match, "word")}')
                topnode = find1(match, 'ancestor::alpino_ds')

                origutts = match.xpath(origuttxpath)
                cleanedutt = getcleanedutt(match)
                xsids = match.xpath(xsidxpath)
                xsid = xsids[0] if xsids != [] else 0
                sentnodelist = getnodeyield(topnode)
                # sent = space.join([gav(n, 'word') for n in sentnodelist])
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
                results.append((match, meta))
    return results
