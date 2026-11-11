from sastadev.deregularise import remove_ge, correctinflection



testset = [('gevastgeplakt', 'vastgeplakt'), ('geöpgegeten', "opgegeten"), ('ge-opgegeten', "opgegeten"),
           ('vastgeplakt', 'vastgeplakt')]


testset2 = [('gevastgeplakken', 'vastgeplakt'), ('geüitgekijkt', 'uitgekeken')]


def report(wrongword, result, okword, verbose=False):
    if result == okword:
        if verbose:
            print(f'OK: {wrongword}: {result} = {okword}')
    else:
        print(f'NO: {wrongword}: {result} != {okword}')


def test1():
    verbose = True
    for wrongword, okword in testset:
        result = remove_ge(wrongword)
        report(wrongword, result, okword, verbose=verbose)

def test2():
    verbose = True
    for wrongword, okword in testset2:
        result_metas = correctinflection(wrongword)
        for result, meat in result_metas:
            report(wrongword, result, okword, verbose=verbose)




if __name__ == '__main__':
    # test1()
    test2()
