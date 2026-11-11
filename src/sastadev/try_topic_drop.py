from sastadev.filefunctions import get_corrected_tree_fullname
from sastadev.treebankfunctions import getattval, getorigutt, getsentence, getstree
from sastadev.queryfunctions import topic_drop

gav = getattval

ok_test_triples = [('vklstap', 'stap_08', '36'),
                   ('vklstap', 'stap_09', '18'),
                   ('vklstap', 'stap_08', '18'),
                   ('vklstapfase2', 'kind1', '17'),
                   ('vklstapfase2', 'kind1', '37'),
                   ('vklstapfase2', 'STP_3', '11'),
                   ('vklstapfase2', 'STP_Du', '4'),
                   ('vklstapfase2', 'STP_Du', '34'),
                   ('vklstapfase2', 'STP_Ko', '40'),
                   ]

no_test_triples = [('vklstap', 'stap_08', '16'),
                   ('vklstapfase2', 'stap_024', '12'),
                   ('vklstapfase2', 'STAP_024', '37'),
                   ('vklstapfase2', 'STP_KC', '11')

                   ]

ok_test_tuples = [(tr, True) for tr in ok_test_triples]
no_test_tuples = [(tr, False) for tr in no_test_triples]

all_test_tuples = ok_test_tuples + no_test_tuples

def main():
    # all_test_tuples = [(  ('vklstapfase2', 'STP_Ko', '40'), True)]
    for tr, ref in all_test_tuples:
        ds, sample, uttid = tr
        fullname = get_corrected_tree_fullname(ds, sample, uttid)
        full_stree = getstree(fullname)
        if full_stree is None:
            print(f'No tree foud for {ds}, {sample}, {uttid}: {fullname}')
            continue
        stree = full_stree.getroot()
        results = topic_drop(stree)
        sentence = getsentence(stree)
        origutt = getorigutt(stree)
        if results != [] and ref:
            print(f'OK: {ds}-{sample}-{uttid}: is correctly identified as topic_drop: {gav(results[0], 'word')} in {sentence} from {origutt}.')
        elif results == [] and not ref:
                print(f'OK: {ds}-{sample}-{uttid}: is correctly not identified as topic_drop: {sentence} from {origutt}.')
        elif results == [] and ref:
            print(f'NO: {ds}-{sample}-{uttid}: is incorrectly not identified as topic_drop: {sentence} from {origutt}.')
        elif results != [] and not ref:
            print(f'NO: {ds}-{sample}-{uttid}: is incorrectly identified as topic_drop: {gav(results[0], 'word')} in {sentence} from {origutt}.')


if __name__ == '__main__':
    main()