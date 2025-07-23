from sastadev.lexicon import informlexiconpos, issuperadjective


def test_super_adjective():
    """
    Test the issuperadjective function from the sastadev.lexicon module.
    This function checks if a word is a super adjective based on its POS tag.
    """
    # Test cases for super adjectives
    test_cases = [
        ('superhard', True),
        ('superlang', True),
        ('superman', False),
        ('supermarkt', False)
    ]

    for word, expected in test_cases:
        result = issuperadjective(word)
        assert result == expected, f'Error: {word} expected {expected}, got {result}'
