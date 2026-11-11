from lxml import etree
from sastadev.filefunctions import get_corrected_tree_fullname
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getorigutt, getattval as gav, showtree, simpleshow

def test_f(triples, f):
    for triple in triples:
        infullname = get_corrected_tree_fullname(triple[0], triple[1], triple[2])
        stree = get_stree(infullname)
        origutt = getorigutt(stree)
        results = f(stree)
        print(f'{origutt}: {str([gav(result, 'word') for result in results])}')

        junk = 0

def test_transform_f(triples, f):
    for triple in triples:
        infullname = get_corrected_tree_fullname(triple[0], triple[1], triple[2])
        stree = get_stree(infullname)
        origutt = getorigutt(stree)
        result = f(stree)
        print('original tree:')
        simpleshow(stree, )
        print('*****')
        print('transformed tree')
        simpleshow(result)

        junk = 0

def get_stree(infullname: str) -> SynTree:
    fulltree = etree.parse(infullname)
    stree = fulltree.getroot()
    return stree
