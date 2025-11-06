from collections import Counter, defaultdict
import os
from sastadev.conf import settings
from sastadev.constants import resultsfolder, analysissuffix, datafolder, scores_by_qid_folder
from sastadev.datasets import DataSet, trainingdatasets
from sastadev.methods import Method, MethodName, supported_methods, validmethods
from sastadev.query import is_preorcore, query_inform
from sastadev.readmethod import read_method, getmethod
from sastadev.rpf1 import getscores, sumfreq
from sastadev.sastatypes import ExactResults, QId, Table, UttId
from sastadev.stringfunctions import remove_spaces
from sastadev.scorecount import ScoreCount, scorecount_avg
from sastadev.xlsx import getxlsxdata, mkworkbook
from typing import Dict, List, Tuple

ScoreTuple = Tuple[float, float, float]
QId_Scores_Dict = Dict[QId, ScoreTuple]
QId_ScoreCount_Dict = Dict[QId, ScoreCount]
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

outpath = os.path.join(settings.SD_DIR, datafolder, scores_by_qid_folder)
if not os.path.exists(outpath):
    os.makedirs(outpath)

qidheader = ['qid', 'recall', 'precision', 'f1']


class ResultsAndSilver:
    results : List[UttId]
    silver: List[UttId]
    def __init__(self, results, silver):
        self.results = results
        self.silver = silver


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




def get_score_by_query(dataset: DataSet, methodname: str, variant: str) -> QId_ScoreCount_Dict :
    scoresdict = {}
    resultsandsilverdict : Dict[str,  Dict[QId, ResultsAndSilver]] = {}
    combinedresultsandsilver = {}
    if methodname in supported_methods:
        method = getmethod(methodname, variant=variant)
    else:
        settings.LOGGER.error(f'Method {methodname} not supported')
        return {}
    resultsandsilverdict[dataset.name] = get_results(dataset, method)

    for qid in resultsandsilverdict[dataset.name]:
        if qid not in combinedresultsandsilver:
            combinedresultsandsilver[qid] = ResultsAndSilver([], [])
        combinedresultsandsilver[qid].results += resultsandsilverdict[dataset.name][qid].results
        combinedresultsandsilver[qid].silver += resultsandsilverdict[dataset.name][qid].silver


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
        recall, precision, f1_score = scoretuple
        scoresdict[qid] = ScoreCount(recall, precision, f1_score, lrefcounter)

    return scoresdict



def computeqidscores(methodname) -> QId_Scores_Dict:
    selected_trainingdatasets = [ds for ds in trainingdatasets if ds.method == methodname]
    allscores_by_qid = defaultdict(list)
    for dataset in selected_trainingdatasets:
        # method = getmethod(dataset.method, variant=dataset.variant)
        score_by_qid_dict = get_score_by_query(dataset, methodname, dataset.variant)
        for qid in score_by_qid_dict:
            allscores_by_qid[qid].append(score_by_qid_dict[qid])
    resultscores = {}
    for qid in allscores_by_qid:
        resultscores[qid] = scorecount_avg(allscores_by_qid[qid])
    return resultscores


def main():
    for methodname in validmethods:
        scoresdict = computeqidscores(methodname)
        table = []
        for qid in scoresdict:
            newrow = [qid]  + list(scoresdict[qid])
            table.append(newrow)
        filename = f'scores_by_qid_{methodname}.xlsx'
        fullname = os.path.join(outpath, filename)
        wb =mkworkbook(fullname, [qidheader], table, freeze_panes=(1,1))
        wb.close()

if __name__ == '__main__':
    main()



