from collections import defaultdict
from dataclasses import dataclass
import os
from sastadev.conf import settings
from sastadev.methods import MethodName, stap, asta, tarsp
from sastadev.sastatypes import Table
from sastadev.xlsx import getxlsxdata
from typing import Callable, List, Tuple

mn2col_mapping = {tarsp: [1,2],  asta:[3,4], stap:[5,6]}

bymethodsheetname = 'ByMethod'

@dataclass
class SortOrderDictParameters:
    sentlengths: dict
    realwordscountdict: dict
    codecountdict: dict
    utt_criterion_scores: dict
    cause_count_dict: dict
    sortorderfunction: Callable

@dataclass
class SortOrderParameters:
    sentlength: int
    realwordscount: int
    codecount: int
    utt_criterion_score: Tuple[float, float]
    cause_count: int



def get_causes_by_utt(sentences: dict) -> dict:
    """
    give a list of criteria for each sentence that led to its selection
    """
    newdict = defaultdict(list)
    for dsname in sentences:
        for row in sentences[dsname]:
            criterion = row[0]
            sample = row[1]
            xsid = row[2]
            newkey = (dsname, sample, xsid)
            newdict[newkey].append(criterion)
    return newdict

def get_criterion_scores(method_name:MethodName) -> dict:
    """
    function to collect the scores for criteria based on the training data
    """
    result_dict = {}
    infilename = 'sas_criterion_scores.xlsx'
    inpath = os.path.join(settings.SD_DIR, 'data', 'sas_criterion_scores')
    infullname = os.path.join(inpath, infilename)
    header, data = getxlsxdata(infullname, sheetname=bymethodsheetname)
    cols = mn2col_mapping[method_name]
    for row in data:
        criterion = row[0]
        scores = [row[i] for i in cols]
        if scores != ['','']:
            result_dict[criterion] = tuple(scores)
    return result_dict

criterion_scores = {}
for m in [tarsp, stap, asta]:
    criterion_scores[m] = get_criterion_scores(m)

def get_cause_count_dict(causes_dict) -> dict:
    result_dict = defaultdict(lambda: defaultdict(int))
    for key in causes_dict:
        count = len(causes_dict[key])
        ds_name, sample, xsid = key
        result_dict[sample].update({xsid: count})
    return result_dict



def get_utt_criterion_scores(sentences: Table, method_name: MethodName) -> Tuple[dict,dict]:
    """
    assigns a score to each sentence based on the scores for the criteria that led to its selection
    """
    result_dict = defaultdict(lambda: defaultdict(tuple))
    causes_dict = get_causes_by_utt(sentences)
    scores_dict = criterion_scores[method_name]
    for key in causes_dict:
        ds_name, sample, uttid = key
        causes_list = causes_dict[key]
        causes_scores = [scores_dict[cause] if cause in scores_dict else (100.0, 1.0) for cause in causes_list ]
        # if (100.0, 1.0) in causes_scores:
        #     settings.LOGGER.warning(f'criterion not in scores_dict for {ds_name}/{sample}/{uttid}')
        #     settings.LOGGER.warning(str(causes_list))
        #     settings.LOGGER.warning(str(causes_scores))
        the_score = get_the_score(causes_scores)
        result_dict[sample].update({uttid:the_score})

    cause_count_dict = get_cause_count_dict(causes_dict)
    return result_dict, cause_count_dict


def get_the_score(causes_scores:List[Tuple[float, float]]) -> Tuple[float, float]:
    if any([isinstance(x[0], str)  or isinstance(x[1], str) for x in causes_scores]):
        settings.LOGGER.error(f'string in {str(causes_scores)}')
    result = min(causes_scores)
    return result

def sortutterances(foundutts: dict, sod_pars: SortOrderDictParameters) -> dict:
    # @@ here we must see what the keys of the dictionaries is: sample, or (ds_name, sample): it is inconsistent now
    sortedfoundutts = defaultdict(list)
    for sample in foundutts:
        origlist = foundutts[sample]
        sl = sod_pars.sentlengths[sample]
        rwc = sod_pars.realwordscountdict[sample]
        cc = sod_pars.codecountdict[sample]
        ucs = sod_pars.utt_criterion_scores[sample]
        cause_counts = sod_pars.cause_count_dict[sample]
        sortedlist = sorted(origlist, key=lambda x:
                        sod_pars.sortorderfunction(rwc[x], sl[x], cc[x],
                                        ucs[x], cause_counts[x]), reverse=True)
        sortedfoundutts[sample] = sortedlist
    return sortedfoundutts

def sortorderfunction_rwc_cc_rwc_sl(realwordcount, sentlength, codecount, utt_criterion_score, cause_count):
    """
    The assumption is that the proportion between *codecount* and *realwordcount*, *realwordcount* and *sentlength* are
    relevant.
    This function sorts on (realwordcount / codecount, realwordcount, sentlength)

    :param realwordcount:
    :param sentlength:
    :param codecount:
    :return:
    """
    rwc_cc = realwordcount / codecount if codecount != 0 else realwordcount + 1
    resulttuple = (rwc_cc, realwordcount, sentlength)
    return resulttuple


def sortorderfunction_cc_rwc_rwc_sl(realwordcount, sentlength, codecount, utt_criterion_score, cause_count):
    """
    The assumption is that the proportion between *codecount* and *realwordcount*, *realwordcount* and *sentlength* are
    relevant.
    This function sorts on (codecount / realwordcount, realwordcount, sentlength)

    :param realwordcount:
    :param sentlength:
    :param codecount:
    :return:
    """
    cc_rwc = codecount / realwordcount if realwordcount != 0 else 0
    resulttuple = (cc_rwc, realwordcount, sentlength)
    return resulttuple

def sortorderfunction_neg_cc_rwc_rwc_sl(realwordcount, sentlength, codecount, utt_criterion_score, cause_count):
    """
    The assumption is that the proportion between *codecount* and *realwordcount*, *realwordcount* and *sentlength* are
    relevant.
    This function sorts on (-codecount / realwordcount, realwordcount, sentlength)

    :param realwordcount:
    :param sentlength:
    :param codecount:
    :return:
    """
    cc_rwc = codecount / realwordcount if realwordcount != 0 else 0
    resulttuple = (-cc_rwc, realwordcount, sentlength)
    return resulttuple

def sortorderfunction_causec_neg_cc_rwc_rwc_sl(realwordcount, sentlength, codecount, utt_criterion_score, cause_count):
    """
    We first select by the number of criteria (causecount) , then:
    The assumption is that the proportion between *codecount* and *realwordcount*, *realwordcount* and *sentlength* are
    relevant.
    This function sorts on (-codecount / realwordcount, realwordcount, sentlength)

    :param realwordcount:
    :param sentlength:
    :param codecount:
    :return:
    """
    cc_rwc = codecount / realwordcount if realwordcount != 0 else 0
    resulttuple = (-cause_count, -cc_rwc, realwordcount, sentlength)
    return resulttuple

def sortorderfunction_utt_nothc_neg_cc_rwc_rwc_sl(realwordcount, sentlength, codecount, utt_criterion_score, cause_count):
    """
    We first select by the number of criteria (causecount) , then:
    The assumption is that the proportion between *codecount* and *realwordcount*, *realwordcount* and *sentlength* are
    relevant.
    This function sorts on (-codecount / realwordcount, realwordcount, sentlength)

    :param realwordcount:
    :param sentlength:
    :param codecount:
    :return:
    """
    utt_conf, utt_nothc = utt_criterion_score
    cc_rwc = codecount / realwordcount if realwordcount != 0 else 0
    resulttuple = (utt_nothc, -cc_rwc, realwordcount, sentlength)
    return resulttuple


sortorderfunctions_dict = {
    'sortorderfunction_rwc_cc_rwc_sl': sortorderfunction_rwc_cc_rwc_sl,
    'sortorderfunction_cc_rwc_rwc_sl': sortorderfunction_cc_rwc_rwc_sl,
    'sortorderfunction_neg_cc_rwc_rwc_sl': sortorderfunction_neg_cc_rwc_rwc_sl,
    'sortorderfunction_causec_neg_cc_rwc_rwc_sl': sortorderfunction_causec_neg_cc_rwc_rwc_sl,
    'sortorderfunction_utt_nothc_neg_cc_rwc_rwc_sl': sortorderfunction_utt_nothc_neg_cc_rwc_rwc_sl
                           }






