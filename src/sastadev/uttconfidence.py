from collections import Counter
import os
from sastadev.conf import settings
from sastadev.constants import resultsfolder, byuttscoressuffix, analysissuffix
from sastadev.methods import asta, stap, tarsp, tarspauris, Method, MethodName, supported_methods, validmethods
from sastadev.datasets import alldatasets, trainingdatasets, DataSet
from sastadev.query import is_preorcore, query_inform
from sastadev.readmethod import read_method
from sastadev.rpf1 import getscores, sumfreq
from sastadev.sastatypes import ExactResults, FileName, QId, SampleName, Table, UttId
from sastadev.stringfunctions import remove_spaces
from sastadev.xlsx import getxlsxdata, mkworkbook
from statistics import mean
from typing import Dict, List, Optional,Tuple

comma = ','
slash = '/'

reskeycol = 0 # col A
resultscol = 5 # col F
silvercol = 15 # col P

uttidcol = 0
exactresultscol = 1
silverf1col = 21
uttcol = 22

QId_F1_Dict = Dict[QId, float]
UttId_ExactResults_Dict = Dict[UttId, ExactResults]

precision_threshold = 70.0

confbyuttfolder = '_conf_by_utt'

class ResultsAndSilver:
    results : List[UttId]
    silver: List[UttId]
    def __init__(self, results, silver):
        self.results = results
        self.silver = silver


def getmethod(methodname: MethodName, variant) -> Method:
    methodfullname = supported_methods[methodname]
    method = read_method(methodname, methodfullname, variant=variant)
    return method


def getlist(x) -> list:
    xstr = str(x)
    cleanxstr = remove_spaces(xstr)
    if cleanxstr == '':
        return []
    result = cleanxstr.split(comma)
    return  result

def get_results(dataset: DataSet, method: Method) ->  Dict[QId, ResultsAndSilver]:
    resultsandsilverdict = {}
    resultspath = os.path.join(settings.DATAROOT, dataset.name, resultsfolder)
    resultsfilenames = os.listdir(resultspath)
    analysisfilenames = [fn for fn in resultsfilenames if fn.endswith(f'{analysissuffix}.xlsx')]
    for analysisfilename in analysisfilenames:
        samplename = analysisfilename[:-len(f'{analysissuffix}.xlsx')]
        analysisfullname = os.path.join(resultspath, analysisfilename)
        analysisheader, analysisdata = getxlsxdata(analysisfullname)
        for row in analysisdata:
            reskey = row[reskeycol]
            if reskey == '':
                continue
            qid, qval = tuple(reskey.split(slash))
            if qid == qval:
                qval =''
            if qid in method.queries and is_preorcore(method.queries[qid]) and query_inform(method.queries[qid]):
                baseresults = getlist(row[resultscol])
                results = [(dataset.name, samplename, uttid, qval) for uttid in baseresults]
                basesilver = getlist(row[silvercol])
                silver = [(dataset.name, samplename, uttid, qval) for uttid in basesilver]
                if qid not in resultsandsilverdict:
                    resultsandsilverdict[qid] = ResultsAndSilver(results, silver)
                else:
                    resultsandsilverdict[qid].results += results
                    resultsandsilverdict[qid].silver += silver
    return resultsandsilverdict






def get_score_by_query(rawdatasets: List[DataSet], methodname: str, variant: str) -> QId_F1_Dict :
    scoresdict = {}
    datasets = [ds for ds in rawdatasets if ds.method == methodname and ds.variant == variant]
    resultsandsilverdict : Dict[str,  Dict[QId, ResultsAndSilver]] = {}
    combinedresultsandsilver = {}
    if methodname in supported_methods:
        method = getmethod(methodname, variant=variant)
    else:
        settings.LOGGER.error(f'Method {methodname} not supported')
        return {}
    for dataset in datasets:
        resultsandsilverdict[dataset.name] = get_results(dataset, method)

    for dataset in datasets:
        for qid in resultsandsilverdict[dataset.name]:
            if qid not in combinedresultsandsilver:
                combinedresultsandsilver[qid] = ResultsAndSilver([], [])
            combinedresultsandsilver[qid].results += resultsandsilverdict[dataset.name][qid].results
            combinedresultsandsilver[qid].silver += resultsandsilverdict[dataset.name][qid].silver

    table = []
    for qid in combinedresultsandsilver:
        resultscounter = Counter(combinedresultsandsilver[qid].results)
        refcounter = Counter(combinedresultsandsilver[qid].silver)
        intersection = resultscounter & refcounter
        diff1 = resultscounter - intersection
        diff2 = refcounter - intersection
        lresultscounter = sumfreq(resultscounter)
        lrefcounter = sumfreq(refcounter)
        lintersection = sumfreq(intersection)

        scoretuple = getscores(resultscounter, refcounter)
        scoresdict[qid] = scoretuple

        newrow = [qid, str(resultscounter), lresultscounter,
                       str(refcounter), lrefcounter,
                       str(intersection), lintersection,
                       str(diff1), str(diff2), ] + list(scoretuple)
        table.append(newrow)

    scoreheader = ['qid', 'results', '#results',
                          'reference', '#ref',
                          'íntersection', '#int',
                          'res-int', 'ref-int',
                          'recall', 'precision', 'f1']
    scorefilename = 'scorefile.xlsx'
    path = os.path.join(settings.DATAROOT, confbyuttfolder)
    scorefullname = os.path.join(path, scorefilename)
    wb = mkworkbook(scorefullname, [scoreheader], table, freeze_panes=(1, 1))
    wb.close()
    return scoresdict


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
        precisionlist = []
        for qid in results:
            if (dataset.method, dataset.variant) in score_by_query:
                if qid in score_by_query[(dataset.method, dataset.variant)]:
                    if len(score_by_query[(dataset.method, dataset.variant)][qid]) > 1:
                        precision = score_by_query[(dataset.method, dataset.variant)][qid][1]
                    else:
                        settings.LOGGER.error(f'Wrong score for {dataset.method}/{qid}: {score_by_query[dataset.method][qid]} ')
                        precision = 0.0
                else:
                    settings.LOGGER.info(f'{qid} not found in score_by_query for {dataset.method}')
                    precision = 0.0
            else:
                settings.LOGGER.error(f'{dataset.method}/{dataset.variant} not found in score_by_query')
                precision = 0.0
            precisionlist.append(precision)
        key = (dataset.name, samplename, uttid)
        if key in f1dict:
            f1uttrow = f1dict[key]
        else:
            settings.LOGGER.warning(f'No entry in f1dict for {str(key)}')
            f1uttrow = []
        belowlist = [v for v in precisionlist if v < precision_threshold]
        countbelow = len(belowlist)
        if precisionlist == []:
            avg = 0
        else:
            avg = mean(precisionlist)
        outrow = [dataset.name, samplename, uttid, str(results), str(precisionlist), avg, countbelow] + f1uttrow
        outrows.append(outrow)
    return outrows


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

score_by_query = {}
for methodname, variant in [(stap, '')]:  # for testing, should be: validmethods:
    score_by_query[(methodname, variant)] = get_score_by_query(trainingdatasets, methodname, variant)


def mytry1(methidbane, variant):
    result = score_by_query[(methodname, variant)]
    resultlist = []
    for qid in result:
        newrow = [qid, result[qid][0], result[qid][1], result[qid][2]]
        resultlist.append(newrow)
    header = ['qid', 'recall', 'precision', 'f1']
    # sortedresultlist = sorted(resultlist, key=lambda row: (row[2], row[3]))  # sort by (precision, f1)
    #for row in sortedresultlist:
    #    print(f'{row}')
    outfilename = f'scores_by_qid_{methodname}.xlsx'
    outfolder = confbyuttfolder
    outpath = os.path.join(settings.DATAROOT, outfolder)
    outfullname = os.path.join(outpath, outfilename)
    wb = mkworkbook(outfullname, [header], resultlist, freeze_panes=(1,0))
    wb.close()

    junk = 0

if __name__ == '__main__':
    fulltable = []
    tarsp_trainingdatasets = [ds for ds in trainingdatasets if ds.method == stap ]  # for testing
    for dataset in tarsp_trainingdatasets:
        method = getmethod(dataset.method, variant=dataset.variant)
        mytry1(method.name, variant)
        rows = get_dataset_scoresbyutt(dataset)
        fulltable += rows
    header = ['dataset', 'sample', 'uttid', 'results', 'preclist', 'avg', '#below', 'f1', 'utt']
    outfilename = 'confidence_by_utt.xlsx'
    outfolder = '_conf_by_utt'
    outpath = os.path.join(settings.DATAROOT, outfolder)
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    outfullname = os.path.join(outpath, outfilename)
    wb = mkworkbook(outfullname, [header], fulltable, freeze_panes=(1,1))
    wb.close()
