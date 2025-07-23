"""
The module *tblex* contains functions that require functions
from the lexicon module and from the treebankfunctions module
"""

import sastadev.lexicon as lex
from sastadev.sastatypes import SynTree
from sastadev.sastatoken import Token
from sastadev.treebankfunctions import (all_lower_consonantsnode, getattval,
                                        is_duplicate_spec_noun, iscompound,
                                        isdiminutive, isnumber,
                                        issubstantivised_verb, sasta_long,
                                        sasta_pseudonym, short_nucl_n,
                                        spec_noun)
from typing import List, Tuple

comma = ','
def recognised_wordnodepos(node: SynTree, pos: str) -> bool:
    '''
    The function *recognised_wordnodepos* determines for *node* whether it is a known
    word of part of speech code *pos*.

    It distinguishes several subcases that yield the result True:

    * the value of the *word* attribute of *node* is a known word form (as determined by the function *lex.informlexiconpos*

    * the lower-cased value of the *word* attribute of *node* is a known word form (as determined by the function *lex.informlexiconpos*

    * the node is a node for a compound, as determined by the function *iscompound*:

        .. autofunction:: sastadev.treebankfunctions::iscompound
           :noindex:

    * the node is a node for a diminutive, as determined by the function *isdiminutive*:

        .. autofunction:: sastadev.treebankfunctions::isdiminutive
           :noindex:

    * the node is a node for a name part, as determined by the function *lex.isa_namepart*


    '''
    word = getattval(node, 'word')
    lcword = word.lower()
    result = lex.informlexiconpos(word, pos) or lex.informlexiconpos(lcword, pos) or \
        iscompound(node) or isdiminutive(node) or lex.isa_namepart_uc(word)
    return result


def recognised_wordnode(node: SynTree) -> bool:
    '''
    The function *recognised_wordnode* determines for *node* whether it is a known word.

    It distinguishes several subcases that yield the result True:

    * the value of the *word* attribute of *node* is a known word form (as determined
    by the function *lex.informlexicon*

    * the lower-cased value of the *word* attribute of *node* is a known word form (as
    determined by the function *lex.informlexicon

    * the node is a node for a compound, as determined by the function *iscompound*:

        .. autofunction:: sastadev.treebankfunctions::iscompound

    * the node is node for a diminutive, as determined by the function *isdiminutive*:

        .. autofunction:: sastadev.treebankfunctions::isdiminutive

    * the node is a node for a name part, as determined by the function *lex.isa_namepart*


    '''

    word = getattval(node, 'word')
    lcword = word.lower()
    result = lex.informlexicon(word) \
        or lex.informlexicon(lcword) \
        or iscompound(node) \
        or isdiminutive(node) \
        or lex.isa_namepart(word)
    return result


def recognised_lemmanode(node: SynTree) -> bool:
    '''
    The function *recognised_lemmanode* checks whether the *lemma* of *node* is in
    the lexicon  (as determined by the function *lex.informlexicon*).

    '''
    lemma = getattval(node, 'lemma')
    result = lex.informlexicon(lemma)
    return result


def recognised_lemmanodepos(node: SynTree, pos: str) -> bool:
    '''
    The function *recognised_lemmanodepos* checks whether the *lemma* of *node* is in
    the lexicon with part of speech *pos* (as determined by * lex.informlexiconpos*).

    '''
    lemma = getattval(node, 'lemma')
    result = lex.informlexiconpos(lemma, pos)
    return result


def asta_recognised_lexnode(node: SynTree) -> bool:
    '''
    The function *asta_recognised_lexnode* determines whether *node* should count as a
    lexical verb in the ASTA method.

    This is the case if *pt* equals *ww* and the node is not a substantivised verb as
    determined by the function *issubstantivised_verb*:

    .. autofunction:: sastadev.treebankfunctions::issubstantivised_verb

    '''
    if issubstantivised_verb(node):
        result = False
    else:
        result = getattval(node, 'pt') == 'ww'
    return result


def asta_recognised_nounnode(node: SynTree) -> bool:
    '''
    The function *asta_recognised_nounnode* determines whether *node* should count as a
    noun in the ASTA method.

    This is the case if

    * either the node meets the conditions of *sasta_pseudonym*

       .. autofunction:: sastadev.treebankfunctions::sasta_pseudonym

    * or the node meets the conditions of *spec_noun*

       .. autofunction:: sastadev.treebankfunctions::spec_noun

    * or the node meets the conditions of *is_duplicate_spec_noun*

       .. autofunction:: sastadev.treebankfunctions::is_duplicate_spec_noun

    * or the node meets the conditions of *sasta_long*

       .. autofunction:: sastadev.treebankfunctions::sasta_long

    * or the node meets the conditions of *recognised_wordnodepos*

       .. autofunction:: sastadev.tblex::recognised_wordnodepos

    * or the node meets the conditions of *recognised_lemmanodepos(node, pos)*

       .. autofunction:: sastadev.tblex::recognised_lemmanodepos(node, pos)

    However, the node should:

    * neither consist of lower case consonants only, as determined by *all_lower_consonantsnode*:

       .. autofunction:: sastadev.treebankfunctions::all_lower_consonantsnode

    * nor satisfy the conditions of *short_nucl_n*:

       .. autofunction:: sastadev.treebankfunctions::short_nucl_n

    '''

    if issubstantivised_verb(node):
        pos = 'ww'
    else:
        pos = 'n'
    result = sasta_pseudonym(node)
    result = result or spec_noun(node)
    result = result or is_duplicate_spec_noun(node)
    result = result or sasta_long(node)
    result = result or recognised_wordnodepos(node, pos)
    result = result or recognised_lemmanodepos(node, pos)
    result = result and not (all_lower_consonantsnode(node))
    result = result and not (short_nucl_n(node))
    result = result and not iscardinal(node)
    return result


def iscardinal(node):
    word = getattval(node, 'word')
    wordlc = word.lower()
    if wordlc == '':
        result = False
    elif wordlc in lex.cardinallexicon:
        result = True
    else:
        result = False
    return result

def asta_recognised_wordnode(node: SynTree) -> bool:
    result = sasta_pseudonym(node)
    result = result or spec_noun(node)
    result = result or is_duplicate_spec_noun(node)
    result = result or sasta_long(node)
    result = result or recognised_wordnode(node)
    result = result or recognised_lemmanode(node)
    result = result or isnumber(node)
    result = result or lex.isa_namepart(getattval(node, 'word'))
    result = result and not (all_lower_consonantsnode(node))
    result = result and not (short_nucl_n(node))
    return result


def get_aanloop_and_core(nodes: List[SynTree]) -> Tuple[List[SynTree], List[SynTree]]:
    """
    split the word nodes into a word node list aanloopnodes and a word node corenodes where the aanloopnodes contains
    one or more initial interjections followed by comma, or "kijk (eens/maar/ hier/daar...)" followed by a comma

    :param nodes:
    :return:
    """
    aanloopnodes = []
    corenodes = []

    if len(nodes) > 3 and \
           getattval(nodes[0], 'word').lower() == 'kijk' and \
           getattval(nodes[1], 'word').lower() in ['eens', 'maar', 'nou', 'hier', 'daar'] and \
           getattval(nodes[2], 'word').lower() == comma:
        aanloopnodes = nodes[0:3]
        corenodes = nodes[3:]
    elif len(nodes) >= 2:
        commafound = False
        for node in nodes:
            if commafound:
                break
            if getattval(node, 'lemma').lower() in lex.allfillers:
                aanloopnodes.append(node)
            elif getattval(node, 'lemma').lower() == comma:
                aanloopnodes.append(node)
                commafound = True
            else:
                aanloopnodes = []
                break
        corenodes = nodes[len(aanloopnodes):]
    else:
        aanloopnodes = []
        corenodes = nodes

    return aanloopnodes, corenodes
