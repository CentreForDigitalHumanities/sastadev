from typing import List, Tuple
from sastadev.celexlexicon import dsldict, dslHead, dsllemmaposindex, dslSubClassPNum, pos2posnum
from collections import defaultdict

comma = ','

# The dsl.cd file contains the following fields:
# dslIdNum, dslHead, dslInl, dslClassNum, dslGendNum, dslDeHetNum, dslPropNum, \
#    dslAuxNum, dslSubClassVNum, dslSubCatNum, dslAdvNum, dslCardOrdNum, dslSubClassPNum = 0, 1, 2, 3, 4, 5, 6, 7, 8,
#    9, 10, 11, 12


def get_subclass(lemma: str, pt: str) -> List[Tuple[str, str]]:
    if pt in pos2posnum:
        entries = dsllemmaposindex[(lemma, pos2posnum[pt])]
        for entry in entries:
            if pt == 'vnw':
                vwtypecode = entry[dslSubClassPNum]
    else:
        #  issue a warning
        return []


def findcodes(col: int) -> dict:
    resultdict = defaultdict(list)
    for id in dsldict:
        entry = dsldict[id]
        if len(entry) > col:
            lemma = entry[dslHead]
            resultdict[entry[col]].append(lemma)
    return resultdict


if __name__ == '__main__':
    thedict = findcodes(dslSubClassPNum)
    for key in thedict:
        if key != '':
            print(f'{key}: {comma.join(thedict[key])}')

