import copy
from typing import List, Tuple

space = ' '

uttstr = "ook ik ADD hebt"
explstr = "ik heb ook ADD"

utt = uttstr.split(space)
expl= explstr.split(space)


def find_best_alignment(utt: List[str], expl:List[str]) -> List[Tuple[str, str]]:
    # first align the words that are identical
    results = []
    curutt = copy.deepcopy(utt)
    curexpl = copy.deepcopy(expl)
    utt_tuples = [(i, wrd) for i, wrd in enumerate(utt)]
    expl_tuples = [(i, wrd) for i, wrd in enumerate(expl)]
    maybe_more_identical_words = True
    while maybe_more_identical_words:
        identical_found = False
        for i, tpl1 in enumerate(utt_tuples):
            for j, tpl2 in enumerate(expl_tuples):
                if tpl1[1]  == tpl2[1]:
                    results.append((tpl1, tpl2))
                    identical_found = True
                    utt_tuples.remove(tpl1)
                    expl_tuples.remove(tpl2)
                    break
            if identical_found:
                break

    strresults = []
    for (i,j) in results:
        strresults.append((utt[i], expl[j]))
    return strresults


if __name__ == '__main__':
    results = find_best_alignment(utt, expl)
    print(results)








