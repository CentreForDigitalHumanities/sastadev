from sastadev.lexicon import informlexicon, nochildword, validword


def test_lexicon():
    # word: expected result
    test_cases = [
        ('stukkies', False),
        ('jochie', True),
        ('gevalt', True),
        ('stukjes', True),
        ('gevallen', True),
        ('mouwe', False),
        ('mouwen', True),
        ('gaatie', False),
        ('gaat', True),
        ('ie', True),
    ]
    for word, expected in test_cases:
        assert informlexicon(
            word) == expected, f"informlexicon({word!r}) != {expected}"

    assert not validword('pele', 'tarsp')
    assert nochildword('pele')
