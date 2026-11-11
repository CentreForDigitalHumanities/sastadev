
from sastadev.conf import settings
from sastadev.methods import supported_methods, Method
from sastadev.readmethod import read_method
from sastadev.sastatypes import QueryDict, QId
from sastadev.stringfunctions import str2list
from typing import List, Optional

def get_method_by_name(method_name: str, variant=None) -> Optional[Method]:
    if method_name in supported_methods:
        filename = supported_methods[method_name]
        result = read_method(method_name, filename, variant=variant)
        return result
    else:
        settings.LOGGER.error(f'Method name {method_name} is not supported.')
        return None

def get_implied_by(qid: QId, queries: QueryDict) -> List[QId]:
    base_implied_by = queries[qid].implied_by
    implied_by = base_implied_by
    for aqid in base_implied_by:
        new_qids = get_implied_by(aqid, queries)
        implied_by.extend(new_qids)
    return implied_by

tarsp_method = get_method_by_name('tarsp')
tarsp_queries = tarsp_method.queries

tarsp_implied_by_dict = {qid: get_implied_by(qid, tarsp_queries) for qid in tarsp_queries}

junk = 0
