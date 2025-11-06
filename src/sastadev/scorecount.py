from typing import List, Tuple

class ScoreCount:
    recall : float
    precision : float
    f1_score : float
    count : int
    def __init__(self, recall, precision, f1_score, cnt):
        self.recall = recall
        self.precision = precision
        self.f1_score = f1_score
        self.count = cnt

def scorecount_avg(scorecounts: List[ScoreCount]) -> Tuple[float, float, float]:
    countsum = sum([sc.count for sc in scorecounts])
    allrecall = sum([sc.recall * sc.count for sc in scorecounts]) / countsum if countsum != 0 else 0
    allprecision = sum(sc.precision * sc.count for sc in scorecounts) / countsum if countsum != 0 else 0
    allf1_score = sum([sc.f1_score * sc.count for sc in scorecounts]) / countsum if countsum != 0 else 0
    result = allrecall, allprecision, allf1_score
    return result



