"""
module with a function to show a syntactc=ic tree properly

"""
from lxml import etree
from sastadev.filefunctions import get_corrected_tree_fullname
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getattval as gav

space = ' '

def displaytree(stree: SynTree, indent=0, step=4) -> str:
    resultstrings = []
    if stree.tag in ['meta', 'xmeta']:
        streestr = f'{stree.tag}-{stree.attrib["name"]}'
        indentedstreestr = f'\n{(indent * space)}{streestr}'
    elif stree.tag == 'node':
        poscat = gav(stree, 'pt')
        if poscat == '':
            poscat = gav(stree, 'cat')
        if poscat == '':
            poscat = gav(stree, 'pos')
        if poscat == '':
            poscat= '@@'
        rel = gav(stree, 'rel')
        word = gav(stree, 'word')
        lemma = gav(stree, 'lemma')
        streestr=f'{rel}/{poscat}-{word} ({lemma})' if 'word' in stree.attrib else f'{rel}/{poscat}'
        indentedstreestr = f'\n{(indent * space)}{streestr}'
    else:
        indentedstreestr = f'\n{(indent * space)}{stree.tag}'
    resultstrings.append(indentedstreestr)
    for child in stree:
        childstrings = displaytree(child, indent=indent+step, step=step)
        resultstrings += childstrings
    return resultstrings

testtrees = [('auristrain', 'dld03', '1')]

def main():
    for dataset, sample, uttid in testtrees:
       fullname = get_corrected_tree_fullname(dataset, sample, uttid)
       fulltree = etree.parse(fullname)
       tree = fulltree.getroot()
       resultstrings = displaytree(tree)
       resultstring = ''.join(resultstrings)
       print(resultstring)


if __name__ == '__main__':
    main()