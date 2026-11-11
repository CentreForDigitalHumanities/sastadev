from dataclasses import dataclass
from typing import List


@dataclass
class StageReportData():
    utt_count : int
    stage: int
    stage_refinement: bool
    clause_measure_count: dict
    non_clause_reskeys: dict
    scored_non_clause_reskeys: list

@dataclass
class FullStageReportData():
    stage_report_data: StageReportData = None
    fullstage : str = None
    proportion : float = None
    refinement_proportion: float = None
    lscored : int = None
    lnonclause : int = None




@dataclass
class PFiReportData():
    stage: int
    scored_measures: list
    added_measures: dict

@dataclass
class PFReportData():
   stage_reports: List[PFiReportData]
   pf : int
   pfi_scores : List[int]

@dataclass
class GZWReportData():
    wc: int
    utt_count: int
    gzw: int

@dataclass
class LeerdoelenReportData():
    stage: int = None
    leerdoelen_by_stage: dict = None
    natuurlijke_hiaten: dict = None

@dataclass
class ReportData():
    sample_name: str = None
    speaker_metadata: dict = None
    full_stage_report_data: FullStageReportData = None
    pf_report_data: PFReportData = None
    gzw_report_data: GZWReportData = None
    leerdoelen_report_data: LeerdoelenReportData = None
