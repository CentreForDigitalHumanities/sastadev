from lxml import etree
from sastadev.lexicon import getwordposinfo, pvinfl2dcoi
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getattval as gav, nodecopy



past_node = etree.Element('node', attrib={'pt': 'ww', 'wvorm': 'pv', 'pvagr': 'met-t', 'pvtijd': 'tgw',
                                          'word': 'past', 'lemma': 'passen'})


testlist = [(past_node, 'pas')]

def get_backplacement(replacementnode: SynTree, originalword: str) -> SynTree:
    candidates = []
    replacement_pt = gav(replacementnode, 'pt')
    replacement_lemma = gav(replacementnode, 'lemma')
    wordinfos = getwordposinfo(originalword, replacement_pt)
    for wordinfo in wordinfos:
        pt, dehet, infl, lemma = wordinfo
        if lemma == replacement_lemma:
            candidates.append(wordinfo)
    if candidates == []:
        result = nodecopy(replacementnode)
        result.set('word', originalword)
        return result
    else:
        selected_wordinfo = candidates[0]
        # translate the inflection codes
        pt, dehet, infl, lemma = selected_wordinfo
        if pt == 'ww':   # (and infl a finite code)
            dcoituple = pvinfl2dcoi(originalword, infl, lemma)
            junk = 0
            # make a node with these properties


def tryme():
    for node, wrd in testlist:
        newnode = get_backplacement(node, wrd)
        junk = 0



if __name__ == '__main__':
    tryme()