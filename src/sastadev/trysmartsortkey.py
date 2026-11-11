from sastadev.stringfunctions import smartsortkey, SmartSortKey

testpairs =[('aan', ('aan',)),
            ('dld03', ('dld', '03')),
            ('auristrain_dld14_23', ('auristrain_dld', '14', '_', '23')),
            ('auristrain_dld14_9', ('auristrain_dld', '14', '_', '9')),
            ('29a', ('29', 'a')),
            ('29b', ('29', 'b')),
           ]

def tryme():
    errorfound = False
    for wrd,tpl in testpairs:
        smartkey = smartsortkey(wrd)
        if smartkey.tpl != tpl:
            print(f'NO:{smartkey} != {tpl} (input: {wrd}')
            errorfound = True
    sortedwrds = sorted([wrd for wrd, _ in testpairs], key=lambda x: smartsortkey(x))
    print(f'Sorted:')
    for wrd in sortedwrds:
        print(wrd)
    if errorfound:
        raise AssertionError

if __name__ == '__main__':
    tryme()