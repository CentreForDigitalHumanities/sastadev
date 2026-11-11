"""
The module *tblex* contains functions that require functions
from the lexicon module and from the treebankfunctions module
"""
from sastadev.conf import settings
import sastadev.lexicon as lex
# from sastadev.lexicon import (informlexicon, isa_namepart, chatspecial, additionalwordslexicon, spellingadditions, \
#     isallersuperlative, issuperadjective, nonwordslexicon, acronyms_lexicon)
from sastadev.queryconstants import Tarsp_kijkVU
from sastadev.sastatypes import SynTree
from sastadev.stringfunctions import compoundsep, ispunctuation
import sastadev.treebankfunctions as tbf
# from sastadev.treebankfunctions import (all_lower_consonantsnode, find1, getattval, getnodeyield,
#                                         is_duplicate_spec_noun, iscompound,
#                                         isdiminutive, isnumber,
#                                         issubstantivised_verb, sasta_long,
#                                         sasta_pseudonym, short_nucl_n,
#                                         spec_noun)
from typing import List, Tuple

comma = ','
alpinoparse = settings.PARSE_FUNC
gav = tbf.getattval

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
    word = tbf.getattval(node, 'word')
    lcword = word.lower()
    result = lex.informlexiconpos(word, pos) or lex.informlexiconpos(lcword, pos) or \
        tbf.iscompound(node) or tbf.isdiminutive(node) or lex.isa_namepart_uc(word)   ## is_acronym left out here
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

    word = tbf.getattval(node, 'word')
    lcword = word.lower()
    result = lex.informlexicon(word) \
        or lex.informlexicon(lcword) \
        or tbf.iscompound(node) \
        or tbf.isdiminutive(node) \
        or lex.isa_namepart(word)   ## is_acronym left out here, not used by young children, asta has its own function
    return result


def recognised_lemmanode(node: SynTree) -> bool:
    '''
    The function *recognised_lemmanode* checks whether the *lemma* of *node* is in
    the lexicon  (as determined by the function *lex.informlexicon*).

    '''
    lemma = gav(node, 'lemma')
    result = lex.informlexicon(lemma)
    return result


def recognised_lemmanodepos(node: SynTree, pos: str) -> bool:
    '''
    The function *recognised_lemmanodepos* checks whether the *lemma* of *node* is in
    the lexicon with part of speech *pos* (as determined by * lex.informlexiconpos*).

    '''
    lemma = gav(node, 'lemma')
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
    if tbf.issubstantivised_verb(node):
        result = False
    else:
        result = gav(node, 'pt') == 'ww'
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

    * or the lemma of the node is an acronym (function *is_acronym*)

       .. autofunction:; sastadev.tblex::is_acronym

    However, the node should:

    * neither consist of lower case consonants only, as determined by *all_lower_consonantsnode*:

       .. autofunction:: sastadev.treebankfunctions::all_lower_consonantsnode

    * nor satisfy the conditions of *short_nucl_n*:

       .. autofunction:: sastadev.treebankfunctions::short_nucl_n

    '''

    lemma = gav(node, 'lemma')
    if tbf.issubstantivised_verb(node):
        pos = 'ww'
    else:
        pos = 'n'
    result = tbf.sasta_pseudonym(node)
    result = result or tbf.spec_noun(node)
    result = result or tbf.is_duplicate_spec_noun(node)
    result = result or tbf.sasta_long(node)
    result = result or recognised_wordnodepos(node, pos)
    result = result or recognised_lemmanodepos(node, pos)
    result = result or lex.is_acronym(lemma)
    result = result or lemma in lex.valid_asta_words_lexicon
    result = result and not (tbf.all_lower_consonantsnode(node))
    result = result and not (tbf.short_nucl_n(node))
    result = result and not iscardinal(node)
    return result


def iscardinal(node):
    word = gav(node, 'word')
    wordlc = word.lower()
    if wordlc == '':
        result = False
    elif wordlc in lex.cardinallexicon:
        result = True
    else:
        result = False
    return result

def asta_recognised_wordnode(node: SynTree) -> bool:
    word = gav(node, 'word')
    result = tbf.sasta_pseudonym(node)
    result = result or tbf.spec_noun(node)
    result = result or tbf.is_duplicate_spec_noun(node)
    result = result or tbf.sasta_long(node)
    result = result or recognised_wordnode(node)
    result = result or recognised_lemmanode(node)
    result = result or tbf.isnumber(node)
    result = result or lex.isa_namepart(word)
    result = result or lex.is_acronym(word)
    result = result or word in lex.valid_asta_words_lexicon
    result = result and not (tbf.all_lower_consonantsnode(node))
    result = result and not (tbf.short_nucl_n(node))
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
           tbf.getattval(nodes[0], 'word').lower() == 'kijk' and \
           tbf.getattval(nodes[1], 'word').lower() in ['eens', 'maar', 'nou', 'hier', 'daar'] and \
           tbf.getattval(nodes[2], 'word').lower() == comma:
        aanloopnodes = nodes[0:3]
        corenodes = nodes[3:]
    elif len(nodes) >= 2:
        commafound = False
        for node in nodes:
            if commafound:
                break
            if tbf.getattval(node, 'lemma').lower() in lex.allfillers:
                aanloopnodes.append(node)
            elif tbf.getattval(node, 'lemma').lower() == comma:
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


NodeList = List[SynTree]


def nodesplit(nodelist: List[SynTree], sep=lambda n: tbf.getattval(n, 'lemma') == comma, sepinclude=True) -> List[NodeList]:
    resultlists = []
    currentlist = []
    for node in nodelist:
        if sep(node):
            if sepinclude:
                currentlist.append(node)
            resultlists.append(currentlist)
            currentlist = []
        else:
            currentlist.append(node)
    if currentlist != []:
        resultlists.append(currentlist)
    return resultlists


def getaanloop_core_uitloop(stree: SynTree) -> Tuple[List[NodeList], NodeList, List[NodeList]]:
    """
    splits the nodeyield of stree into a list of aanloops, a core, and a list of uitloops. There can be multiple
    aanlops and uitloops, there must always be a core
    :param stree:
    :return: triple with
    * zero or more aanloops
    * a core
    * zero or more uitloops
    """
    nodeyield = tbf.getnodeyield(stree)
    sentparts = nodesplit(nodeyield)
    aanloops = []
    uitloops = []
    core = []
    corefound = False
    for i, sentpart in enumerate(sentparts):
        # if we dealing with the last sentpart and no core found yet, this must be the core
        if i == len(sentparts) - 1 and not corefound:
            core += sentpart
            return aanloops, core, uitloops
        elif not corefound and canbeaanloop(sentpart):
            aanloops.append(sentpart)
        elif corefound and canbeuitloop(sentpart):
            uitloops.append(sentpart)
        else:
            misanalyseduitloop = [nd for uitloop in uitloops for nd in uitloop]
            core = core + misanalyseduitloop + sentpart
            uitloops = []
            corefound = True
    return aanloops, core, uitloops


def canbeaanloop(nodes: List[SynTree]) -> bool:
    prevnode = None
    for node in nodes:
        nodept = tbf.getattval(node, 'pt')
        nodelemma = tbf.getattval(node, 'lemma')
        nodeword = tbf.getattval(node, 'word')
        if nodept == 'ww' and nodeword.lower() != 'kijk':
            return False
        elif nodeword.lower() == 'kijk':
            prevnode = node
            continue
        elif nodelemma in lex.kijkvuadverbs and tbf.getattval(prevnode, 'word').lower() == 'kijk':
            prevnode = node
            continue
        elif nodelemma in lex.interjections:
            prevnode = node
            continue
        elif nodelemma in lex.vuwordslexicon:
            prevnode = node
            continue
        elif nodelemma in lex.tswnouns:
            prevnode = node
            continue
        elif nodept == 'n' and tbf.getattval(node, 'ntype') == 'eigen':
            prevnode = node
            continue
        elif nodelemma.lower() in lex.allfillers:
            prevnode = node
            continue
        elif nodelemma == comma:
            prevnode = node
            continue
        else:
            return False
        prevnove = node
    return True

def canbeuitloop(nodes: List[SynTree]) -> bool:
    realnodes = [node for node in nodes if tbf.getattval(node, 'pt') != 'let']
    if len(realnodes) > 4:
        return False
    for i, node in enumerate(nodes):
        nodept = tbf.getattval(node, 'pt')
        nodelemma = tbf.getattval(node, 'lemma')
        nodeword = tbf.getattval(node, 'word')
        if nodept == 'ww'  and nodeword.lower() != 'kijk':
            return False
        elif nodelemma == 'hè' or nodelemma == 'he':   # we wnat to keep these in the core
            return False
        elif nodept == 'vg':  # this too strict but we want to exclude coordinations such as x, y, en z
            return False
    return True


def tarsp_kijkvu(node: SynTree) -> bool:

    nodeparent = node.getparent()
    matches = nodeparent.xpath(f""".//node[{Tarsp_kijkVU}]""")
    result = matches != [] and node in matches
    return result


def isrealwordnode(node: SynTree) -> bool:
    nodept = tbf.getattval(node, 'pt')
    nodelemma = tbf.getattval(node, 'lemma')
    result = 'word' in node.attrib and nodept != 'let' and (nodept != "tsw" or nodelemma in lex.tswnouns) and \
              len(nodelemma) != 1 and nodelemma not in lex.chatcodes and nodelemma not in lex.fillers and \
             not tarsp_kijkvu(node)
    return result

def is_rpronoun(node: SynTree) -> bool:
    nodelemma = tbf.getattval(node, 'lemma')
    result = nodelemma in lex.rpronoun_lemmas
    return result

def isalpinonouncompound(wrd: str) -> bool:
    if ispunctuation(wrd):
        return False
    fullstr = f'geen {wrd}'  # geen makes it a noun and can combine with uter and neuter, count and mass, sg and plural
    tree = alpinoparse(fullstr)
    # find the noun
    if tree is None:
        settings.LOGGER.error(f'Parsing {fullstr} failed')
        return False
    nounnode = tbf.find1(tree, './/node[@pt="n"]')
    if nounnode is None:
        # settings.LOGGER.error(f'No noun found in {fullstr} parse')
        return False
    nounwrd = tbf.getattval(nounnode, 'word')
    if nounwrd != wrd:
        settings.LOGGER.error(f'Wrong noun ({nounwrd}) found in {fullstr} parse')
        return False
    nounlemma = tbf.getattval(nounnode, 'lemma')
    if compoundsep in nounlemma:
        parts = nounlemma.split(compoundsep)
        unknownparts = [part for part in parts if not lex.known_word(part) and part != "DIM"]
        result = unknownparts == []
        if not result:
            settings.LOGGER.error(f'Unknown words ({comma.join(unknownparts)}) found in {fullstr} parse')
            return False
        return True
    else:
        return False

