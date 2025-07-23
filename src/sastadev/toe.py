from typing import List

from sastadev.alpino import getdehetwordinfo
from sastadev.conf import settings
from sastadev.lexicon import isalpinonouncompound
from sastadev.sastatoken import Token
from sastadev.sastatypes import SynTree
from sastadev.smallclauses import bg, mkinsertmeta, realword, word
from sastadev.tokenmd import TokenListMD
from sastadev.treebankfunctions import getattval, getnodeyield, mktoken2nodemap

lonelytoe = 'Lonely toe'

def isdet(node) -> bool:
    nodept = getattval(node, 'pt')
    nodepdtype = getattval(node, 'pdtype' )
    result = nodept in ['lw'] or (nodept in  ['vnw'] and nodepdtype in ['det'])
    return result


def contentword(node) -> bool:
    nodept = getattval(node, 'pt')
    result = nodept in ['n', 'ww', 'adj', 'bw']
    return result


def lonelytoe(tokensmd: TokenListMD, tree: SynTree) -> List[TokenListMD]:

    insertiondone = False
    leaves = getnodeyield(tree)
    reducedleaves = [leave for leave in leaves if realword(leave)]
    if not len(reducedleaves) > 1:
        return []
    tokens = tokensmd.tokens
    treewords = [word(tokennode) for tokennode in leaves]
    tokenwords = [token.word for token in tokens if not token.skip]
    if treewords != tokenwords:
        settings.LOGGER.warning(
            'Token mismatch: {} v. {}'.format(treewords, tokenwords))
        return []
    token2nodemap = mktoken2nodemap(tokens, tree)
    metadata = tokensmd.metadata

    newtokens = []
    naarfound = False

    for i, token in enumerate(tokens):
        naarfound = naarfound or token.word == 'naar'
        if not naarfound:
            if  i + 2 < len(tokens) and tokens[i].pos in token2nodemap and \
                    tokens[i+1].pos in token2nodemap and \
                    tokens[i+2].word == 'toe':
                thisnode = token2nodemap[token.pos]
                nextnode = token2nodemap[tokens[i+1].pos]
                if isdet(thisnode) and getattval(nextnode, 'pt') == 'n':
                    naartoken = Token('naar', token.pos, subpos=5)
                    inserttokens = [naartoken]
                    metadata += mkinsertmeta(inserttokens, newtokens, cat=lonelytoe)
                    naarfound = True
                    newtokens.append(naartoken)
                    insertiondone = True
            elif i +1 < len(tokens) and tokens[i].pos in token2nodemap and \
                    tokens[i+1].word == 'toe':
                thisnode = token2nodemap[token.pos]
                if isnominal(thisnode) :
                    naartoken = Token('naar', token.pos, subpos=5)
                    naarfound = True
                    newtokens.append(naartoken)
                    inserttokens = [naartoken]
                    metadata += mkinsertmeta(inserttokens, newtokens, cat=lonelytoe)
                    insertiondone = True
        newtokens.append(token)
    if insertiondone:
        result = [TokenListMD(newtokens, metadata)]
    else:
        result = [tokensmd]
    return result

nominalpts = ['n', 'vnw']
def isnominal(node: SynTree) -> bool:
    pt = getattval(node, 'pt' )
    wrd = getattval(node, 'word')
    if pt in nominalpts:
        return True
    elif isalpinonouncompound(wrd):
        return True
    else:
        return False



# def isvariantcompatible(variant: str, variants:str) -> bool:
#     rawvariantlist = variants.split(comma)
#     variantlist = [variant.strip() for variant in rawvariantlist]
#     result = variantlist == [] or variant in variantlist
#     return result
#
# import copy
# def transformtree(stree:SynTree) -> SynTree:
#     newstree = copy.deepcopy(stree)
#     ldxpath = """.//node[node[@rel="hd" and @pt="ww"] and
#        node[@rel="ld" and (@pt="n" or @cat="np")] and
#        node[@rel="svp"  and @pt="vz"] and
#        not(node[@rel="su"])
#        ]"""
#     ldclauses = stree.xpath(ldxpath)
#     for ldclause in ldclauses:
#         ldnode = ldclause.xpath(' node[@rel="ld" and (@pt="n" or @cat="np")]')
#         ldnode.attrib["rel"] = "su"
#     return newstree