from dataclasses import dataclass


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
class PFReportData():
    stage: int
    scored_measures: list
    added_measures: dict

@dataclass
class GZWReportData():
    pass



@dataclass
class ReportData():
    sample_name: str = None
    speaker_metadata: dict = None
    full_stage_report_data: FullStageReportData = None
    pf_report_data: PFReportData = None
