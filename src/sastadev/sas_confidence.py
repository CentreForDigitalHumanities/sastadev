import os
from sastadev.conf import settings
from sastadev.constants import datafolder, confbyuttfolder
from sastadev.methods import Method, validmethods
from sastadev.query import query_inform
from sastadev.sastatypes import SynTree, TreeBank, ExactResultsDict, SAS_Result_List
from sastadev.treebankfunctions import getxsid, find1
from sastadev.xlsx import getxlsxdata
from sastadev.uttconfidence import fetch_scores_by_query, get_precision_list, precision_threshold
from statistics import mean

low_avg_conf_message = 'Low confidence for this utterance'
contains_low_conf_measures_message = 'This utterance contains multiple low confidence language measures'

def get_cutoff_dict() -> dict:
    cutoff_dict = {}
    cutoff_filename = 'cutoff_data.xlsx'
    path = os.path.join(settings.SD_DIR, datafolder, confbyuttfolder)
    cutoff_fullname = os.path.join(path, cutoff_filename)
    header, data = getxlsxdata(cutoff_fullname)
    for row in data:
        cutoff_dict[row[0]] = row[1]
    return cutoff_dict

cutoff_dict = get_cutoff_dict()
score_by_query = {}
for methodname in validmethods:
    score_by_query[methodname] = fetch_scores_by_query(methodname)

def low_avg_confidence(treebank: TreeBank, exact_resultsdict: ExactResultsDict, method: Method) -> SAS_Result_List:
    outlist = []
    for tree in treebank:
        uttid = getxsid(tree)
        if uttid in exact_resultsdict:
            results = [qid for ((qid, _), pos) in exact_resultsdict[uttid] if query_inform(method.queries[qid])]
            precisionlist = get_precision_list(results, method.name, score_by_query)
            qid_prec_list = zip(results, precisionlist)
            belowlist = [(qid, prec) for qid, prec in qid_prec_list if prec < precision_threshold[method.name]]
            countbelow = len(belowlist)
            if precisionlist == []:
                avg = 0
            else:
                avg = mean(precisionlist)

            if avg < cutoff_dict[method.name]:
                match = find1(tree, './/node[@cat="top"]')
                if match is not None:
                    newtriple = (match, low_avg_conf_message, [])
                    outlist.append(newtriple)
                else:
                    settings.LOGGER.error(f'sas_confidence/low_avg_confidence: not top node found in tree for utt {uttid}')

            if countbelow > 1:
                itemlist = [method.queries[qid].item for qid, _ in belowlist]
                itemstr = ', '.join(itemlist)
                message = f'{contains_low_conf_measures_message}: {itemstr} '
                match = find1(tree, './/node[@cat="top"]')
                if match is not None:
                    newtriple = (match, message, [])
                    outlist.append(newtriple)
                else:
                    settings.LOGGER.error(f'sas_confidence/low_avg_confidence: not top node found in tree for utt {uttid}')
        else:
            settings.LOGGER.warning(f'Utterance {uttid} not in the results')
    return outlist





