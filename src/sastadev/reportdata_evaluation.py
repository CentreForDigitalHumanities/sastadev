"""
module to carry out an evaluation in terms of stage, stage refinement, profile score, GZW, leerdoelen.
"""

from dataclasses import dataclass

from sastadev.allresults import AllResults
from sastadev.toelichting import ReportData

@dataclass
class EvaluationData():
    stage: int
    refinement: bool
    profile_score: int
    gzw: float
    leerdoelen: dict

def get_evaluation_data(report_data: ReportData, allresults: AllResults) -> EvaluationData:
    result = EvaluationData()
    result.stage = report_data.full_stage_report_data.stage_report_data.stage
    result.refinement = report_data.full_stage_report_data.stage_report_data.refinement
    result.profile_score = report_data.pf_report_data.pf
    result.gzw = report_data.gzw_report_data.gzw
    result.leerdoelen =report_data.leerdoelen_report_data.leerdoelen_by_stage
    return result


