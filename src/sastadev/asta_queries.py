from typing import Callable, Dict, List, Optional

from sastadev.conf import settings
from sastadev.dedup import getposition
from sastadev.macros import expandmacros
from sastadev.metadata import (longrep, repeated, repeatedseqtoken, repetition,
                               substringrep)
from sastadev.normalise_lemma import normaliselemma
from sastadev.sastatypes import SynTree
from sastadev.stringfunctions import string2list
from sastadev.tblex import asta_recognised_lexnode, asta_recognised_nounnode
from sastadev.treebankfunctions import (clausecats, find1, getattval,
                                        getnodeyield, getyield, showtns)

noun_xpath = './/node[%asta_noun%]'
expanded_noun_xpath = expandmacros(noun_xpath)

lex_path = './/node[%ASTA_LEX%]'
expanded_lex_xpath = expandmacros(lex_path)

astabijzinquerybase = './/node[%ASTA_Bijzin%]'
astabijzinquery = expandmacros(astabijzinquerybase)

astacoredelpvquery = './/node[%coredelpv%]'
expandedastacoredelpvquery = expandmacros(astacoredelpvquery)

dpancestorsquery = 'ancestor::node[@rel="dp"] | self::node[@rel="dp" or @rel="--"]'

lemma_path = './/node[%asta_noun% or %ASTA_LEX%]'
expandedlemma_path = expandmacros(lemma_path)
# this covers all repetitions but the short repetitions should not be included
repetitioncond = f'@subcat="{repetition}"'
longrepetitioncond = f'@value="{repeated}" or @value="{repeatedseqtoken}" or @value="{longrep}" or @value="{substringrep}"'


def astalemmafunction(node: SynTree) -> str:
    repetitionantecedent = getrepetitionantecedent(node)
    if repetitionantecedent is not None:
        result = astalemmafunction(repetitionantecedent)
    else:
        rawlemma = getattval(node, 'lemma')
        rawword = getattval(node, 'word')
        pt = getattval(node, 'pt')
        if pt == 'n':
            result = normaliselemma(rawword, rawlemma)
        else:
            resultlist = [c for c in rawlemma if c != '_']
            result = ''.join(resultlist)
    return result


def getrepetitionantecedent(node: SynTree) -> Optional[SynTree]:
    topnode = find1(node, 'ancestor::alpino_ds')
    dupindex = get_dupindex(topnode, longrepetitioncond)
    nodepos = getattval(node, 'begin')
    if nodepos in dupindex:
        antecedentpos = dupindex[nodepos]
        antecedent = find1(
            topnode, f'.//node[@word and @begin="{antecedentpos}"]')
    else:
        antecedent = None
    return antecedent


def get_dupindex(stree: SynTree, cond: str) -> Dict[str, str]:
    dupindex = {}
    dupxpath = './/xmeta[{cond}]'.format(cond=cond)
    dupmetadatalist = stree.xpath(dupxpath)
    for meta in dupmetadatalist:
        if 'annotatedposlist' in meta.attrib and 'annotationposlist' in meta.attrib:
            keyliststr = meta.attrib['annotatedposlist']
            keylist = string2list(keyliststr)
            valueliststr = meta.attrib['annotationposlist']
            valuelist = string2list(valueliststr)
            if len(keylist) != len(valuelist):
                settings.LOGGER.error(
                    'Error in metadata: {} in sentence {}'.format(meta, getyield(stree)))
            else:
                for key, val in zip(keylist, valuelist):
                    dupindex[key] = val
    return dupindex


def asta_noun(
        stree: SynTree) \
        -> List[SynTree]:
    '''The function *asta_noun* uses the function *asta_x* with parameters *stree*,
    *expanded_noun_path* and the function *asta_recognised_nounnode*.

    The *expanded_noun_path* is the expansion of the macro **noun_path**.

    .. autofunction:: sastadev.tblex::asta_recognised_nounnode

    '''
    results = asta_x(stree, expanded_noun_xpath, asta_recognised_nounnode)
    return results


def asta_lex(stree: SynTree) -> List[SynTree]:
    '''The function *asta_lex* uses the function *asta_x* with parameters *stree*,
    *expanded_lex_path* and the function *asta_recognised_nounnode*.

    The *expanded_lex_path* is the expansion of the macro **lex_path**.

    .. autofunction:: sastadev.tblex::asta_recognised_lexnode
         :noindex:

    '''

    results = asta_x(stree, expanded_lex_xpath, asta_recognised_lexnode)
    return results


def asta_recognised_lexicalnode(node: SynTree) -> bool:
    result = asta_recognised_nounnode(node) or asta_recognised_lexnode(node)
    return result


def asta_lemma(stree: SynTree) -> List[SynTree]:
    '''The function *asta_lemma* uses the function *asta_x* with parameters *stree*,
    *lemma_path* and the function *asta_recognised_lexicalnode*.


    .. autofunction:: sastadev.treebankfunctions::asta_recognised_lexicalnode
         :noindex:

    '''
    results = asta_x(stree, expandedlemma_path, asta_recognised_lexicalnode)
    return results


def old_asta_noun(stree: SynTree) -> List[SynTree]:
    theyield = getyield(stree)   # for debugging purposes
    thenodeyield = getnodeyield(stree)
    cond1 = '@value="{}" or @value="{}" or @value="{}" or @value="{}"'.format(
        repeated, repeatedseqtoken, longrep, substringrep)
    dupindex = get_dupindex(stree, cond1)
    cond2 = '@subcat="{}"'.format(repetition)
    allrepdupindex = get_dupindex(stree, cond2)
    revallrepdupindex = {val: key for key, val in allrepdupindex.items()}
    noun_nodes = stree.xpath(expanded_noun_xpath)
    # print(showtns(noun_nodes))

    clean_noun_nodes = noun_nodes

    # remove the nodes that should get it from this function
    clean_noun_nodes = [node for node in clean_noun_nodes if getattval(
        node, 'begin') not in allrepdupindex]

    # remove words not recognised as nouns; is dit nodig? Ja dit is nodig!!!
    clean_noun_nodes = [
        node for node in clean_noun_nodes if asta_recognised_nounnode(node)]
    # print(showtns(clean_noun_nodes))

    additional_nodes = []
    for key in dupindex:
        keynode = find1(
            stree, './/node[(@pt or @pos) and @begin="{}"]'.format(key))
        if keynode is not None:
            val = dupindex[key]
            valnode = find1(
                stree, './/node[(@pt or @pos) and @begin="{}"]'.format(val))
            if valnode is not None:
                if valnode in clean_noun_nodes:
                    additional_nodes.append(keynode)

    result = clean_noun_nodes + additional_nodes
    # print(showtns(result))
    return result


def verbleftof(node: SynTree, positions: List[str]) -> bool:
    nodebegin = getattval(node, 'begin')
    for position in positions:
        if int(position) < int(nodebegin):
            return True
    return False


def asta_delpv(stree: SynTree) -> List[SynTree]:
    coredelpvnodes = stree.xpath(expandedastacoredelpvquery)
    streeleaves = getnodeyield(stree)
    wwbegins = [getattval(node, 'begin')
                for node in streeleaves if getattval(node, 'pt') == 'ww']
    delpvnodes = [node for node in coredelpvnodes if node.xpath(
        dpancestorsquery) == [] or not (verbleftof(node, wwbegins))]
    return delpvnodes


def asta_x(stree: SynTree,
           xpathexpr: str,
           recognized_x_f: Callable[[SynTree], bool]) -> List[SynTree]:
    theyield = getyield(stree)   # for debugging purposes
    thenodeyield = getnodeyield(stree)
    cond1 = '@value="{}" or @value="{}" or @value="{}" or @value="{}"'.format(
        repeated, repeatedseqtoken, longrep, substringrep)
    dupindex = get_dupindex(stree, cond1)
    cond2 = '@subcat="{}"'.format(repetition)
    allrepdupindex = get_dupindex(stree, cond2)
    revallrepdupindex = {val: key for key, val in allrepdupindex.items()}
    x_nodes = stree.xpath(xpathexpr)
    # print(showtns(noun_nodes))

    clean_x_nodes = x_nodes

    # remove the nodes that should get it from this function
    clean_x_nodes = [node for node in clean_x_nodes if getattval(
        node, 'begin') not in allrepdupindex]

    # remove words not recognised as nouns; is dit nodig? Ja dit is nodig!!!
    clean_x_nodes = [node for node in clean_x_nodes if recognized_x_f(node)]
    # print(showtns(clean_noun_nodes))

    additional_nodes = []
    for key in dupindex:
        keynode = find1(
            stree, './/node[(@pt or @pos) and @begin="{}"]'.format(key))
        if keynode is not None:
            val = dupindex[key]
            valnode = find1(
                stree, './/node[(@pt or @pos) and @begin="{}"]'.format(val))
            if valnode is not None:
                if valnode in clean_x_nodes:
                    additional_nodes.append(keynode)

    result = clean_x_nodes + additional_nodes
    # print(showtns(result))
    return result


def getmluxnodes(mluxnodes, posnodes, dupinfo):
    resultnodes = []
    for node in mluxnodes:
        nodeposition = getposition(node)
        origpos = get_origpos(nodeposition, dupinfo)
        targetnode = find_node(origpos, posnodes)
        if targetnode is not None:
            resultnodes.append(node)
    return resultnodes


def get_origpos(nodeposition, dupinfo):
    newposition = nodeposition
    if newposition not in dupinfo.longdups:
        result = None
    else:
        while newposition in dupinfo.longdups:
            newposition = dupinfo.longdups[newposition]
        result = newposition
    return result


def find_node(position, nodes):
    results = [node for node in nodes if getposition(node) == position]
    lresults = len(results)
    if lresults == 0:
        result = None
    elif lresults == 1:
        result = results[0]
    else:
        settings.LOGGER.warning('Multiple nodes found for position {}: {}, in {}'.format(
            position, showtns(results), showtns(nodes)))
        result = results[0]
    return result


bijzin_xpath = './/node[%ASTA_Bijzin%]'
expanded_bijzin_xpath = expandmacros(bijzin_xpath)


def old_asta_bijzin(stree):
    candnodes = stree.xpath(expanded_bijzin_xpath)
    tops = stree.xpath('.//node[@cat="top"]')
    top = tops[0]
    done, resultingnodes = removehoofdzin(top, candnodes)
    return resultingnodes


def removerepetitions(ptnodes: List[SynTree], stree: SynTree) -> List[SynTree]:
    '''
    The function *removerepetitions* returns a list of nodes from *ptnodes* that are
    not marked in the metadata as repetitions.

    '''
    newptnodes = []
    for ptnode in ptnodes:
        ptnodeend = ptnode.attrib['begin'] if 'begin' in ptnode.attrib else None
        xmetaxpath = './/xmeta[@subcat="Repetition" and @annotatedposlist="[{}]"]'.format(
            ptnodeend)
        repmetas = stree.xpath(xmetaxpath)
        if repmetas == []:
            newptnodes.append(ptnode)
    return newptnodes


def asta_bijzin(stree: SynTree) -> List[SynTree]:
    '''
    The function *asta_bijzin* identifies *bijzinnen* in  *stree*. The term *bijzin*
    is used in ASTA in a slightly different way than usual.
    It usually means *subordinate clause*, but in ASTA it is equivalent to the English
    term *clause* (so it can be a main clause or a subordinate clause).

    The function finds each node that is a clause except for the left-most one. For
    example, in *wij gaan naar huis als hij ziek is* the leftmost clause starts at
    *wij* (and is not marked as a clause), and the second one starts with *als*,
    and that one is found as a *Bijzin*.

    If a main clause starts with a subordinate clause, then this subordinate clause is
    contained in the main clause: In e.g. *als hij ziek is gaan we naar huis* the
    subordinate clause is *als hij ziek is* and the main clause is *als hij ziek is
    gaan we naar huis*. We should mark *gaan* as the first word of a clause, but
    in the Alpino structure it is not the first word of a clause. For this reason we set
    the start of a clause
    that contains another clause with the same value for the *begin* attribute equal
    to the *end* attribute of the contained clause, so that a marking appears under the
    word *gaan*, the first word after the contained clause.

    The function launches an XPath query (*astabijzinquery*)  which crucially uses the
    macro *ASTA_Bijzin*. This query yields not only true clause nodes but also nodes
    of words that typically introduce clauses but have been parsed wrongly.
    These words may have been repeated, and if so, only one of them should be in the
    results, so the repetitions are removed from the results by means of the function
    *removerepetitions*:

    .. autofunction:: sastadev.asta_queries::removerepetitions
    '''
    theyield = getyield(stree)
    clausenodes = stree.xpath(astabijzinquery)
    ptnodes = [n for n in clausenodes if 'pt' in n.attrib]
    okptnodes = removerepetitions(ptnodes, stree)
    trueclausenodes = [
        n for n in clausenodes if getattval(n, 'cat') in clausecats]
    # alternative 1
    # sortedclausenodes = sorted(trueclausenodes, key=lambda x: (int(getattval(x,'begin')), -int(getattval(x, 'end'))))
    # result = sortedclausenodes[1:] + okptnodes

    # alternative2 -follows the conventions for ASTA
    sortedclausenodes = sorted(trueclausenodes, key=lambda x: (
        int(getattval(x, 'begin')), int(getattval(x, 'end'))))
    if len(sortedclausenodes) > 1:
        cn0 = sortedclausenodes[0]
        cn1 = sortedclausenodes[1]
        if getattval(cn1, 'begin') == getattval(cn0, 'begin'):
            cn0end = getattval(cn0, 'end')
            newbegin = cn0end
            newokptnodexpath = '//node[@pt and @begin="{newbegin}"]'.format(
                newbegin=newbegin)
            newokptnode = find1(cn1, newokptnodexpath)
            result = sortedclausenodes[2:] + okptnodes
            if newokptnode is not None:
                result += [newokptnode]
        else:
            result = sortedclausenodes[1:] + okptnodes
    else:
        result = sortedclausenodes[1:] + okptnodes

    # ad hoc statement to ensure that there are no None matches should not happen anymore
    result = [el for el in result if el is not None]
    return result


def removehoofdzin(stree, clausenodes):
    resultingnodes = clausenodes
    done = False
    for child in stree:
        chatt = getattval(child, 'cat')
        if chatt in clausecats:
            if child in clausenodes:
                resultingnodes.remove(child)
                done = True
                return done, resultingnodes
            else:
                done = True
        if not done:
            done, resultingnodes = removehoofdzin(child, clausenodes)
    return done, resultingnodes

def asta_xxx(stree: SynTree) -> List[SynTree]:
    results = []
    nodeyield = getnodeyield(stree)
    for node in nodeyield:
        if getattval(node, 'word').lower() in ['xxx', 'yyy', 'www']:
            results.append(node)
    return results