"""
module to generate SAF files with revised tokenisation
"""

from collections import defaultdict
from dataclasses import dataclass
from sastadev.allresults import AllResults
from sastadev.alt_tokenisation import retokenize, tokenisation_xpath
from sastadev.cleanCHILDEStokens import cleantokens, cleantext
from sastadev.conf import settings
from sastadev.methods import Method, tarsp, stap, asta
from sastadev.resultsbyutterance import getresultsbyutt, getexactbyutt
from sastadev.sastatypes import HeadedTable, Table, UttId
from sastadev.treebankfunctions import find1, getorigutt, getsentence

from typing import Dict, List

from sastadev.xlsx import mkworkbook, xlsx_writerow

import xlsxwriter

levelcol = 1
utt_labels = ['Uiting']

comma = ','

# constants for levels
uiting = 'Uiting'
opmerkingen = 'Opmerkingen'
sasta_opm = 'SASTA-opm'

# default header pair
default_header_pair = (['Uiting', 'Level'], ['Fases', 'Opmerkingen'])

method_levels = {tarsp: [uiting, 'Sz', 'Zc', 'Wg', 'VVW', sasta_opm, opmerkingen],
                 asta: [uiting, 'SampleGrootte', 'MLU', 'Taalmaat', 'foutenanalyse', 'lemma', sasta_opm, opmerkingen],

                 stap: [uiting, 'complexiteit', 'grammaticale fout', sasta_opm, opmerkingen]
                 }
method_header_pairs = {tarsp: default_header_pair, asta: default_header_pair, stap: default_header_pair}

@dataclass
class AnnotatedUtterance:
    uttid: UttId
    tokens: List[str]
    levels: Dict[str, list]
    stages: Dict[str, set]

    def torows(self, maxtokens: int, method: Method) -> Table:
        table  = []
        lhead = len(method_header_pairs[method.name][0])
        ltail = len(method_header_pairs[method.name][1])
        for level in method_levels[method.name]:
            stages = self.stages[level]
            therow = [self.uttid, get_level_label(level, method)]
            for lst in self.levels[level]:
                newrowel = comma.join(lst)
                therow.append(newrowel)
            ltherow = len(therow)
            restrow = ['' for i in range(maxtokens+lhead+1-ltherow)]
            therow.extend(restrow)

            stages_list = list(stages)
            sorted_stages_list = sorted(stages_list)
            sorted_stages_str_list = [str(i) for i in sorted_stages_list]
            stage_el = comma.join(sorted_stages_str_list)
            therow.append(stage_el)
            remark_el = ''
            therow.append(remark_el)
            table.append(therow)
        return table

def mk_header(maxtokens: int, method: Method) -> List[str]:
    words_header = ['Hele uiting'] + [f'Word{str(i+1)}' for i in range(maxtokens)]
    header = method_header_pairs[method.name][0] + words_header + method_header_pairs[method.name][1]
    return header


def exact2annotated_utterance(uttid: UttId, tokens: List[str], exact: dict, method:Method) -> AnnotatedUtterance:
    ltokens = len(tokens)
    levels = {level:  [[] for _ in range(ltokens + 1)] for level in method_levels[method.name]}
    stages = {level: set() for level in method_levels[method.name]}
    uttlevel = method_levels[method.name][0]
    for i, token in enumerate(tokens):
        curlist = levels[uttlevel][i+1]
        curlist.append(token)
    for el in exact:
        reskey = el[0]
        position = el[1]
        qid = reskey[0]
        if method.queries[qid].inform != 'no':
            thelevel = method.queries[qid].level
            thestage = method.queries[qid].fase if method.queries[qid].fase != '' else 0
            val = reskey[1]
            theitem = method.queries[qid].item if val == qid else val
            if thelevel in levels:
                if  len(levels[thelevel]) > position:
                    levels[thelevel][position].append(theitem)
                else:
                    settings.LOGGER.error(f'{position} not in {thelevel} for {theitem} in {uttid}: {str(tokens)}; {str(levels[thelevel])}')
            if thestage != 0 and thelevel in stages:
                stages[thelevel].add(thestage)
    result = AnnotatedUtterance(uttid=uttid, tokens=tokens, levels=levels, stages=stages)
    return result


def get_saf2_headed_table(allresults: AllResults, method: Method) -> HeadedTable:
    annotated_utterances = []
    exactbyutt = getexactbyutt(allresults.exactresults)

    sorted_uttids = sorted(exactbyutt.keys(), key=lambda x: int(x))
    analysed_trees_dict = {el[0]:el[1] for el in allresults.analysedtrees}

    max_tokens = 0
    for uttid in sorted_uttids:
        thetree = analysed_trees_dict[uttid]
        # get the origutts or else the sentence
        origutt = getorigutt(thetree)
        if origutt is None:
            origutt = getsentence(thetree)
        tok_meta_str = find1(thetree, tokenisation_xpath)
        if tok_meta_str is None:
            print(f'No tokenisation found for xsid={uttid}')
            continue
        tok_meta = eval(tok_meta_str)
        new_tok = retokenize(tok_meta)
        max_tokens = max(max_tokens, len(new_tok))

        annotated_utterance = exact2annotated_utterance(uttid, new_tok, exactbyutt[uttid], method)
        annotated_utterances.append(annotated_utterance)

    table = []
    for annotated_utterance in annotated_utterances:
        rows = annotated_utterance.torows(max_tokens, method)
        table.extend(rows)

    header = mk_header(max_tokens, method)

    return header, table


def mk_saf2_wb(outfullname, header, table):
    workbook = xlsxwriter.Workbook(outfullname)
    bold = workbook.add_format({'bold': True})
    white_blue_bg = workbook.add_format({'bg_color': '#00008B', 'font_color': 'white' })

    worksheet1 = workbook.add_worksheet('annotations')

    # worksheet1
    worksheet1.freeze_panes(1, 2)


    rowctr = 0
    xlsx_writerow(worksheet1, rowctr, header, format=bold)
    rowctr += 1

    for row in table:
        if row[levelcol] in utt_labels:
            theformat = white_blue_bg
        else:
            theformat = None
        xlsx_writerow(worksheet1, rowctr, row, format=theformat)
        rowctr += 1

    worksheet1.autofit()


    worksheet2 = workbook.add_worksheet('errors')
    return workbook

level_label_dict = {stap: {'complexiteit': 'Complexiteit', 'grammaticale fout': 'Grammaticale fout'},
                    asta: {'SampleGrootte': 'Samplegrootte', 'foutenanalyse': 'Foutenanalyse'}}

def get_level_label(level: str, method: Method) -> str:
    if method.name in level_label_dict and level in level_label_dict[method.name]:
        result = level_label_dict[method.name][level]
    else:
        result = level
    return result



