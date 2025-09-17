from collections import defaultdict
from sastadev.sastatypes import Table
from typing import List, Tuple

def get_samplename_uttids_tuples(data: Table, samplecol: int, uttidcol: int) -> List[Tuple[str, List[str]]]:
    thedict = defaultdict(list)
    for row in data:
        samplename = row[samplecol]
        uttid = row[uttidcol]
        if uttid not in thedict[samplename]:
            thedict[samplename].append(uttid)
    result = thedict.items()
    return result
