"""
module with a function to show a syntactc=ic tree properly

"""
from lxml import etree
from sastadev.filefunctions import get_corrected_tree_fullname
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getattval as gav

space = ' '

def displaytree(stree: SynTree, indent=0, step=4, details=False) -> str:
    resultstrings = []
    if stree.tag in ['meta', 'xmeta']:
        streestr = f'{stree.tag}-{stree.attrib["name"]}: {stree.attrib["value"]}'
    elif stree.tag == 'node':
        index = gav(stree, 'index')
        poscat = gav(stree, 'pt')
        if poscat == '':
            poscat = gav(stree, 'cat')
        if poscat == '':
            poscat = gav(stree, 'pos')
        if poscat == '':
            poscat= ''
        rel = gav(stree, 'rel')
        word = gav(stree, 'word')
        lemma = gav(stree, 'lemma')
        if 'word' in stree.attrib:
            postagstr = f':{gav(stree, 'postag')}' if details else ''
            indexstr = f'{index}:' if index != '' else ''
            streestr=f'{rel}/{indexstr}{poscat}-{word} ({lemma}){postagstr}'
        elif 'cat' in stree.attrib:
            indexstr = f'{index}:' if index != '' else ''
            streestr = f'{rel}/{indexstr}{poscat}'
        else:
            streestr = f'{rel}/{index}'
    elif stree.tag == 'sentence':
        streestr = f'{stree.tag}-{stree.text}'
    else:
        streestr = stree.tag
    indentedstreestr = f'\n{(indent * space)}{streestr}'
    resultstrings.append(indentedstreestr)
    for child in stree:
        childstrings = displaytree(child, indent=indent+step, step=step, details=details)
        resultstrings += childstrings
    return resultstrings

def printtree(stree: SynTree, indent=0, step=4, details=False, text='') -> None:
    resultstrings = displaytree(stree, indent, step, details)
    resultstring = ''.join(resultstrings)
    print(text)
    print(resultstring)

testtrees = [('vkltarsp', 'tarsp_13', '12')]

def main():
    for dataset, sample, uttid in testtrees:
       fullname = get_corrected_tree_fullname(dataset, sample, uttid)
       fulltree = etree.parse(fullname)
       tree = fulltree.getroot()
       printtree(tree, details=True)


if __name__ == '__main__':
    main()