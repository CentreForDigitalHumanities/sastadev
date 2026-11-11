from sastadev.celexlexicon import dmwdict
from sastadev.basicreplacements import basicreplacements
from sastadev.corrector import enexceptions
from sastadev.stringfunctions import endsinschwa, monosyllabic
from sastadev.lexicon import informlexicon, getwordinfo, WordInfo
from typing import List

def wrongword(word: str) -> bool:
    word_infos = getwordinfo(word)
    result1 = any([wi[0] == 'ww' and wi[2] == 've' for wi in word_infos])   # aaide   aaiden
    result = result1
    return result

def okword(word: str) -> bool:
    word_infos = getwordinfo(word)
    result1 = any([wi[0] == 'n' for wi in word_infos])
    result2 = any([wi[0] == 'adj' for wi in word_infos])
    result = result2
    return result

def main():
    results = []
    for word in dmwdict:
        if word not in basicreplacements and word not in enexceptions and \
                endsinschwa(word) and not monosyllabic(word):
            if okword(word):
                n_word = f'{word}n'
                if informlexicon(n_word):
                    n_word_info = getwordinfo(n_word)
                    if any([wi[0] == 'ww' for wi in n_word_info]):
                        word_info = getwordinfo(word)
                        results.append((word, word_info, n_word, n_word_info))
    junk = 0
    for w, wi, nw, nwi in results:
        # print(f'{w}\t{nw}\t{wi}\t{nwi}')
        print(f'{w}\t{nw}')

if __name__ == '__main__':
    main()