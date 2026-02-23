"""
This module is intended for an adaptation of auchann output in which words of false starts are marked wit the prefix 1
"""
from dataclasses import dataclass
import editdistance
import itertools
import re
from sastadev.basicreplacements import basicreplacements
from sastadev.xlsx import getxlsxdata
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class WordPos:
    word: str
    pos: int

    def __str__(self):
        return f"{self.pos}:{self.word}"


@dataclass(frozen=True)
class AlignedWords:
    utt_wordpos: Optional[WordPos]
    expl_wordpos: Optional[WordPos]


Alignment = List[AlignedWords]

included_prefix = '1'
space = ' '
ellipsis = '...'

diffthreshold = 0.45
minlength = 4
basicreplacement_reldistance = 0.0005   # larger than 0.0 becuase full identity should be preferred
max_reldistance = 1.0

# valid replacements not included in basicreplacements because Alpino takes care of it
alpino_replacements = {'dees': 'deze', 'ie': 'hij'}


simple_false_start_pattern = r'\b(\w+)(\s*)(\[//\])'

scoped_false_start_pattern = r'(<[^>]+>)\s*\[//\]'

def red(word1, word2) -> float:
    distance = editdistance.distance(word1, word2)
    result = distance / (max(len(word1), len(word2) ))
    return result

def false_start_to_prefix(auchannstr: str) -> str:
    result = auchannstr
    result = re.sub(simple_false_start_pattern, rf'{included_prefix}\1\2' , result)

    result = scoped_false_start_to_prefix(result)


    return result

def clean_spaces(instr:str) -> str:
    words = instr.split()
    result = space.join(words)
    return result

def scoped_false_start_to_prefix(auchannstr: str) -> str:
    firstmatch = re.search(scoped_false_start_pattern, auchannstr)
    if firstmatch is None:
        return auchannstr
    else:
        replacement = get_replacement(firstmatch.group(1))
        raw_resultstr = auchannstr[:firstmatch.start()] + replacement + scoped_false_start_to_prefix(auchannstr[firstmatch.end():])
        resultstr = clean_spaces(raw_resultstr)
        return resultstr

def get_replacement(instr: str) -> str:
    purestr = instr[1:-1]
    word_list = purestr.split(space)
    out_word_list = [f'{included_prefix}{word}' for word in word_list]
    result = f'{space}{space.join(out_word_list)}{space}'
    return result


## has order diff make list ((token1, pos1), (token2,pos2)) for 'precedes' as a counter for utt and explanation
# check whether the intersection contains a < b in one and b < a in the other

# ook ik ADD hebt / ik heb ook ADD
# (ook, ik), (ook ADD), (ook, hebt), (ik, ADD), (ik hebt), (ADD, hebt)
# (ik, heb), (ik, ook), (ik, ADD), (heb, ook), (heb, ADD). (ook, ADD)
# exact matches: ook, ik, ADD; approcimative match: heb/hebt
#  reversal = (ook, ik) v. (ik, ook); (ADD, hebt) v. (heb, ADD)

def make_alignment(wordposlist1, wordposlist2) -> Alignment:
    the_alignment = []
    expl_positions_covered = []
    for (word1, pos1) in wordposlist1:
        uttwordpos = WordPos(word1, pos1)
        matches = [(word2, pos2, smart_reldistance(word1, word2)) for word2, pos2 in wordposlist2 ]
        if matches != {}:
            # choose the one with the lowest relative distance and if equal the closest one
            thematch = min(matches, key=lambda match:(match[2], abs(match[1] - pos1)))
            explwordpos = WordPos(thematch[0], thematch[1])
            the_aligned_words = AlignedWords(uttwordpos, explwordpos)
            the_alignment.append(the_aligned_words)
            expl_positions_covered.append(thematch[1])
        else:
            the_aligned_words = AlignedWords(uttwordpos, None)
            the_alignment.append(the_aligned_words)

    for word2, pos2 in wordposlist2:
        if pos2 not in expl_positions_covered:
            wordpos2 = WordPos(word2, pos2)
            the_aligned_words = AlignedWords(None, wordpos2)
            the_alignment.append(the_aligned_words)


    return the_alignment




def reldistance(utt1: str, utt2:str) -> float:
    maxlen = max(len(utt1), len(utt2))
    ed = editdistance.distance(utt1, utt2)
    reled = ed / maxlen
    return reled


def smart_reldistance(uttword, explword) -> float:
    if uttword == explword:
        return 0.0
    elif explword in [el[0] for el in  basicreplacements[uttword]]:
        return basicreplacement_reldistance
    elif uttword in alpino_replacements and explword in alpino_replacements[uttword]:
        return basicreplacement_reldistance
    else:
        red = reldistance(explword, uttword)
        if max(len(uttword), len(explword)) >= minlength:
            return red
        else:
            return max_reldistance

def inverted(aligned_words1: AlignedWords, aligned_words2: AlignedWords) -> bool:
    if aligned_words1.utt_wordpos is None or aligned_words2.utt_wordpos is None:
        return False
    if aligned_words1.expl_wordpos is None or aligned_words2.expl_wordpos is None:
        return False
    case1 = (aligned_words1.utt_wordpos.pos > aligned_words2.utt_wordpos.pos and
             aligned_words1.expl_wordpos.pos < aligned_words2.expl_wordpos.pos)
    case2 = (aligned_words1.utt_wordpos.pos < aligned_words2.utt_wordpos.pos and
             aligned_words1.expl_wordpos.pos > aligned_words2.expl_wordpos.pos)
    result = case1 or case2
    return result

def has_inversion(uttwordposlist:List[WordPos], explwordposlist: List[WordPos]) -> Tuple[bool, str]:
    the_alignment = make_alignment(uttwordposlist, explwordposlist)
    combinations = itertools.combinations(the_alignment, 2)
    inverted_combinations = [(a, b) for  (a, b) in combinations if inverted(a,b) ]
    result = inverted_combinations != []
    if result:
        explanation = get_explanation(inverted_combinations)
    else:
        explanation = ''
    return result, explanation

def get_explanation(inverted_combinations:List[Tuple[WordPos, WordPos]]) -> str:
    explanation_list = []
    for alignedwords1, alignedwords2 in inverted_combinations:
        list1 = [alignedwords1.utt_wordpos, alignedwords2.utt_wordpos]
        sorted_list1 = sorted(list1, key=lambda utt_wordpos: utt_wordpos.pos)
        sorted_wordlist1 = [el.word for el in sorted_list1]
        list2 = [alignedwords1.expl_wordpos, alignedwords2.expl_wordpos]
        sorted_list2 = sorted(list2, key=lambda expl_wordpos: expl_wordpos.pos)
        sorted_wordlist2 = [el.word for el in sorted_list2]
        explanation = ellipsis.join(sorted_wordlist1) + ' v. ' + ellipsis.join(sorted_wordlist2)
        explanation_list.append(explanation)

    result = '\n'.join(explanation_list)
    return result


utt_expl_pairs = [('ook ik ADD hebt', 'ik heb ook ADD'),
                  ('Arjan heeft luiers', 'luiers heeft Arjan gekocht'),
                  ('ik dacht gisteren dat ik ziek was', 'gisteren dacht ik dat ik ziek was'),
                  ("is dit 'n David boekje ?",  "is dit 'n boekje voor David ?"),
                  ("is ie ziek ?", "is hij ziek ?"),]

inputstrings = ['0ik 0heb ook ik [//] ADD hebt [//]',
                'ik <heb echt> [//] iets 0hebt 0echte nodig'
                ]

def test():
    for instr in inputstrings:
        result = false_start_to_prefix(instr)
        print(instr)
        print(result)
        print('---------')


def test2():
    for utt, expl in utt_expl_pairs:
        utt_list = utt.split()
        expl_list = expl.split()
        utt_pos_list = [(w, i) for i, w in enumerate(utt_list)]
        expl_pos_list = [(w,i) for i,w in enumerate(expl_list)]

        the_alignment = make_alignment(utt_pos_list, expl_pos_list)
        for aligned_words in the_alignment:
            print(f'{aligned_words.utt_wordpos} <-> {aligned_words.expl_wordpos}')

        with_inversion, explanation = has_inversion(utt_pos_list, expl_pos_list)
        print(f'inversion: {with_inversion}')
        print(f'explanation: {explanation}')

def test3():
    infullname = r"D:\Dropbox\jodijk\Utrecht\Projects\AuCHann\TD_DLD_gold Current.xlsx"
    header, data = getxlsxdata(infullname, sheetname='Sheet1')
    okcount = 0
    allcount = 0
    for row in data:
        allcount +=1
        utt = row[2]
        expl = row[3]
        inv = row[5]




if __name__ == "__main__":
    # test()
    test2()