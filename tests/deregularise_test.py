

from sastadev.deregularise import (correctinflection)

thelist = [('daan', 'gedaan'), ('vervald', 'vervallen'), ('opgevald', 'opgevallen'),
                        ('overvald', 'overvallen'), ('oververvald', 'oververvallen'), ('gevalt', 'gevallen'),
                        ('ebakt', 'gebakken'), ('sebakt', 'gebakken'), ('sebakte', 'gebakken'),
            ('slaapte', 'sliep'), ('geslaapt', 'geslapen'),
            ('sliepten', 'sliepen'), ('sliepte', 'sliep'),
            ('aaneengeloopt', 'aaneengelopen'),
            ('gekijken', 'gekeken'), ('gekeekt', 'gekeken'), ('uitgekijken', 'uitgekeken'),
            ('uitgekeekt', 'uitgekeken')

            ]

# @pytest.mark.skip(reason='test code does not work')
def test_deregularise():  # noqa: C901

    for wrong, good in thelist:
        cands = correctinflection(wrong)
        for cand, m in cands:
            print(f'({wrong}, {good}, {m})' )

            if cand != good:
                pass

        if cands == []:
            print('WRONG', wrong, '', good)
        for cand, m in cands:
            if cand != good:
                print('WRONG', wrong, cand, good, m)
                errorfound = True


if __name__ == '__main__':
    test_deregularise()