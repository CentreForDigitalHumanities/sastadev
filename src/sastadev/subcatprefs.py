import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from sastadev.conf import settings
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getattval
from sastadev.xlsx import getxlsxdata

OTH = 'OTH'
TRG = 'TRG'

subcatlexiconfilename = 'sasta_subcatlexicon.xlsx'
subcatlexiconfolder = 'data/subcatlexicon'
subcatlexiconfullname = os.path.join(settings.SD_DIR, subcatlexiconfolder, subcatlexiconfilename)



def frq2relfrq(scfrqlist: Tuple[Any, int]) -> Tuple[Any, float]:
    total = sum([frq for sc, frq in scfrqlist])
    result = [(sc, frq/total*100) for sc, frq in scfrqlist]
    return result

def frqlex2relfrqlex(tempsubcatlexicon: dict) -> dict:
    subcatlexicon = {}
    for lemma in tempsubcatlexicon:
        relfrqlist = frq2relfrq(tempsubcatlexicon[lemma])
        for sc, relfrq in relfrqlist:
            subcatlexicon[(lemma, sc)] = int(round(relfrq))
    return subcatlexicon

def groupsc(sclex: Dict[str, Dict[str, int]]) -> Dict[str, List[Tuple[str, int]]]:
    newsclex : Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    for lemma in sclex:
        for sc in sclex[lemma]:
            frq = sclex[lemma][sc]
            newsclex[lemma].append((sc, frq))
    return newsclex


def getsubcatprefscore(stree: SynTree) -> int:
    resultscore = 0
    # gather the verbs
    verbnodes = stree.xpath('.//node[@pt="ww"]')
    for verbnode in verbnodes:
        sc = getattval(verbnode, 'sc')
        lemma = getattval(verbnode, 'lemma')
        if (lemma, sc) in oth_subcatlexicon:
            resultscore += oth_subcatlexicon[(lemma, sc)]
        elif (lemma, sc) in trg_subcatlexicon:
            resultscore += trg_subcatlexicon[(lemma, sc)]
    return resultscore





scheader, scdata = getxlsxdata(subcatlexiconfullname)

oth_tempsubcatlexicon = defaultdict(lambda: defaultdict(int))
trg_tempsubcatlexicon = defaultdict(lambda: defaultdict(int))
all_tempsubcatlexicon = defaultdict(lambda: defaultdict(int))


# lemma sc role rolecat frq
for row in scdata:
    lemma = row[0]
    if lemma == '':
        continue
    sc = row[1]
    rolecat = row[3]
    frqstr = row[4]
    frq = int(frqstr) if frqstr != '' else 0
    upper_rolecat = rolecat.upper()
    if upper_rolecat == OTH:
        oth_tempsubcatlexicon[lemma][sc] += frq
    elif upper_rolecat == TRG:
        trg_tempsubcatlexicon[lemma][sc] += frq
    else:
        settings.LOGGER.error(f'Illegal rolecat encountered in:\n {str(row)}')
    all_tempsubcatlexicon[lemma][sc] += frq

# now group the sc's of the same lemma under this lemma
oth_temp2subcatlexicon = defaultdict(list)
trg_temp2subcatlexicon = defaultdict(list)
all_temp2subcatlexicon = defaultdict(list)

oth_temp2subcatlexicon = groupsc(oth_tempsubcatlexicon)
trg_temp2subcatlexicon = groupsc(trg_tempsubcatlexicon)
all_temp2subcatlexicon = groupsc(all_tempsubcatlexicon)


# now convert the frequencies in relative frequencies to use them as integer score (0 - 100)
oth_subcatlexicon = frqlex2relfrqlex(oth_temp2subcatlexicon)
trg_subcatlexicon = frqlex2relfrqlex(trg_temp2subcatlexicon)
all_subcatlexicon = frqlex2relfrqlex(all_temp2subcatlexicon)

# we can deleter the temporary lexicons

del oth_tempsubcatlexicon
del trg_tempsubcatlexicon
del all_tempsubcatlexicon

del oth_temp2subcatlexicon
del trg_temp2subcatlexicon
del all_temp2subcatlexicon
