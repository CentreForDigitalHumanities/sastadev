from sastadev.stringfunctions import smartsortkey


testpairs =[('aan', ('aan',)),
            ('dld03', ('dld', 3)),
            ('auristrain_dld14_23', ('auristrain_dld', 14, '_', 23)),
            ('auristrain_dld14_9', ('auristrain_dld', 14, '_', 9))
]

def tryme():
    errorfound = False
    for wrd,tpl in testpairs:
        smartkey = smartsortkey(wrd)
        if smartkey != tpl:
            print(f'NO:{smartkey} != {tpl} (input: {wrd}')
            errorfound = True
    sortedwrds = sorted([wrd for wrd, _ in testpairs], key=smartsortkey)
    print(f'Sorted:')
    for wrd in sortedwrds:
        print(wrd)
    if errorfound:
        raise AssertionError

if __name__ == '__main__':
    tryme()