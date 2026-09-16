from typing import List

from sastadev.conf import settings
from sastadev.metadata import defaultpenalty
from sastadev.sastatoken import Token
from sastadev.sastatypes import SynTree
from sastadev.smallclauses import mkinsertmeta, realword, word
from sastadev.tblex import isalpinonouncompound
from sastadev.tokenmd import TokenListMD
from sastadev.treebankfunctions import  getattval, getnodeyield, isdet,  mktoken2nodemap

gav = getattval
lonelytoestr = 'Lonely toe'
een_beetje = 'lonely beetje'



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

    prevtoken = None
    for i, token in enumerate(tokens):
        naarfound = naarfound or token.word == 'naar'
        if not naarfound:
            if i + 2 < len(tokens) and tokens[i].pos in token2nodemap and \
                    tokens[i+1].pos in token2nodemap and \
                    tokens[i+2].word == 'toe':
                thisnode = token2nodemap[token.pos]
                nextnode = token2nodemap[tokens[i+1].pos]
                if isdet(thisnode) and getattval(nextnode, 'pt') == 'n':
                    naartoken = Token('naar', token.pos, subpos=5)
                    inserttokens = [naartoken]
                    metadata += mkinsertmeta(inserttokens, newtokens, cat=lonelytoestr)
                    naarfound = True
                    newtokens.append(naartoken)
                    insertiondone = True
            elif i +1 < len(tokens) and tokens[i].pos in token2nodemap and \
                    tokens[i+1].word == 'toe':
                thisnode = token2nodemap[token.pos]
                if isnominal(thisnode) :
                    if prevtoken is None:
                        prevtokenpos = 0
                    else:
                        prevtokenpos = prevtoken.pos
                    naartoken = Token('naar', prevtokenpos, subpos=5)
                    naarfound = True
                    newtokens.append(naartoken)
                    inserttokens = [naartoken]
                    metadata += mkinsertmeta(inserttokens, newtokens, cat=lonelytoe)
                    insertiondone = True
        newtokens.append(token)
        prevtoken = token
    if insertiondone:
        result = [TokenListMD(newtokens, metadata)]
    else:
        result = []
    return result



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



def beetje(tokensmd: TokenListMD, tree: SynTree) -> List[TokenListMD]:

    insertion_done = False
    leaves = getnodeyield(tree)
    reducedleaves = [leave for leave in leaves if realword(leave)]
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
    for i, token in enumerate(tokens):
        insert_position = None
        prevtoken = tokens[i-1] if i > 0 else None
        prevprevtoken = tokens[i - 2] if i > 1 else None
        if token.word == 'beetje':
            if prevtoken is not None and not prevtoken.skip:
                prevtoken_node = token2nodemap[prevtoken.pos] if prevtoken.pos in token2nodemap else None
                prevtoken_pt = gav(prevtoken_node, 'pt')
                if prevtoken_pt == 'adj':
                    art_token = prevprevtoken
                else:
                    art_token = prevtoken
                if art_token is not None:
                    art_token_node = token2nodemap[art_token.pos] if art_token.pos in token2nodemap else None
                    art_token_lemma = gav(art_token_node, 'lemma')
                    if art_token_lemma != 'een':
                        insert_position = art_token.pos if art_token is not None else 0
                else:
                    insert_position =  0
            else:
                insert_position = 0
            if insert_position is not None:
                een_token = Token('een', insert_position, subpos=5)
                insert_tokens = [een_token]
                metadata += mkinsertmeta(insert_tokens, newtokens, cat=een_beetje, penalty=-defaultpenalty)
                newtokens.append(een_token)
                insertion_done = True
        newtokens.append(token)
    sorted_newtokens = sorted(newtokens, key=lambda x: x.pos+x.subpos)
    result = [TokenListMD(sorted_newtokens, metadata)] if insertion_done else []
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

def x_isnominal(node: SynTree) -> bool:
    """
    checks whether node is nominal;
    when node is a bare index node, it checks whether the antecedent of node s nominal
    """
    if 'word' in node.attrib or 'cat' in node.attrib:
        return isnominal(node)
    else:
        antecedent = getantecedentof(node)
        return isnominal(antecedent)

nominal_cats = ['np']
def is_nominal_phrase(node: SynTree) -> bool:
    cat = gav(node, 'cat')
    if cat in nominal_cats:
        return True
    elif cat == 'mwu':
        # het duurst
        nodeyield = getnodeyield(node)
        sorted_children = sorted(nodeyield, key=lambda n: int(gav(n, 'begin')))
        child1 = sorted_children[0]
        child2 = sorted_children[1]
        child1_is_het = gav(child1, 'pt') == 'lid' and gav(child1, 'lemma') == 'het'
        child2_is_adj = gav(child2, 'pt') == 'adj'
        if len(node) == 2 and child1_is_het and child2_is_adj:
            return True
        elif gav(child1, 'pt') == 'vz':
            return False
        elif any([gav(child, 'pt') == 'n' and gav(child, 'ntype')== 'eigen' for child in node]):
            return True
        # we must cover more cases such as 3 januari
        else:
            return False
    else:
        return False

def x_is_nominal_phrase(node: SynTree) -> bool:
    """
    checks whether node is a nominal phrase;
    when node is a bare index node, it checks whether the antecedent of node s nominal
    """
    if 'word' in node.attrib:
       return False
    elif 'cat' in node.attrib:
       return is_nominal_phrase(node)
    else:
        antecedent = getantecedentof(node)
        return is_nominal_phrase(antecedent)


def getantecedentof(stree: SynTree):
    idx = getattval(stree, 'index')
    antecedentxpath = f'./ancestor::alpino_ds/descendant::node[(@word or @cat) and @index="{idx}"]'
    antecedents = stree.xpath(antecedentxpath)
    if antecedents != []:
        antecedent = antecedents[0]
    else:
        antecedent = None
    return antecedent

def x_gav(node: SynTree, att: str) -> str:
    """
    looks up the value of att in node, and
    when node is a bare index node, it looks the value of att up in the antecedent of node
    """
    if 'word' in node.attrib or 'cat' in node.attrib:
        return gav(node, att)
    else:
        antecedent = getantecedentof(node)
        return gav(antecedent, att)
