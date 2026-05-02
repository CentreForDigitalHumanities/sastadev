'''
The module TARSPpostfunctions defines functions for the TARSP post part of the methods

'''
from collections import Counter
import copy
from typing import Dict, List, Optional, Tuple

from sastadev.allresults import AllResults, mkresultskey, ResultsKey
from sastadev.CHILDES_age import childes_age_from_string, normalise_age, month_diff
from sastadev.conf import settings
from sastadev.filefunctions import getbasename
from sastadev.forms import get_toelichting_filename
from sastadev.query import core_process, query_inform
from sastadev.rpf1 import sumfreq
from sastadev.sastatypes import QId, QueryDict, Stage, SynTree
from sastadev.stringfunctions import show_roman, conj, disj
from sastadev.tarsp_tables import gzw_by_stage, gzw_by_age, norm_tabel_1_data, norm_tabel_2_data
from sastadev.toelichting import PFReportData, ReportData, StageReportData, FullStageReportData
from sastadev.treebankfunctions import getmeta
from typing import Callable, Tuple

RefinedStage = Tuple[int, bool]

commaspace = ', '

BWOndBB = mkresultskey('T029')
BX = mkresultskey('T030')
he = mkresultskey('T039')
Into = mkresultskey('T048')
OndB = mkresultskey('T064')
OndVC = mkresultskey('T071')
OndWB = mkresultskey('T073')
OndWBB = mkresultskey('T074')
OndWVC = mkresultskey('T076')
OndWBVC = mkresultskey('T075')
VCWOndBB = mkresultskey('T100')
OndWVCVCX = mkresultskey('T077')
VCW = mkresultskey('T099')
Xneg = mkresultskey('T140')
LongXneg = mkresultskey('T167')
WOndX = mkresultskey('T129')
VrXY = mkresultskey('T111')
WOnd4 = mkresultskey('T130')
WOnd5plus = mkresultskey('T131')
Vr5plus = mkresultskey('T113')

gtotaal_qid = 'T152'
pf_qid = 'T162'

long_B_measures = [BWOndBB, OndWB, OndWBB, OndWBVC, VCWOndBB]
long_VC_measures = [OndWVC, OndWBVC, VCWOndBB, OndWVCVCX]
vraagzin_measures = [he, WOndX, VrXY, WOnd4, WOnd5plus, Vr5plus]
addable_taalmaten = [OndB, OndVC, Into, Xneg ]

addable_dict = {OndB: long_B_measures, OndVC: long_VC_measures, Into: vraagzin_measures, Xneg: [LongXneg]}

#: The variable (constant) *vuqueryids* contains a list of Query identifiers for
#: queries for fixed expressions (V.U.).
vuqueryids = ['T094', 'T095', 'T096', 'T150']
#: The variable (constant) *tarsp_clausetypes* contains the (lower case) values for the
#: subcategory of a query that represent clause types.
tarsp_clausetypes = ['mededelende zin', 'vragen', 'gebiedende wijs']
#: The variable (constant) *excludedqids* contains a list of QIds for queries that
#: should be excluded in computing G.O. Fase.
excludedqids = ['T039', 'T048', 'T049', 'T052']   # TARSP p. 21: hè, Into, Inversie, Kop
#: The variable (constant) *gofase_minthreshold* contains the value of the minimum
#: percentage of analysis units that must have been scored to be included in G.O. Fase.
gofase_minthreshold = 0.05  # 5% p21 Tarsp 2005

girl = 'meisje'
boy = 'jongen'
child = 'kind'
snel = 'snel'
gemiddeld = 'gemiddeld'

snel_gemiddeld = {snel, gemiddeld}


def mk_measure_str(measure_list: List[ResultsKey], thequeries: QueryDict, coord=conj) -> str:
    qids = [meas[0] for meas in measure_list]
    items = [thequeries[qid].item for qid in qids if qid in thequeries]
    result = coord(items)
    return result


def getqueriesbystage(queries: QueryDict) -> Dict[Stage, List[QId]]:
    '''
    The function *getqueriesbystage* creates a dictionary with a stage as key and a
    list of QIds as value.

    It selects those QIds for which the query's (lower cased) subcategory is contained
    in the constant *tarsp_clausetypes*:

    .. autodata:: sastadev.TARSPpostfunctions::tarsp_clausetypes

    and which is not included in the list of *excludedqids*:

    .. autodata:: sastadev.TARSPpostfunctions::excludedqids

    if these conditions are met, the QId is appended to the dictionary item with key
    equal to the stage of the query associated with QId.
    '''
    results = {}
    for qid in queries:
        if queries[qid].subcat.lower() in tarsp_clausetypes and qid not in excludedqids:
            stage = queries[qid].fase
            if stage in results:
                results[stage].append(qid)
            else:
                results[stage] = [qid]
    return results


def vutotaal(allresults: AllResults, _: SynTree) -> int:
    '''
    The function *vutotaal* computes the total number of  "Vaste Uitdrukkingen" (VU) in
    the variable *allresults*. It uses the set *vuqueryids* to determine which
    queries to take into account and which not:

     .. autodata:: vuqueryids
    '''
    scores = []
    for qid in vuqueryids:
        if qid in allresults.coreresults:
            scores.append(allresults.coreresults[qid])
        else:
            scores.append(Counter())
#    scores = [allresults.coreresults[qid] for qid in vuqueryids]
    counts = [len(s) for s in scores]
    result = sum(counts)
    return result


def gtotaal(allresults: AllResults, _: SynTree) -> int:
    '''
    The function *gtotaal* computes the number of utterances to be analysed. It does
    so by subtracting the number of V.U. utterances and the results for *Atotaal* from
    the total number of utterances.
    '''
    Atotaal = 0
    vutotaal = allresults.postresults['T151']
    raw_gtotaal  =len(allresults.allutts)
    Gtotaal = raw_gtotaal - Atotaal - vutotaal
    return Gtotaal


def countutts(acounter: Counter):
    '''
    The function *countutts* returns the sum of the values for each key in
    *acounter*.
    '''
    result = 0
    for k in acounter:
        result += acounter[k]
    return result


def getuttcountsbystage(queriesbystage: Dict[Stage, List[QId]], allresults: AllResults)\
        -> Dict[Stage, int]:
    '''
    The function *getuttcountsbystage* computes a dictionary *uttcounts* of Stage,
    int items based on the input parameters *queriesbystage* and *allresults*.

    For each qid in *queriesbystage* that is a qid for a core query, it counts the
    number of utterances marked in  *allresults.coreresults*. For this it uses the
    function *countutts*:

    .. autofunction:: sastadev.TARSPpostfunctions::countutts

    '''
    uttcounts = {}
    for stage in queriesbystage:
        uttcounts[stage] = 0
        for qid in queriesbystage[stage]:
            reskey = mkresultskey(qid)
            if reskey in allresults.coreresults:
                uttcounts[stage] += countutts(allresults.coreresults[reskey])
    return uttcounts


def getstage(uttcounts: Dict[Stage, int], allresults: AllResults) -> Stage:
    '''
    The function *getstage* computes the stage on the basis of the *uttcounts*
    dictionary with Stage, int items and *allresults*

    The stage is taken into consideration if its number of scores divided by *gtotaal* is
    greater or equal to the value of *gofase_minthreshold*:

    .. autodata:: sastadev.TARSPpostfunctions::gofase_minthreshold

    Utterances from higher levels can be counted in.
    From the remaining candidates the highest stage value is selected.
    '''
    cands = []
    gtotaal = allresults.postresults[gtotaal_qid]
    for el in uttcounts:
        if gtotaal != 0:
            # include utterances from the higher stages
            higher_stages_uttcount = sum([uttcounts[stage] for stage in uttcounts if stage > el])
            all_utt_count = uttcounts[el] + higher_stages_uttcount
            if all_utt_count / gtotaal >= gofase_minthreshold:
                cands.append(el)
        else:
            settings.LOGGER.error('gtotaal has value 0')
    if cands == []:
        result = 1
    else:
        result = max(cands)
    return result


def gofase(allresults: AllResults, thequeries: QueryDict) -> str:
    '''
    The function *gofase* computes the stage given the results in the parameter
    *allresults* and the queries in the parameter *thequeries*.

    It first obtains *queriesbystage*, a dictionary of Stage, List[QId] items, via the
    function  *getqueriesbystage* applied to *thequeries*:

    .. autofunction:: sastadev.TARSPpostfunctions::getqueriesbystage

    Next, it obtains *uttcounts*,  a dictionary of Stage, int items by applying the
    function  *getuttcountsbystage* to *queriesbystage* and *allresults*:

    .. autofunction:: sastadev.TARSPpostfunctions::getuttcountsbystage

    Finally, it obtains the stage by applying the function *getstage* to *uttcounts*
    and *allresults*:

    .. autofunction:: sastadev.TARSPpostfunctions::getstage

    It then uses the obtained stage to obtain the refined_stage by means of the function *get-refined_stage*:

    .. autofunction:: sastadev.TARSPpostfunctions::get_refined_stage

    It turns the obtained value of type RefinedStage into a string using the function *show_refined_stage*:

    .. autofunction:: sastadev.TARSPpostfunctions::show_refined_stage

    and then it returns the obtained string.
    '''

    stage_report_data = gofaseplus(allresults, thequeries)
    refined_stage = stage_report_data.stage, stage_report_data.stage_refinement

    result = show_refined_stage(refined_stage)

    return result

def gofaseplus(allresults: AllResults, thequeries: QueryDict) -> StageReportData:
    '''
    The function *gofase* computes the stage given the results in the parameter
    *allresults* and the queries in the parameter *thequeries*.

    It first obtains *queriesbystage*, a dictionary of Stage, List[QId] items, via the
    function  *getqueriesbystage* applied to *thequeries*:

    .. autofunction:: sastadev.TARSPpostfunctions::getqueriesbystage

    Next, it obtains *uttcounts*,  a dictionary of Stage, int items by applying the
    function  *getuttcountsbystage* to *queriesbystage* and *allresults*:

    .. autofunction:: sastadev.TARSPpostfunctions::getuttcountsbystage

    Finally, it obtains the stage by applying the function *getstage* to *uttcounts*
    and *allresults*:

    .. autofunction:: sastadev.TARSPpostfunctions::getstage

    It then uses the obtained stage to obtain the refined_stage by means of the function *get-refined_stage*:

    .. autofunction:: sastadev.TARSPpostfunctions::get_refined_stage

    It turns the obtained value of type RefinedStage into a string using the function *show_refined_stage*:

    .. autofunction:: sastadev.TARSPpostfunctions::show_refined_stage

    and then it returns the obtained string.
    '''
    queriesbystage: Dict[Stage, List[QId]] = getqueriesbystage(thequeries)
    scored_utt_counts: Dict[Stage, int] = getuttcountsbystage(queriesbystage, allresults)
    utt_count = allresults.postresults[gtotaal_qid]
    stage: Stage = getstage(scored_utt_counts, allresults)
    non_clause_reskeys = get_non_clause_reskeys(stage, thequeries)
    scored_non_clause_reskeys = [reskey for reskey in non_clause_reskeys
                                 if reskey in allresults.coreresults and  len(allresults.coreresults[reskey]) > 0]

    refined_stage = get_refined_stage(stage, scored_non_clause_reskeys, non_clause_reskeys)

    result = StageReportData(utt_count=utt_count, stage=stage, stage_refinement=refined_stage[1], clause_measure_count=scored_utt_counts,
                             non_clause_reskeys=non_clause_reskeys, scored_non_clause_reskeys=scored_non_clause_reskeys)

    return result


def show_refined_stage(refined_stage: RefinedStage) -> str:
    stage, refinement = refined_stage
    refinement_string = '+' if refinement else ''
    result = f'{show_roman(stage)}{refinement_string}'
    return result


def get_non_clause_reskeys(stage: Stage,  allqueries: QueryDict) -> list:
    thereskeys = [mkresultskey(qid) for qid in allqueries if
                  allqueries[qid].fase == stage and allqueries[qid].process == core_process
                  and allqueries[qid].stars != 'star2' and query_inform(allqueries[qid]) and qid != LongXneg[0] and
                  allqueries[qid].subcat.lower() not in tarsp_clausetypes]
    return thereskeys


def get_refined_stage(stage: Stage, scored_reskeys, thereskeys) -> RefinedStage:
    refined = len(scored_reskeys) / len(thereskeys) > 0.5
    return stage, refined




def genpfi(stage: Stage, allresults: AllResults, allqueries: QueryDict) -> int:
    '''
    Obsolete. Not used anymore
    The function *genpfi* computes the *Profielscore* (PF) for the stage given by the
    parameter *stage* on the basis of *allresults* and the query dictionary *allqueries*.
    It selects the queries of the given stage that are core queries and that are not
    *star2* queries.

    From these, it only selects the ones for which the number of results is larger than 0.
    It adds *OndVC* if *OndWVC* or *OndWBVC* has been scored.
    Special measures for *Xneg*, *OndB*, *VCW* and *BX* still have to be implemented.
    The description in Schlichting (p. 23) is not specific enough.
    '''
    thereskeys = [mkresultskey(qid) for qid in allqueries if allqueries[qid].fase == stage and allqueries[qid].process == core_process
               and allqueries[qid].stars != 'star2' and query_inform(allqueries[qid]) and qid != LongXneg[0]]
    coreresults = allresults.coreresults
    scored_reskeys = [reskey for reskey in thereskeys if reskey in coreresults and len(coreresults[reskey]) > 0]
    # OndVC, VCW
    if any([lvcm in coreresults and len(coreresults[lvcm]) > 0 for lvcm in long_VC_measures] ):
       if stage == 2 and OndVC not in scored_reskeys:
           scored_reskeys.append(OndVC)
       if stage == 2 and VCW not in scored_reskeys:
           scored_reskeys.append(VCW)
    # XNeg
    if LongXneg in coreresults and len(coreresults[LongXneg]) > 0:
        if stage == 3 and Xneg not in scored_reskeys:
            scored_reskeys.append(Xneg)
    # OndB, BX
    if any([lbm in coreresults and len(coreresults[lbm]) > 0 for lbm in long_B_measures ]):
        if stage == 2 and OndB not in scored_reskeys:
            scored_reskeys.append(OndB)
        if stage == 2 and BX not in scored_reskeys:
            scored_reskeys.append(BX)
    # Into
    if any([vrm in coreresults and len(coreresults[vrm]) > 0 for vrm in vraagzin_measures]):
        if stage == 2 and Into not in scored_reskeys:
            scored_reskeys.append(Into)
    result = len(scored_reskeys)
    return result


def genpfiplus(stage: Stage, allresults: AllResults, allqueries: QueryDict) -> PFReportData:
    '''
    The function *genpfiplus* computes a PFReportData object for the stage given by the
    parameter *stage* on the basis of *allresults* and the query dictionary *allqueries*.
    It selects the queries of the given stage that are core queries and that are not
    *star2* queries.

    From these, it only selects the ones for which the number of results is larger than 0. It stores the
    results in the *scored_measures* field of the PFReportData object.

    It computes added measures (potentially for *Xneg*, *OndVC*, *OndB*, *VCW* and *BX*) and stores them
    in the added_measures field of the PFReportData object.
    This is based on Schlichting (2005/2017, p. 23), but is more specific  than described there.
    '''
    thereskeys = [mkresultskey(qid) for qid in allqueries if allqueries[qid].fase == stage and allqueries[qid].process == core_process
               and allqueries[qid].stars != 'star2' and query_inform(allqueries[qid]) and qid != LongXneg[0]]
    coreresults = allresults.coreresults
    scored_reskeys = [reskey for reskey in thereskeys if reskey in coreresults and len(coreresults[reskey]) > 0]
    additional_reskeys = {}
    # OndVC, VCW
    if any([lvcm in coreresults and len(coreresults[lvcm]) > 0 for lvcm in long_VC_measures] ):
       if stage == 2 and OndVC not in scored_reskeys:
           additional_reskeys[OndVC] = long_VC_measures
       if stage == 2 and VCW not in scored_reskeys:
           additional_reskeys[OndVC] = long_VC_measures
    # XNeg
    if LongXneg in coreresults and len(coreresults[LongXneg]) > 0:
        if stage == 3 and Xneg not in scored_reskeys:
            additional_reskeys[Xneg] = [LongXneg]
    # OndB, BX
    if any([lbm in coreresults and len(coreresults[lbm]) > 0 for lbm in long_B_measures ]):
        if stage == 2 and OndB not in scored_reskeys:
            additional_reskeys[OndB] = long_B_measures
        if stage == 2 and BX not in scored_reskeys:
            additional_reskeys[BX] = long_B_measures
    # Into
    if any([vrm in coreresults and len(coreresults[vrm]) > 0 for vrm in vraagzin_measures]):
        if stage == 2 and Into not in scored_reskeys:
            additional_reskeys[Into] = vraagzin_measures
    result = PFReportData(stage=stage, scored_measures=scored_reskeys, added_measures=additional_reskeys)
    return result



def pf2(allresults: AllResults, allqueries: QueryDict) -> int:
    '''
    The function *pf2* uses the function *genpfiplus* to compute the 'Profielscore' for Stage II
    '''

    pf2_report_data = genpfiplus(2, allresults, allqueries)
    result = len(pf2_report_data.scored_measures)
    return result


def pf3(allresults: AllResults, allqueries: QueryDict) -> int:
    '''
    The function *pf3* uses the function *genpfiplus* to compute the 'Profielscore' for Stage III
    '''
    pf3_report_data = genpfiplus(3, allresults, allqueries)
    result = len(pf3_report_data.scored_measures)
    return result




def pf4(allresults: AllResults, allqueries: QueryDict) -> int:
    '''
    The function *pf4* uses the function *genpfiplus* to compute the 'Profielscore' for Stage IV
    '''
    pf4_report_data = genpfiplus(4, allresults, allqueries)
    result = len(pf4_report_data.scored_measures)
    return result


def pf5(allresults: AllResults, allqueries: QueryDict):
    '''
    The function *pf5* uses the function *genpfiplus* to compute the 'Profielscore' for Stage V
    '''
    pf5_report_data = genpfiplus(5, allresults, allqueries)
    result = len(pf5_report_data.scored_measures)
    return result


def pf6(allresults: AllResults, allqueries: QueryDict) -> int:
    '''
    The function *pf6* uses the function *genpfiplus* to compute the 'Profielscore' for Stage VI
    '''
    pf6_report_data = genpfiplus(6, allresults, allqueries)
    result = len(pf6_report_data.scored_measures)
    return result


def pf7(allresults: AllResults, allqueries: QueryDict) -> int:
    '''
    The function *pf7* uses the function *genpfiplus* to compute the 'Profielscore' for Stage VII
    '''
    pf7_report_data = genpfiplus(7, allresults, allqueries)
    result = len(pf7_report_data.scored_measures)
    return result

def pfplus(allresults: AllResults, allqueries: QueryDict) -> List[PFReportData]:
    '''
    The function *pfplus* computes a list of PFReportData objects for each stage from stage 2 through stage 7.
    It does so by applying the function *genpfiplus* for each stage.

    .. autofunction:: sastadev.TARSPpostfunctions::genpfiplus

    '''
    pfi_result_list = [genpfiplus(stg, allresults, allqueries) for stg in range(2,8)]
    return pfi_result_list




def pf(allresults: AllResults, allqueries: QueryDict) -> int:
    '''
    The function *pf* computes the *'Profielscore'* for the whole sample (*PF*).

    It first uses the function *pfplus* to generate a list of *PFReportData*,
    containing one PFReportData object for each stage.

    .. autofunction:: sastadev.TARSPpostfunctions::pfplus

    It then sums the number of scored measures of each stage, and it sums the number of added measures of each stage.
    It then returns the total number of scored and added measures


    '''
    pfi_result_list = pfplus(allresults, allqueries)
    core_score = sum([len(prd.scored_measures) for prd in pfi_result_list])
    additional_score = sum([len(prd.added_measures) for prd in pfi_result_list])
    result = core_score + additional_score
    return result


def getname(allresults: AllResults, allqueries: QueryDict) -> str:
    '''
    The function *getname* obtains the name of the patient/child being investigated
    from the metadata. It uses the function *getmeta* to achieve this.

    '''
    result = getmeta('name')
    return result


def getchildage(allresults: AllResults, allqueries: QueryDict) -> str:
    '''
    The function *getchildage* is intended to obtain the age of the child being
    investigated from the metadata. It still has to be implemented. Currently it simply returns the empty string..

    '''
    result = ''
    return result

non_clause_measures_str = "Woordgroepen, Verbindingswoorden, Voornaamwoorden en Woordstructuren"
#def mk_stage_report(stage_report_data: StageReportData) -> List[str]:
def mk_stage_report_data(allresults: AllResults, thequeries: QueryDict, in_report_data) -> StageReportData:
    report_data = copy.deepcopy(in_report_data)
    full_stage_report_data = FullStageReportData()
    stage_report_data = gofaseplus(allresults, thequeries)
    full_stage_report_data.stage_report_data = stage_report_data
    utt_count = stage_report_data.utt_count
    stage = stage_report_data.stage
    stagecount = stage_report_data.clause_measure_count[stage]
    refinement = stage_report_data.stage_refinement
    refined_stage = stage, refinement
    fullstage = show_refined_stage(refined_stage)
    proportion = stagecount / utt_count
    pct = proportion * 100
    gofase_minthreshold_pct = gofase_minthreshold * 100
    full_stage_report_data.fullstage = fullstage
    full_stage_report_data.proportion = proportion

    higher_stages = [stg for stg in stage_report_data.clause_measure_count if stg > stage]
    higher_stages_clause_counts = {stg: stage_report_data.clause_measure_count[stg] for stg in higher_stages if stg in stage_report_data.clause_measure_count}
    higher_stages_clause_sum = sum([stage_report_data.clause_measure_count[stg] for stg in higher_stages])
    total_clause_count = stagecount + higher_stages_clause_sum
    total_proportion = total_clause_count / utt_count
    total_pct = total_proportion * 100

    full_stage_report_data.higher_stages = higher_stages
    full_stage_report_data.higher_stages_clause_counts = higher_stages_clause_counts


    # refinement
    refinement_proportion = len(stage_report_data.scored_non_clause_reskeys) / len(stage_report_data.non_clause_reskeys)
    lscored = len(stage_report_data.scored_non_clause_reskeys)
    lnonclause = len(stage_report_data.non_clause_reskeys)

    full_stage_report_data.refinement_proportion = refinement_proportion
    full_stage_report_data.lscored = lscored
    full_stage_report_data.lnonclause = lnonclause

    report_data.full_stage_report_data = full_stage_report_data

    return report_data

non_clause_measures_str = "Woordgroepen, Verbindingswoorden, Voornaamwoorden en Woordstructuren"
#def mk_stage_report(stage_report_data: StageReportData) -> List[str]:
def mk_stage_report(allresults: AllResults, thequeries: QueryDict, report_data) -> List[str]:
    full_stage_report_data = report_data.full_stage_report_data
    stage_report_data = full_stage_report_data.stage_report_data
    report = ["", "", "Fase", ""]
    utt_count = stage_report_data.utt_count
    stage = stage_report_data.stage
    roman_stage = show_roman(stage)
    stagecount = stage_report_data.clause_measure_count[stage]
    fullstage = full_stage_report_data.fullstage
    proportion = stagecount / utt_count
    pct = proportion * 100
    gofase_minthreshold_pct = gofase_minthreshold * 100
    newpar = f"De vastgestelde fase inclusief verfijning is {fullstage}."
    report.append(newpar)
    if proportion >= gofase_minthreshold:
        newpars = [f"Fase {roman_stage} is de hoogste fase waarin  {gofase_minthreshold_pct:.2f}% of meer van de uitingen gevonden zijn bij de Zinsconstructies.",
                   f"Er zijn in deze fase namelijk {stagecount} uitingen gevonden in {utt_count} uitingen ({pct:.2f}%, en dat is groter dan of gelijk aan {gofase_minthreshold_pct:.2f}%)."
                   ]
        report.extend(newpars)
    else:
        higher_stages = [stg for stg in stage_report_data.clause_measure_count if stg > stage]
        higher_stages_clause_counts = {stg: stage_report_data.clause_measure_count[stg] for stg in higher_stages if stg in stage_report_data.clause_measure_count}
        higher_stages_clause_counts_str = conj([f'{stg}: {val}' for stg, val  in higher_stages_clause_counts.items()])
        higher_stages_clause_sum = sum([stage_report_data.clause_measure_count[stg] for stg in higher_stages])
        total_clause_count = stagecount + higher_stages_clause_sum
        total_proportion = total_clause_count / utt_count
        total_pct = total_proportion * 100
        iszijn = 'is' if stagecount == 1 else 'zijn'
        uitingorpl = 'uiting' if stagecount == 1 else 'uitingen'
        newpars = [f"Weliswaar {iszijn} er in fase {stage} slechts {stagecount} {uitingorpl} gevonden in {utt_count} uiting{'' if utt_count == 1 else 'en'} bij de Zinsconstructies ({pct:.2f}%), ",
                   f"maar de zinsmaten van de hogere fases ({higher_stages_clause_counts_str}) mogen meegerekend worden (samen: {higher_stages_clause_sum}).",
                   f"Daarmee komt het totaal op {total_clause_count} in {utt_count} uiting{'' if utt_count == 1 else 'en'} ({total_pct:.2f}%, en dat is groter dan of gelijk aan {gofase_minthreshold_pct:.2f}%). ",]
        report.extend(newpars)

    # refinement
    refinement_proportion = len(stage_report_data.scored_non_clause_reskeys) / len(stage_report_data.non_clause_reskeys)
    lscored = len(stage_report_data.scored_non_clause_reskeys)
    lnonclause = len(stage_report_data.non_clause_reskeys)
    newpars = [f"Er is in fase {stage} gescoord voor {lscored} taal{'maat' if lscored == 1 else 'maten'} van de {non_clause_measures_str}, " +
               f"op een totaal van  {lnonclause} van dergelijke taalmaten."]
    if refinement_proportion > 0.5:
        newpars.append(f'Dat is meer dan de helft en daarom is een + voor verfijning van de fase toegekend.')
    else:
        newpars.append(f'Dat is niet meer dan de helft en daarom is er geen + voor verfijning toegekend.')
    report.extend(newpars)

    # comparison with norm table 1
    newpars = [""]
    report.extend(newpars)
    age = report_data.speaker_metadata['childage'] if 'childage' in report_data.speaker_metadata else None
    gender = report_data.speaker_metadata['sex'] if 'sex' in report_data.speaker_metadata else None
    ses = report_data.speaker_metadata['SES'] if 'SES' in report_data.speaker_metadata else None
    newpars = compare_with_norm_stage(roman_stage, age, gender, ses)
    report.extend(newpars)

    return report

def mk_tarsp_p_report(pf_report_data_list, uttcount, allresults) -> List[str]:
    tuples = []
    for prd in pf_report_data_list:
        scores = [sumfreq(allresults.coreresults[reskey]) for reskey in prd.scored_measures]
        sum_score = sum(scores)
        newtuple = (prd.stage, sum_score)
        tuples.append(newtuple)
    tarsp_p_abs = sum([stg * mcount for stg, mcount in tuples])
    tarsp_p = tarsp_p_abs / uttcount
    tuple_str = ' + '.join([f'{stg} * {mcount}' for stg, mcount in tuples])
    tarsp_p_report = ["", "", "TARSP_P", "", "TARSP_P is een score die een aanduiding is voor de gemiddeldde zinscomplexiteit.",
                      "Deze score is gedefinieerd door [Bruinsma et al. 2020]."]
    newpars = ["Deze score staat niet vermeld op de profielkaart.", "De waarde van TARSP_P is:" ,
                f"({tuple_str}) / {uttcount} = {tarsp_p_abs} / {uttcount} = {tarsp_p:.2f}",
               ]
    tarsp_p_report.extend(newpars)
    return tarsp_p_report


def mk_pf_report(allresults: AllResults, thequeries: QueryDict) -> List[str]:
    report = ["", "", "Profielscore", ""]
    pf_report_data_list = pfplus(allresults, thequeries)
    pfi_scores = [len(prd.scored_measures) for prd in pf_report_data_list]
    core_pf_score = sum(pfi_scores)
    sum_str = ' + '.join([str(score) for score in pfi_scores])
    newpar = f"De profielscores per fase resulteren in {sum_str} = {core_pf_score} taalmaten"
    report.append(newpar)
    addable_taalmaten_str = mk_measure_str(addable_taalmaten, thequeries)
    newpar = f"De taalmaten {addable_taalmaten_str} kunnen in bepaalde gevallen meegeteld worden voor de profielscore ook als er niet voor gescoord is."
    report.append(newpar)
    scored_addables = [meas for meas in addable_taalmaten if meas in allresults.coreresults and
                       sumfreq(allresults.coreresults[meas]) != 0]
    scored_addables_str = mk_measure_str(scored_addables, thequeries)
    hoeven_sgpl = "hoeft" if len(scored_addables) == 1 else "hoeven"
    newpar = f"Er zijn voorbeelden gevonden voor {scored_addables_str}, dus die {hoeven_sgpl} niet toegevoegd te worden." if scored_addables != [] else ""
    if newpar != "":
        report.append(newpar)
    added_pf_score = 0
    added_measure_found = False
    found_added_measures = []
    for prd in pf_report_data_list:
        for added_measure in prd.added_measures:
            found_added_measures.append(added_measure)
            added_measure_found = True
            added_qid = added_measure[0]
            added_item = thequeries[added_qid].item
            cand_cause_measures = prd.added_measures[added_measure]
            cause_measures = [meas for meas in cand_cause_measures if meas in allresults.coreresults and
                              sumfreq(allresults.coreresults[meas]) != 0]
            cause_items = [thequeries[meas[0]].item for meas in cause_measures]
            cause_item_str = conj(cause_items)
            if added_measure == Xneg:
                longxneg_counter = allresults.coreresults[LongXneg] if LongXneg in allresults.coreresults else {}
                longxneg_uttids = [uttid for uttid in longxneg_counter if longxneg_counter[uttid] != 0]
                if longxneg_uttids == []:
                    settings.LOGGER.error(f'No LongXneg measures found for {added_measure} measure')
                longxneg_uttids_str = conj(longxneg_uttids)
                newpar = f"Taalmaat {added_item} wordt toegevoegd omdat er minimaal één langere uiting met 'niet' is gescoord, namelijk {longxneg_uttids_str}."
            else:
                newpar = f"Taalmaat {added_item} wordt toegevoegd omdat er gescoord is voor {cause_item_str}."
            report.append(newpar)
            added_pf_score += 1
    rest_addables = [meas for meas in addable_taalmaten if meas not in found_added_measures + scored_addables]
    for rest_addable in rest_addables:
        the_item = thequeries[rest_addable[0]].item
        causes = addable_dict[rest_addable] if rest_addable in addable_dict else []
        if causes != []:
            causes_str = mk_measure_str(causes, thequeries, coord=disj)
            if rest_addable == Xneg:
                newpar = f"{the_item} wordt niet toegevoegd omdat er geen enkele langere uiting met 'niet' is gescoord."
            else:
                newpar = f"{the_item} wordt niet toegevoegd omdat er voor geen van de taalmaten {causes_str} gescoord is."
            report.append(newpar)
    # if not added_measure_found:
    #     all_add_causes = long_VC_measures + long_B_measures + [Into] + [LongXneg]
    #     all_add_cause_items = [thequeries[meas[0]].item for meas in all_add_causes]
    #     unique_add_cause_items = sorted(list(set(all_add_cause_items)))
    #     all_add_cause_items_str = ', '.join(unique_add_cause_items)
    #     cand_add_measures = [OndVC, OndB, VCW, BX, Into, Xneg]
    #     cand_add_measure_items = [thequeries[m[0]].item for m in cand_add_measures]
    #     cand_add_measures_str = ', '.join(cand_add_measure_items)
    #     newpar = f"Geen van de taalmaten {cand_add_measures_str} worden toegevoegd omdat er al voor gescoord is of omdat er niet gescoord is voor {all_add_cause_items_str}"
    #     report.append(newpar)
    pf = allresults.postresults[pf_qid]
    if pf != core_pf_score + added_pf_score:
        settings.LOGGER.error(f'pf ({pf}) is not identical to core_pf_score ({core_pf_score}) + added_pf_score ({added_pf_score}) = {core_pf_score + added_pf_score}')
    newpars = ["", f"Daarmee komt de totale profielscore (PF) uit op {core_pf_score} + {added_pf_score} = {pf}"]
    report.extend(newpars)

    # extend with TARSP_P score
    pf1_prd = genpfiplus(1, allresults, thequeries)
    utt_count = allresults.postresults[gtotaal_qid]
    Tarsp_p_report = mk_tarsp_p_report([pf1_prd] + pf_report_data_list, utt_count, allresults)

    report.extend(Tarsp_p_report)

    return report

def mk_missing_measures_report(stage: int, allresults: AllResults, thequeries: QueryDict) -> List[str]:
    ## @@ extend but first extend method definition
    start = 1 if stage == 1 else 2
    for stg in range(start, stage + 1):
        raw_unscored_queries = [qid for qid in thequeries if thequeries[qid].fase == stg and
                                    thequeries[qid].stars != "star2" and
                                    thequeries[qid].stars != "star1" and
                                    sumfreq(allresults.coreresults[mkresultskey(qid)]) == 0
                               ]
        #implied_queries = [qid for qid in raw_unscored_queries if any([el for el in implied_qid[qid] if qid in implied ])]


def mk_toelichting(allresults: AllResults, thequeries: QueryDict):

    report_data = ReportData(sample_name = getbasename(allresults.filename), speaker_metadata=allresults.speaker_metadata)

    report_data = mk_stage_report_data(allresults, thequeries, report_data)
    stage_report_data = report_data.full_stage_report_data.stage_report_data
    stage = stage_report_data.stage

    age = allresults.speaker_metadata['childage'] if 'childage' in allresults.speaker_metadata else ''


    full_report = [f"TARSP rapport  bij het taalprofielformulier voor sample {report_data.sample_name}", ""]

    speaker_report = mk_speaker_report(report_data)
    full_report.extend(speaker_report)
    stage_report = mk_stage_report(allresults, thequeries, report_data)
    full_report.extend(stage_report)
    pf_report = mk_pf_report(allresults, thequeries)
    full_report.extend(pf_report)
    GZW_report = mk_GZW_report(allresults, thequeries, stage, age)
    full_report.extend(GZW_report)

    outfullname = get_toelichting_filename(allresults.filename, '_form_toelichting')
    with open(outfullname, 'w', encoding='utf-8') as outfile:
        print('\n'.join(full_report), file=outfile)

def get_GZW(allresults: AllResults) -> tuple:
    total_wc = sum([wc for _, wc in allresults.commwordcounts])
    utt_count = len(allresults.commwordcounts)
    result = total_wc / utt_count
    return total_wc, utt_count, result

def mk_GZW_report(allresults: AllResults, thequeries: QueryDict, stage, age) -> List[str]:
    report = ["","","Gemiddelde Zinslengte in Woorden (GZW)", '']
    total_wc, utt_count, gzw = get_GZW(allresults)
    newpar = f"De Gemiddelde zinslengte in woorden (GZW) is {total_wc} / {utt_count} = {gzw:.2f}."
    report.append(newpar)

    # vergelijking met norm @@ to do
    newpars = mk_gwz_compare_report(gzw, stage, age)
    report.extend(newpars)

    return report


max_z = 2


def compare_with_norm_by_stage(gzw, stage) -> Optional[Tuple[float, float]]:
    roman_stage = show_roman(stage)
    if roman_stage in gzw_by_stage:
        norm_row = gzw_by_stage[roman_stage]
        diff = gzw - norm_row[2]
        sd = norm_row[3]
        z = diff / sd
        return diff, z
    else:
        return None


def compare_with_norm_by_age(gzw, age) -> Optional[Tuple[float, float]]:
    norm_data = gzw_by_age
    norm_row = None
    ch_age = childes_age_from_string(age)
    if ch_age is None:
        return None
    for b, e in norm_data:
        ch_b = childes_age_from_string(b)
        ch_e = childes_age_from_string(e)
        if ch_age >= ch_b and ch_age < ch_e:
            norm_row = gzw_by_age[(b, e)]
            break
    if norm_row is not None:
        diff = gzw - norm_row[2]
        sd = norm_row[3]
        z = diff / sd
        return diff, z
    else:
        return None


def mk_comparison_report(comparison, item) -> List[str]:
    report = []
    if comparison is None:
        newpars = ["", f"Een vergelijking met normwaarden voor GZW per {item} is niet mogelijk."]
        report.extend(newpars)
    else:
        diff, z = comparison
        newpar = f"Het verschil met het gemiddelde van de GZW per {item}  bedraagt {diff:.2f} en de z-waarde is {z:.2f}."
        report.append(newpar)
        if abs(z) >= max_z:
            newpar = "Dit is een groot verschil."
        else:
            newpar = "Dit is een verschil dat  verwaarloosd kan worden."
        report.append(newpar)
    return report

def mk_compare_with_norm_high_age_report(gzw, age):
    report = []
    mindiff = 100
    min_b = None
    min_e = None
    for b, e in gzw_by_age:
        gzw_b_e = gzw_by_age[(b, e)][2]
        diff = gzw - gzw_b_e
        if abs(diff) <= abs(mindiff):
            mindiff = diff
            min_b = b
            min_e = e
    closest_cat = gzw_by_age[(min_b, min_e)]
    thediff = gzw - closest_cat[2]
    sd = closest_cat[3]
    z = thediff / sd

    norm_age = normalise_age(age)

    newpars = ["", f"De leeftijd van het kind ({norm_age}) is hoger dan 4 jaar. Daarom is een directe vergelijking van de GZW met de norm niet mogelijk.",
               f"De GZW voor dit kind ({gzw:.2f}) ligt het dichtst bij de GZW van de leeftijdscategorie {b}-{e}.",
               f"Het verschil hiermee is {thediff:.2f} met een z-waarde van {z:.2f}."]

    report.extend(newpars)
    return report


def mk_gwz_compare_report(gzw, stage, age) -> List[str]:
    report = []
    comparison1 = compare_with_norm_by_stage(gzw, stage)

    comparison_report = mk_comparison_report(comparison1, 'fase')
    report.extend(comparison_report)

    comparison_report = mk_compare_with_norm_high_diff_report(gzw, stage)
    report.extend(comparison_report)

    age_str = age if (age is not None and age != '')  else 'onbekend'
    # newpars = ["", f"De leeftijd van het kind is {age_str}."]
    # report.extend(newpars)
    if age < '4;':
        comparison2 = compare_with_norm_by_age(gzw, age)
        comparison_report = mk_comparison_report(comparison2, 'leeftijd')
    else:
        comparison_report = mk_compare_with_norm_high_age_report(gzw, age)
    report.extend(comparison_report)

    return report

def mk_compare_with_norm_high_diff_report(gzw, stage) -> List[str]:
    report = []
    highest_norm_gzw = gzw_by_stage['VI']
    if gzw > highest_norm_gzw[2]:
        diff = gzw - highest_norm_gzw[2]
        sd = highest_norm_gzw[3]
        z = diff / sd
        newpars = ["", f"De GZW ({gzw:.2f}) is groter dan de grootste GZW in de normtabel voor fases." +
                   f"Het verschil is {diff:.2f} met een z-waarde van {z:.2f}."]
    else:
        mindiff = 100
        min_stage = None
        for stg in gzw_by_stage:
            stg_gzw = gzw_by_stage[stg][2]
            diff = gzw - stg_gzw
            if abs(diff) < abs(mindiff):
                mindiff = diff
                min_stage = stg
                sd = gzw_by_stage[stg][3]
        roman_min_stage = show_roman(min_stage)
        diff = gzw - gzw_by_stage[min_stage][2]
        z = diff / sd
        newpars = [f"De GZW ({gzw:.2f}) verschilt het minst met de GZW voor fase {roman_min_stage}.",
                   f"Het verschil is {mindiff:.2f} en de z-waarde is  {z:.2f}."]
    report.extend(newpars)
    return report

def mk_speaker_report(report_data) -> List[str]:
    speaker_metadata = report_data.speaker_metadata
    sample = report_data.sample_name

    gender = normalise_gender(speaker_metadata['sex'])
    age = normalise_age(speaker_metadata['childage'])
    if gender not in {boy, girl}:
        gender_str = child
    else:
        gender_str = gender
    if age is None:
        age_str = f'van onbekende leeftijd'
    else:
        age_str = f'met leeftijd {age}'

    ses = speaker_metadata['SES'] if 'SES' in speaker_metadata else None

    if ses is not None and ses != '':
        ses_pars = [f"De waarde voor Sociaal Economische Status (SES) is {ses}"]
        if ses not in {'A', 'B'}:
            newstr = "Deze waarde kan niet gerelateerd worden aan de TARSP waardes A of B voor milieu, en wordt daarom genegeerd."
            ses_pars.append(newstr)
    else:
        ses_pars =["Er is geen informatie over de Sociaal Economische Status (SES) van het kind."]

        # intro
    newpars = [f"Dit is het rapport voor het spontane-taalsample {sample}. Dit sample is het transcript van een gesprek met een {gender_str} {age_str}."]
    if gender_str == child:
        no_gender_str = "Het geslacht van het kind is niet bekend."
        newpars.append(no_gender_str)

    newpars.extend(ses_pars)

    return newpars


def compare_with_norm_stage(romanstage: str, raw_age: str, raw_gender: str = None, ses: str = None) -> List[str]:
    gender = normalise_gender(raw_gender)
    age = normalise_age(raw_age)
    if ses == '':
        ses = None

    base_message =  f'De ontwikkeling van het onderzochte kind komt overeen met'

    # age, gender, ses check stage
    filtered_rows = [row for row in norm_tabel_1_data if (gender is None or row[3] == gender) and
                    age >= row[1] and age < row[2] and (ses is None or row[4] == ses) and romanstage == row[6]]
    if filtered_rows != []:
        message2_list = []
        for row in filtered_rows:
           snelheid = adapt_snelheid(row[5])
           message2 = f' een {snelheid} ontwikkeling voor een {row[3]} van leeftijdsgroep {row[0]} ({row[1]}-{row[2]}) van milieu {row[4]}'
           message2_list.append(message2)
        full_message2 = ' of \n'.join(message2_list) + "."

        concl_message = f"\n\nDe leeftijd van het kind komt hiermee overeen. De taal van het kind ontwikkelt zich op normale wijze."
        message = base_message + full_message2 + concl_message



    else:
        # leave out the age condition
        filtered_rows = [row for row in norm_tabel_1_data if (gender is None or row[3] == gender) and
                         (ses is None or row[4] == ses) and romanstage == row[6]]

        # if needed leave out the ses condition (ses has a value that cannot be mapped to A or B)
        if filtered_rows == []:
            filtered_rows = [row for row in norm_tabel_1_data if (gender is None or row[3] == gender) and
                             romanstage == row[6]]

        if filtered_rows != []:

            # select nu de rows met hoogste leeftijdklasses en als daar geen snel  of gemiddelde bij zit dan ook de rows hoogste leeftijdklasse met snel
            highest_age_class_filtered_rows = listmax(filtered_rows, key=lambda row: row[0])
            if not any([row[5] in  snel_gemiddeld for row in highest_age_class_filtered_rows]):
                additional_rows = [row for row in filtered_rows if row[5] in snel_gemiddeld]
            else:
                additional_rows = []
            if gender is None:
                girl_rows = [row for row in additional_rows if row[3] == girl]
                boy_rows = [row for row in additional_rows if row[3] == boy]
                highest_girl_rows = listmax(girl_rows, key = lambda row: row[0])
                highest_boy_rows = listmax(boy_rows, key = lambda row: row[0])
                highest_age_additional_rows = highest_girl_rows + highest_boy_rows
            else:
                highest_age_additional_rows = listmax(additional_rows, key = lambda row: row[0])


            all_rows = highest_age_class_filtered_rows + highest_age_additional_rows
            message2_list = []
            for row in all_rows:
                snelheid = adapt_snelheid(row[5])
                message2 = f' een {snelheid} ontwikkeling voor een {row[3]} van leeftijdsgroep {row[0]} ({row[1]}-{row[2]}) van milieu {row[4]}'
                message2_list.append(message2)
            full_message2 = ' of \n'.join(message2_list)

            lowest_rows = listmin(all_rows, key = lambda row: row[0])
            lowest_row = lowest_rows[0]
            highest_rows = listmax(all_rows, key = lambda row: row[0])
            highest_row = highest_rows[0]
            if age < lowest_row[1]:
                diff = month_diff(lowest_row[1], age)
                concl_message = f"\n\nDe leeftijd van het kind is lager dan de ondergrens van het laagste genoemde leeftijdsinterval. Het verschil is {diff} maanden. De taal van het kind ontwikkelt zich sneller dan gewoonlijk."
            elif age == lowest_row[1]:
                concl_message = f'\n\nDe leeftijd van het kind is precies gelijk aan de ondergrens van het laagste genoemde leeftijdsinterval. De taal van het kind ontwikkelt zich normaal.'
            elif age > highest_row[2]:
                diff = month_diff(age, highest_row[2])
                concl_message = f"\n\nDe leeftijd van het kind is hoger dan de bovengrens van het hoogste genoemde leeftijdsinterval. Het verschil is {diff} maanden. Mogelijk is hier sprake van een taalontwikkelingsstoornis (TOS)."
            elif age == highest_row[2]:
                concl_message = f'\n\nDe leeftijd van het kind is precies gelijk aan de bovengrens van het hoogste genoemde leeftijdsinterval. De taal van het kind ontwikkelt zich normaal.'
            else:
                concl_message = ''
            message = base_message + full_message2 + concl_message
        else:
            message = "Met de aangeboden gegevens kan geen vergelijking met de normtabellen voor fases gemaakt worden."

    return [message]


def listmax(xs: list, key: Callable) -> list:
    themax = None
    results = []
    for row in xs:
        if themax is None or key(row) > themax:
            results = [row]
            themax = key(row)
        elif key(row) < themax:
            pass
        else:
            results.append(row)
    return results

def listmin(xs: list, key: Callable) -> list:
    themin = None
    results = []
    for row in xs:
        if themin is None or key(row) < themin:
            results = [row]
            themin = key(row)
        elif key(row) > themin:
            pass
        else:
            results.append(row)
    return results



gender_dict = {'male': boy, 'female': girl, boy: boy, girl: girl, '': None}
def normalise_gender(raw_gender: str) -> str:
    if raw_gender in gender_dict:
        result = gender_dict[raw_gender.lower()]
    else:
        result = raw_gender
        settings.LOGGER.error(f"Unknown gender: {raw_gender}")
    return result

def adapt_snelheid(wrd: str) -> str:
    if wrd == 'langzaam':
        result = 'langzame'
    elif wrd == 'gemiddeld':
        result = 'gemiddelde'
    elif wrd == 'snel':
        result = 'snelle'
    else:
        result = wrd
    return result




