from collections import Counter
import os
from datetime import datetime

from sastadev.computeqidscores import computeqidscores
from sastadev.conf import settings
from sastadev.constants import (analysissuffix, byuttscoressuffix, confbyuttfolder, datafolder,
                                resultsfolder, scores_by_qid_folder)
from sastadev.methods import (asta, stap, tarsp, tarspauris, Method, MethodName, supported_methods, validmethods,
                              validmethodvariantpairs)
from sastadev.datasets import alldatasets, trainingdatasets, DataSet
from sastadev.query import is_preorcore, query_inform
from sastadev.readmethod import read_method, getmethod
from sastadev.rpf1 import getscores, sumfreq
from sastadev.sastatypes import ExactResults, FileName, QId, SampleName, Table, UttId
from sastadev.stringfunctions import remove_spaces
from sastadev.xlsx import getxlsxdata, mkworkbook
from statistics import mean
from typing import Dict, List, Optional,Tuple

header = ['dataset', 'sample', 'uttid', 'results', 'preclist', 'avg', '#below', 'f1', 'utt']

precision_threshold = {asta: 80.0, stap: 80.0, tarsp: 80.0}

uttidcol = 0
exactresultscol = 1
silverf1col = 21
uttcol = 22


def get_scoresbyutt_per_method(methodname: MethodName) -> Table:
    allscores = []
    thedatasets = [ds for ds in trainingdatasets if ds.method == methodname]
    for dataset in thedatasets:
        scores = get_dataset_scoresbyutt(dataset)
        allscores += scores
    return allscores



def get_dataset_scoresbyutt(dataset: DataSet) -> Table:
    scores = []
    resultspath = os.path.join(settings.DATAROOT, dataset.name, resultsfolder)
    resultsfilenames = os.listdir(resultspath)
    byuttscorefilenames = [fn for fn in resultsfilenames if fn.endswith(f'{byuttscoressuffix}.xlsx')]
    samplenames = [fn[:-len(f'{byuttscoressuffix}.xlsx')] for fn in byuttscorefilenames]
    for samplename in samplenames:
        filescores = get_sample_scoresbyutt(dataset, samplename)
        scores += filescores
    return scores

def get_utt_with_f1_dict(dataset: DataSet, samplename: str) -> dict:
    resultdict = {}
    resultspath = os.path.join(settings.DATAROOT, dataset.name, resultsfolder)
    byuttscorefilename = f'{samplename}{byuttscoressuffix}.xlsx'
    byuttscorefullname = os.path.join(resultspath, byuttscorefilename)
    header, data = getxlsxdata(byuttscorefullname, sheetname='Sheet1')
    for row in data:
        uttid = str(row[uttidcol])
        utt = row[uttcol]
        f1 = row[silverf1col]
        resultdict[dataset.name, samplename, uttid] = [f1, utt]
    return resultdict

def get_precision_list(results, methodname: MethodName, score_by_query:dict) -> List[float]:
    precisionlist = []
    for qid in results:
        if methodname in score_by_query:
            if qid in score_by_query[methodname]:
                if len(score_by_query[methodname][qid]) > 1:
                    precision = score_by_query[methodname][qid][1]
                else:
                    settings.LOGGER.error(
                        f'Wrong score for {methodname}/{qid}: {score_by_query[methodname][qid]} ')
                    precision = 0.0
            else:
                settings.LOGGER.info(f'{qid} not found in score_by_query for {methodname}')
                precision = 0.0
        else:
            settings.LOGGER.error(f'{methodname} not found in score_by_query')
            precision = 0.0
        precisionlist.append(precision)
    return precisionlist


def get_sample_scoresbyutt(dataset: DataSet, samplename: SampleName) -> Table:
    outrows = []
    f1dict = get_utt_with_f1_dict(dataset, samplename)
    resultspath = os.path.join(settings.DATAROOT, dataset.name, resultsfolder)
    byuttscorefilename = f'{samplename}{byuttscoressuffix}.xlsx'
    byuttscorefullname = os.path.join(resultspath, byuttscorefilename)
    exactresultsheader, exactresultsdata = getxlsxdata(byuttscorefullname, sheetname='ExactResults')
    if dataset.method in supported_methods:
        method = getmethod(dataset.method, variant=dataset.variant)
    else:
        settings.LOGGER.error(f'Method {dataset.method} not supported. Aborting')
        exit(-1)
    for row in exactresultsdata:
        uttid = str(row[uttidcol])
        rawexactresults = eval(row[exactresultscol])
        results = [qid for ((qid, _), pos) in rawexactresults if query_inform(method.queries[qid])]
        precisionlist = get_precision_list(results, dataset.method, score_by_query)
        key = (dataset.name, samplename, uttid)
        if key in f1dict:
            f1uttrow = f1dict[key]
        else:
            settings.LOGGER.warning(f'No entry in f1dict for {str(key)}')
            f1uttrow = []
        belowlist = [v for v in precisionlist if v < precision_threshold[method.name]]
        countbelow = len(belowlist)
        if precisionlist == []:
            avg = 0
        else:
            avg = mean(precisionlist)
        outrow = [dataset.name, samplename, uttid, str(results), str(precisionlist), avg, countbelow] + f1uttrow
        outrows.append(outrow)
    return outrows

def fetch_scores_by_query(methodname: MethodName) -> dict:
    resultsdatetime = getresultsdatetime(methodname)
    inpath = os.path.join(settings.SD_DIR, datafolder, scores_by_qid_folder)
    infile = f'scores_by_qid_{methodname}.xlsx'
    infullname = os.path.join(inpath, infile)
    storedatetime = os.path.getmtime(infullname)
    if resultsdatetime > storedatetime:
        # use the stored results
        pass
        result = {}
    else:
        # recompute the resulst
        result = computeqidscores(methodname)
    return result

def getresultsdatetime(methodname: MethodName) -> datetime:
    mostrecentdatetime = 0
    datasets = [ds for ds in trainingdatasets if ds.method == methodname]
    for dataset in datasets:
        resultspath = os.path.join(settings.DATAROOT, dataset.name, resultsfolder)
        rawfilenames = os.listdir(resultspath)
        samplefilenames = [fn for fn in rawfilenames if fn.endswith(f'{analysissuffix}.xlsx')]
        for filename in samplefilenames:
            fullname = os.path.join(resultspath, filename)
            modtime = os.path.getmtime(fullname)
            if modtime > mostrecentdatetime:
                mostrecentdatetime = modtime
    return mostrecentdatetime



def main():
    for methodname in validmethods:
        fulltable = get_scoresbyutt_per_method(methodname)
        outfilename = f'confidence_by_utt_{methodname}.xlsx'
        outpath = os.path.join(settings.SD_DIR, datafolder, confbyuttfolder)
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        outfullname = os.path.join(outpath, outfilename)
        wb = mkworkbook(outfullname, [header], fulltable, freeze_panes=(1, 1))
        wb.close()


score_by_query = {}
for methodname in validmethods:
    score_by_query[methodname] = fetch_scores_by_query(methodname)

if __name__ == '__main__':
    main()