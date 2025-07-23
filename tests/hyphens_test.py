from sastadev.lexicon import informlexicon
from sastadev.stringfunctions import accentaigu, delhyphenprefix


def test():

    assert accentaigu('aap') == ['aap', 'aáp', 'áap', 'ááp']
    assert delhyphenprefix('anti-bom', informlexicon) == []
    assert delhyphenprefix('ex-vrouw', informlexicon) == []
    assert delhyphenprefix('sergeant-majoor', informlexicon) == []
    assert delhyphenprefix('ver-verkoop', informlexicon) == ['verkoop']
    assert delhyphenprefix('vver-verkoop', informlexicon) == ['verkoop']
    assert delhyphenprefix('vvver-verkoop', informlexicon) == ['verkoop']


if __name__ == '__main__':
    test()
