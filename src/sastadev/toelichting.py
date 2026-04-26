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
class PFReportData():
    stage: int
    scored_measures: list
    added_measures: dict
