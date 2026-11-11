'''
defines functions for the STAP post part of the methods

'''
from collections import Counter

from sastadev.allresults import mkresultskey
from sastadev.rpf1 import sumfreq
from sastadev.sastatypes import QId
from typing import List

BB_ids = ['S010', 'S011', 'S012']
S013qid = 'S013'
S013reskey = mkresultskey(S013qid)


def BB_totaal(allresults, _):
    scores = []
    for qid in BB_ids:
        if qid in allresults.coreresults:
            scores.append(allresults.coreresults[qid])
        else:
            scores.append(Counter())
    counts = [len(s) for s in scores]
    result = sum(counts)
    return result


def GLVU(allresults, _):
    total_length_VU = 0
    if S013reskey in allresults.coreresults:
        for key in allresults.coreresults[S013reskey]:
            total_length_VU += allresults.coreresults[S013reskey][key]
    result = total_length_VU / allresults.uttcount
    return result


def GL5LVU(allresults, _):
    counts = []
    if S013reskey in allresults.coreresults:
        for key in allresults.coreresults[S013reskey]:
            counts.append(allresults.coreresults[S013reskey][key])
    sorted_counts = counts.sort()
    result = sum(counts[45:50]) / 5
    return result


# # the functions below are not used because Excel computes the results inside the form
overige_fouten_qids =['S026', 'S027', 'S028', 'S029', 'S030', 'S031', 'S032', 'S033', 'S038', 'S039']
def overige_fouten_count(allresults, _) -> int:    ## this one is NOT used for the form but provides additional interesting information
    result = fouten_count(overige_fouten_qids, allresults)
    return result

hoofdww_weg_qids = ['S050']
def hoofdww_weg_count(allresults, _):
    result = fouten_count(hoofdww_weg_qids, allresults)
    return result

def ov_uiting_count(allresults, _) -> int:
    result = uiting_met_fouten_count(overige_fouten_qids, allresults)
    return result


congruentie_fouten_qids = ['S022', 'S034', 'S035']
def congruentie_fouten_count(allresults, _) -> int:
    result = fouten_count(congruentie_fouten_qids, allresults)
    return result

bepaler_verkeerd_qids = ['S021', 'S037']
def bepaler_verkeerd_count(allresults, _) -> int:
    result = fouten_count(bepaler_verkeerd_qids, allresults)
    return result

bepaler_weg_qids = ['S020']
def bepaler_weg_count(allresults, _) -> int:
    result = fouten_count(bepaler_weg_qids, allresults)
    return result

def fouten_count(qids: List[QId], allresults) -> int:
    result = 0
    for qid in qids:
        reskey = mkresultskey(qid)
        if reskey in allresults.coreresults:
            result += sumfreq(allresults.coreresults[reskey])
    return result

def uiting_met_fouten_count(qids, allresults) -> int:
    uttid_list = []
    for qid in qids:
        reskey = mkresultskey(qid)
        if reskey in allresults.coreresults:
            for uttid, cnt in allresults.coreresults[reskey].items():
                uttid_list.append(uttid)
    # remove duplicates
    uttid_set = set(uttid_list)
    result = len(uttid_set)
    return result


vt_fout_qids = ['S024']
def vt_fout_count(allresults, _) -> int:
    result = fouten_count(vt_fout_qids, allresults)
    return result

vd_fout_qids = ['S025']
def vd_fout_count(allresults, _) -> int:
    result = fouten_count(vd_fout_qids, allresults)
    return result

del_nmwg_qids = ['S036']
def del_nmwg_count(allresults, _) -> int:
    result = fouten_count(del_nmwg_qids, allresults)
    return result


