from sastadev.corrector import gaatie


testset = [('kan-ie', 'kan ie'),
           ('wil-ie', 'wil ie'),
           ('moet-ie', 'moet ie'),
           ('gaat-ie', 'gaat ie'),
           ('moettie', 'moet ie'),
           ('gaatie', 'gaat ie')
           ]

def trygaatie():
    errorfound = False
    for wrd, corr in testset:
        results = gaatie(wrd)
        if results != [corr]:
            print(f'Error: {results} != [{corr}]')
            errorfound = True

    if errorfound:
        raise AssertionError

if __name__ == '__main__':
    trygaatie()