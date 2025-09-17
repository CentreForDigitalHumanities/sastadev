from sastadev.stringfunctions import isconsonant, isdiphthong, istriphthong, isvowel, normalise_word, \
    wordfinalalrepeatedconsonantsre
import re

# maybe this module is not necessary for  blauwe -> blauw because we can simply take the lemma form

testlist = [('blauwe', 'e', 'blauw'), ('rode', 'e', 'rood'), ('dikke', 'e', 'dik'), ('weeë', 'e', 'wee'),
            ('blije', 'e', 'blij'), ('grijze', 'e', 'grijs')]

def dropvowelsuffix(wrd: str, suffix: str) -> str:
    """
    Removes the suffix from wrd if the word ends in the suffix and adjusts the remainin stem in accordance with
    Dutch spelling rules

    unfinished!!
    :param wrd:
    :param suffix:
    :return:
    """
    result = wrd
    if suffix == '':
        return result
    normalised_suffix = normalise_word(wrd[-len(suffix):])
    if  normalised_suffix != suffix:   # normalise_word  because of weeë , e -? wee; zeeën, en -> zee
        return result
    stem = wrd[:-len(suffix)]
    newstem = stem
    if isvowel(suffix[0]):
        if isconsonant(newstem[-1]):
            # zaaiden _> blauwe
            if istriphthong(newstem[-4:-1]):
                pass
            #  blauwe, e -> blauw
            elif isdiphthong(newstem[-3:-1]):
                pass
            # rode, e -> rood
            elif newstem[-2] in 'aeou' and isconsonant(newstem[-3]):
                newstem = re.sub(r'([aeou])(.)$', r'\1\1\2', newstem)
            else:
                # dikke
                # repeated consonants at the end reduce to a single consonant
                newstem = wordfinalalrepeatedconsonantsre.sub(r'\1', newstem)
        elif isvowel(newstem[-1]):
            pass

    result = newstem
    return result


def tryme():
    for word, suffix, correct_stem  in testlist:
        predicted_stem = dropvowelsuffix(word, suffix)
        if predicted_stem == correct_stem:
            print(f'OK: {word} - {suffix}: {predicted_stem} = {correct_stem}')
        else:
            print(f'NO: {word} - {suffix}: {predicted_stem}  != {correct_stem}')


if __name__ == '__main__':
    tryme()