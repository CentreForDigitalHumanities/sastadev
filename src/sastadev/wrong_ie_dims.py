"""
module to deal with incorrectly formed ie-diminutives such as wielties, boomie, etc.
"""
import re
from sastadev.iedims import getbase
from sastadev.lexicon import known_word
from sastadev.stringfunctions import vowels
from typing import Optional
# bcdfghjklmnpqrstvwxz

ltiepattern = r'([lr]t)i(es?)$'    # wieltie, wielties, keertie, keerties
vvmiepattern = fr'([{vowels}][{vowels}]m)i(es?)$'  # boomie boomies
vvliepattern = fr'([{vowels}][{vowels}][lrn])i(es?)$' # wielie, wielies, keerie, keeries, maanie, maanies


# to addd krokodillie, mandarijnie

def get_je_from_wrong_ie_dim(wrd: str) -> Optional[str]:
    new_wrd = wrd
    new_wrd = re.sub(ltiepattern, r'\1j\2', new_wrd)
    # new_wrd = re.sub(vvmiepattern, r'\1pj\2', new_wrd)  # should probably not be done boomie is not marked as verkl
    new_wrd = re.sub(vvliepattern, r'\1tj\2', new_wrd)

    if new_wrd == wrd:
        return None
    else:
        lemmas = []
        candpairs = []
        lemmas += getbase(new_wrd)
        for lemma in lemmas:
            candpairs.append((new_wrd, lemma))
        results = []
        if any([known_word(lemma) for _, lemma in candpairs]):
            return new_wrd


test_pairs = [('wieltie', 'wieltje'), ('wielties', 'wieltjes'), ('keertie', 'keertje'), ('keertie', 'keertje'),
              ('boomie', 'boompje'), ('boomies', 'boompjes'), ('wielie', 'wieltje'), ('wielies', 'wieltjes')]

def tryme():
    verbose = True
    for wrd, correct_wrd in test_pairs:
        new_wrd = get_je_from_wrong_ie_dim(wrd)
        if new_wrd == correct_wrd:
            if verbose:
                print(f'OK: {wrd}: {new_wrd} = {correct_wrd}')
        else:
            print(f'NO: {wrd}: {new_wrd} != {correct_wrd}')


if __name__ == '__main__':
    tryme()