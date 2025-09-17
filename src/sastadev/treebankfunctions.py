"""
various treebank functions

"""
import functools
import re
# import logging
from copy import copy, deepcopy
# import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from more_itertools import unique_everseen
from lxml import etree

from sastadev.anonymization import pseudonymre
# from sastadev.lexicon import informlexiconpos, isa_namepart_uc, informlexicon, isa_namepart
# import lexicon as lex
from sastadev.conf import settings
from sastadev import correctionlabels
from sastadev.metadata import Meta
from sastadev.sastatoken import Token
from sastadev.sastatypes import (FileName, OptPhiTriple, PhiTriple, Position,
                                 PositionMap, PositionStr, Span, SynTree,
                                 UttId)
from sastadev.stringfunctions import allconsonants

# from sastadev.tblex import recognised_wordnode, recognised_lemmanode, recognised_wordnodepos, recognised_lemmanodepos


class Metadata:
    """
    contains 3 elements, each a string: type, name, value
    """

    def __init__(self, thetype, thename, thevalue):
        self.type = thetype
        self.name = thename
        self.value = thevalue

    def md2PEP(self):
        result = '##META {} {} = {}'.format(self.type, self.name, self.value)
        return result

    def md2XMLElement(self):
        result = etree.Element('meta', type=self.type,
                               name=self.name, value=self.value)
        return result


#: The constant *min_sasta_length* sets the minimum length a word must have to count as
#: a real, though unknown, word
min_sasta_length = 9

#: The constant *sasta_short_length* sets the maximum length an unknown word may have
#: to be discarded as a real word
sasta_short_length = 4

space = ' '
vertbar = '|'
#: The constant *compoundsep* is the symbol used to separate the compound parts in a
# lemma.
compoundsep = '_'

numberpattern = r'^[\d\.,]+$'
numberre = re.compile(numberpattern)

topcat = 'top'

# next 3 derived from the alpino dtd
allrels = ['hdf', 'hd', 'cmp', 'sup', 'su', 'obj1', 'pobj1', 'obj2', 'se', 'pc', 'vc', 'svp', 'predc', 'ld', 'me',
           'predm', 'obcomp', 'mod', 'body', 'det', 'app', 'whd', 'rhd', 'cnj', 'crd', 'nucl', 'sat', 'tag', 'dp',
           'top', 'mwp', 'dlink', '--']

allcats = ['smain', 'np', 'ppart', 'ppres', 'pp', 'ssub', 'inf', 'cp', 'du', 'ap', 'advp', 'ti', 'rel', 'whrel',
           'whsub', 'conj', 'whq', 'oti', 'ahi', 'detp', 'sv1', 'svan', 'mwu', 'top', 'cat', 'part']
# part occurs but is not official

allpts = ['let', 'spec', 'bw', 'vg', 'lid',
          'vnw', 'tw', 'ww', 'adj', 'n', 'tsw', 'vz']

openclasspts = ['bw', 'ww', 'adj', 'n']

clausecats = ['smain', 'ssub', 'inf', 'cp', 'ti', 'rel',
              'whrel', 'whsub', 'whq', 'oti', 'ahi', 'sv1', 'svan']
clausebodycats = ['smain', 'ssub', 'inf', 'sv1', 'ppart', 'ppres']

trueclausecats = ['smain', 'cp', 'rel', 'whrel', 'whsub', 'whq', 'sv1', 'svan']

complrels = ['su', 'obj1', 'pobj1', 'obj2',
             'se', 'pc', 'vc', 'svp', 'predc', 'ld']

headrels = ['hd', 'crd']

extendedheadrels  = ['hdf']

mainclausecats = ['smain', 'whq', 'sv1']

ptsubclasspairs = [('n', 'ntype'), ('tw', 'numtype'), ('vnw', 'vwtype'), ('lw', 'lwtype'), ('vz', 'vztype'),
                   ('vg', 'conjtype'), ('spec', 'spectype'), ('ww', 'wvorm')]
ptsubclassdict = {pt: subclass for (pt, subclass) in ptsubclasspairs}

pluralcrds = [('en',)]

hwws_tijd = ['hebben', 'zijn', 'zullen']
hwws_aspect = ['gaan', 'komen', 'zijn', 'blijven',
               'zitten', 'liggen', 'lopen', 'staan']
hwws_voice = ['worden', 'zijn']
hwws_modal = ['kunnen', 'zullen', 'mogen', 'moeten',
              'willen', 'hoeven', 'horen', 'behoren']
hwws_caus = ['doen', 'laten']
hwws_circum = ['doen']

tarsp_auxverbs = set(hwws_tijd + hwws_aspect + hwws_voice
                     + hwws_modal + hwws_caus + hwws_circum)

potentialdet_onbvnws = {'al', 'alle', 'beide', 'een', 'elk', 'elke', 'ene', 'enig', 'enige', 'enkel', 'ettelijke',
                        'evenveel', 'geen', 'ieder', 'meer', 'meerdere', 'menig', 'minder', 'minst', 'sommig',
                        'teveel', 'tevéél', 'veel', 'weinig', 'één', 'keiveel'}

# uttidquery = "//meta[@name='uttid']/@value"
sentidxpath = './/sentence/@sentid'

# altquery = "//meta[@name='alt']/@value"
metaquerytemplate = "//meta[@name='{}']/@value"
sentencexpathquery = "//sentence/text()"

uniquecounter = 0

countattvalxpathtemplate = 'count(.//node[@{att}="{val}"])'
countcompoundxpath = 'count(.//node[contains(@lemma, "_")])'

monthnames = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus',
              'september', 'oktober', 'november', 'december']

origuttxpath = './/meta[@name="origutt"]/@value'


inflectional_attributes = {'ww': {'buiging', 'getalN',  'pvagr', 'pvtijd', 'wvorm'},
                           'n': {'getal', 'graad'},
                           'adj': {'buiging', 'graad', 'naamval'},
                           'bw': {},
                           'vz': {},
                           'tsw': {},
                           'lid': {'naamval', 'npagr'},
                           'vnw': {'buiging', 'getal', 'naamval', 'npagr', 'persoon', 'status' }
                           }

all_inflectional_attributes = functools.reduce(lambda x, y: x.union(y), [inflectional_attributes[pt] for pt in inflectional_attributes])

#: the constant *inflate_start* contains the value for the *begin* attribute of the first word node in an inflated tree
inflate_start = 10

#: the constant *inflate_step* contains the value of the increase to be made to get the value of the *begin* attribute
#: of the next word node in an inflated tree
inflate_step = 10

def adjacent(node1: SynTree, node2: SynTree, stree: SynTree) -> bool:
    """
    :param node1:
    :param node2:
    :param stree: syntactic structure containing *node1* and *node2*
    :return: True if *node1* is adjacent to *node2* in *stree*, False otherwise

    The function *adjacent* determines whether *node1* is adjacent to *node1* in syntactic structure *stree*,
    and it works correctly in inflated syntactic structures. The two nodes must be nodes for words.
    """
    yieldnodes = getnodeyield(stree)
    for i, n in enumerate(yieldnodes):
        if yieldnodes[i] == node1:
            prec = yieldnodes[i - 1] if i > 0 else None
            succ = yieldnodes[i + 1] if i < len(yieldnodes) - 1 else None
            result = prec == node2 or succ == node2
            return result
    return False


def immediately_precedes(node1: SynTree, node2: SynTree, stree: SynTree) -> bool:
    """
    :param node1:
    :param node2:
    :param stree: syntactic structure containing *node1* and *node2*
    :return: True if *node1* immediately precedes *node2* in *stree*, False otherwise

    The function *immediately_precedes* determines whether *node1* immediately precedes *node1* in syntactic structure *stree*,
    and it works correctly in inflated syntactic structures. The two nodes must be nodes for words.
    """
    yieldnodes = getnodeyield(stree)
    for i, n in enumerate(yieldnodes):
        if yieldnodes[i] == node1:
            succ = yieldnodes[i + 1] if i < len(yieldnodes) - 1 else None
            result = succ == node2
            return result
    return False


def immediately_follows(node1: SynTree, node2: SynTree, stree: SynTree) -> bool:
    """
    :param node1:
    :param node2:
    :param stree: syntactic structure containing *node1* and *node2*
    :return: True if *node1* immediately follows *node2* in *stree*, False otherwise

    The function *immediately_follows* determines whether *node1* immediately follows *node1* in syntactic structure *stree*,
    and it works correctly in inflated syntactic structures. The two nodes must be nodes for words.
    """
    return immediately_precedes(node2, node1, stree)

def is_neut_sg(node: SynTree) -> bool:
    result = getattval(node, 'pt') == 'n' and getattval(node, 'getal') == 'ev' and \
             (getattval(node, 'genus') == 'onz' or getattval(node, 'graad') == 'dim')
    return result

def isdefdet(node: SynTree) -> bool:
    nodelemma = getattval(node, 'lemma')
    nodept = getattval(node, 'pt')
    nodevwtype = getattval(node, 'vwtype')
    nodecase = getattval(node, 'naamval')
    if nodelemma in ['de', 'het', 'deze', 'die', 'dit', 'dat']:
        return True
    if nodept == 'vnw' and nodevwtype in ['bez']:
        return True
    if nodept == 'n' and nodecase == 'gen':
        return True
    return False


def countav(stree: SynTree, att: str, val: str) -> int:
    countattvalxpath = countattvalxpathtemplate.format(att=att, val=val)
    result = stree.xpath(countattvalxpath)
    return result


def modalinv(node: SynTree) -> bool:
    infl = getattval(node, 'infl')
    result = infl == 'modal_inv'
    return result


def getcompoundcount(stree: SynTree) -> int:
    result = stree.xpath(countcompoundxpath)
    return result


def copymodifynode(node: SynTree, dct: Dict[str, Any]):
    newnode = copy(node)
    for att in dct:
        newnode.attrib[att] = dct[att]
    return newnode


def myfind(tree: SynTree, query: str) -> Optional[SynTree]:
    list = tree.xpath(query)
    if list == []:
        return None
    else:
        return list[0]


def getmeta(syntree: SynTree, attname: str, treebank: bool = True) -> Optional[str]:
    prefix = "." if treebank else ""
    thequery = prefix + metaquerytemplate.format(attname)
    result = getqueryresult(syntree, xpathquery=thequery)
    return result


def normalizedword(stree: SynTree) -> Optional[str]:
    if stree is None:
        result = None
    elif 'pt' in stree.attrib:
        theword = getattval(stree, 'word')
        thelemma = getattval(stree, 'lemma')
        if theword is None or theword == '':
            result = None
        elif thelemma is None or thelemma == '':
            result = theword.lower()
        else:
            if theword[0].isupper() and thelemma[0].isupper():
                result = theword
            else:
                result = theword.lower()
    else:
        result = None
    return result


def mkproper(astring: str) -> str:
    result = astring.rjust(4, '0')
    return result


def getproperuttid(syntree: SynTree) -> str:
    global uniquecounter
    result1 = getmeta(syntree, 'uttid')
    if result1 is not None:
        result = 'U' + mkproper(result1)
    else:
        result1 = getsentid(syntree)
        if result1 is not None:
            result = 'S' + mkproper(result1)
        else:
            uniquecounter += 1
            result1 = str(uniquecounter)
            result = 'C' + mkproper(result1)
    return result


def ismainclausenode(node: SynTree) -> bool:
    nodecat = getattval(node, 'cat')
    catok = nodecat in mainclausecats
    if nodecat == 'sv1':
        parentnode = parent(node)
        parentnodecat = getattval(parentnode, 'cat')
        sv1ok = parentnodecat not in ['whq', 'cp', 'rel', 'whrel', 'whsub']
        result = sv1ok
    else:
        result = catok
    return result


def getnodeendmap(stree: SynTree) -> Dict[PositionStr, Position]:
    leaves = getnodeyield(stree)
    result = {getattval(leave, 'end'): i + 1 for i, leave in enumerate(leaves)}
    return result

def getxselseuttid(syntree: SynTree) -> UttId:
    result = getmeta(syntree, 'xsid')
    if result is None:
        result = getmeta(syntree, 'uttid')
        if result is None:
            result = getsentid(syntree)
            if result is None:
                result = '0'
    return result


def getuttid(syntree: SynTree) -> UttId:
    result = getmeta(syntree, 'uttid')
    if result is None:
        result = getsentid(syntree)
        if result is None:
            result = '0'
    return result


def getuttno(syntree: SynTree) -> UttId:
    result = getmeta(syntree, 'uttno')
    if result is None:
        result = '0'
    return result


def getuttidorno(syntree: SynTree) -> UttId:
    result = getmeta(syntree, 'xsid')
    if result is None:
        result = getmeta(syntree, 'uttno')
    if result is None:
        result = '0'
    return result


def getxsid(syntree: SynTree) -> UttId:
    result = getmeta(syntree, 'xsid')
    if result is None:
        result = '0'
    return result


def getaltid(syntree: SynTree) -> Optional[str]:
    result = getmeta(syntree, 'alt')
    return result


def noxpathsentid(syntree: SynTree) -> List[UttId]:
    results = []
    if syntree is not None:
        for child in syntree:
            if child.tag == 'sentence':
                if 'sentid' in child.attrib:
                    results = [child.attrib['sentid']]
    return results


# put the next one in comments, see below for a different definition
# def getsentid(syntree: SynTree) -> Optional[UttId]:
#     result = getqueryresult(syntree, noxpathquery=noxpathsentid)
#     return result


def lastconstituentof(stree: SynTree) -> SynTree:
    curlastend = 0
    topnodes = stree.xpath('.//node[@cat="top"]')
    topnode = topnodes[0]
    for child in topnode:
        if 'cat' in child.attrib:
            childend = int(getattval(child, 'end'))
            if childend > curlastend:
                result = child
                curlastend = childend
    return result


def getsentence(syntree: SynTree, treebank: bool = True) -> Optional[str]:
    prefix = "." if treebank else ""
    thequery = prefix + sentencexpathquery
    result = getqueryresult(syntree, xpathquery=thequery)
    return result


def lastmainclauseof(stree: SynTree) -> SynTree:
    topnodes = stree.xpath('.//node[@cat="top"]')
    curlastmainclause = None
    if topnodes != []:
        topnode = topnodes[0]
        for child in topnode:
            curlastmainclause = reclastmainclauseof(child, curlastmainclause)
    return curlastmainclause


def reclastmainclauseof(node: SynTree, current: SynTree) -> SynTree:
    if node is None:
        result = current
    elif ismainclausenode(node):
        currentend = int(getattval(current, 'end')
                         ) if current is not None else 0
        nodeend = int(getattval(node, 'end'))
        if nodeend > currentend:
            result = node
        else:
            result = current
    else:
        for child in node:
            current = reclastmainclauseof(child, current)
        result = current
    return result


def getrelchildof(node: SynTree, rel: str) -> Optional[SynTree]:
    """
    gets the first child node with rel=rel under a node.
    It should always return a word node (so should have a pt attribute; it does not deal properly with conjunction
    :return: node with grammatical relation rel
    """
    if node is None:
        return None
    for child in node:
        chrel = getattval(child, 'rel')
        if chrel == rel:
            return child
    return None


def getheadof(node: SynTree) -> SynTree:
    return getrelchildof(node, 'hd')


def getdetof(node: SynTree) -> SynTree:
    return getrelchildof(node, 'det')


def getfirstconjunctof(node: SynTree) -> SynTree:
    return getrelchildof(node, 'cnj')


def getextendedheadof(node: SynTree) -> SynTree:
    result1 = getheadof(node)
    if result1 is None:
        result2 = getfirstconjunctof(node)
        if result2 is not None:
            if 'cat' in result2.attrib:
                result = getheadof(result2)
            else:
                result = result2
        else:
            print('here it goes wrong')
            pass

    else:
        result = result1
    return result


persons = ['persoon', '3p', '3m', '3v', '3o', '3', '2v', '2b', '2', '1']
numbers = ['getal', 'ev', 'mv']
genders = ['genus', 'onz', 'zijd', 'fem', 'masc']


def valmerge(v1: str, v2: str, vallist: List[str]) -> str:
    """
    presupposes that v1 and v2 occur in the vallist
    :param v1:
    :param v2:
    :param vallist:
    :return:
    """
    v1ind = vallist.index(v1)
    v2ind = vallist.index(v2)
    newind = max(v1ind, v2ind)
    result = vallist[newind]
    return result


def phimax(v1: str, v2: str) -> str:
    if v1 in persons and v2 in persons:
        result = valmerge(v1, v2, persons)
    elif v1 in numbers and v2 in numbers:
        result = valmerge(v1, v2, numbers)
    elif v1 in genders and v2 in genders:
        result = valmerge(v1, v2, genders)
    else:
        settings.LOGGER.error(
            'Phimax: Illegal or incompatible value combination: V1={}, v2={}'.format(v1, v2))
        result = v1
    return result


def merge(phi1: OptPhiTriple, phi2: OptPhiTriple) -> OptPhiTriple:
    if phi1 is None or phi2 is None:
        return None
    else:
        (p1, n1, g1) = phi1
        (p2, n2, g2) = phi2
        result = (phimax(p1, p2), phimax(n1, n2), phimax(g1, g2))
        return result


def getconjphi(node: SynTree) -> OptPhiTriple:
    crd = tuple(node.xpath('node[@rel="crd"]'))
    conjs = node.xpath('node[@rel="cnj"]')
    conjphis = [getphi(conj) for conj in conjs]
    startphi = ('3', 'getal', 'genus')
    curphi: OptPhiTriple = startphi
    for conjphi in conjphis:
        curphi = merge(curphi, conjphi)
    if curphi is not None:
        if crd in pluralcrds:
            (p, n, g) = curphi
            curphi = (p, 'mv', g)
    return curphi


def getlemma(node: SynTree) -> str:
    if node is None:
        result = ''
    elif 'cat' in node.attrib:
        nodecat = getattval(node, 'cat')
        if nodecat == 'conj':
            result = ''
        elif nodecat == 'mwu':
            result = ''
        else:
            hnode = getheadof(node)
            result = getlemma(hnode)
    elif 'pt' in node.attrib:
        result = getattval(node, 'lemma')
    else:
        result = ''
    return result


def getphi(node: SynTree) -> Optional[PhiTriple]:
    if node is None:
        return None
    elif 'cat' in node.attrib:
        nodecat = getattval(node, 'cat')
        if nodecat == 'conj':
            result = getconjphi(node)
            return result
        elif nodecat == 'mwu':
            result = ('3', 'getal', 'genus')
            return result
        else:
            hnode = getheadof(node)
            result = getphi(hnode)
            return result
    elif 'pt' in node.attrib:
        if 'persoon' in node.attrib:
            person = getattval(node, 'persoon')
        else:
            person = '3'
        if 'getal' in node.attrib:
            number = getattval(node, 'getal')
        else:
            number = 'ev'
        if 'genus' in node.attrib:
            gender = getattval(node, 'genus')
        else:
            gender = 'genus'
        result = (person, number, gender)
        return result
    else:
        return None


def inverted(thesubj: SynTree, thepv: SynTree) -> bool:
    subjphi = getphi(thesubj)
    if subjphi is None:
        return False
    else:
        (subjperson, subjnumber, subjgender) = subjphi
    tense = getattval(thepv, 'pvtijd')
    subjbegin = getattval(thesubj, 'begin')
    subjlemma = getattval(thesubj, 'lemma')
    pvend = getattval(thepv, 'end')
    # maybe defien immediately-follows for inflated trees
    inversion = '2' == subjperson[0] and tense == 'tgw' and subjnumber in ['ev', 'getal'] and \
                pvend <= subjbegin and subjlemma in [
                    'jij', 'je']  # getal added for je
    return inversion


def getattval(node: SynTree, att: str) -> str:
    if node is None:
        result = ''
    elif att in node.attrib:
        result = node.attrib[att]
    else:
        result = ''
    return result


def is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def number2intstring(numberstr: str) -> str:
    if is_number(numberstr):
        result = str(int(numberstr))
    else:
        result = numberstr
    return result


def keycheck(key: Any, dict: Dict[Any, Any]) -> bool:
    if key not in dict:
        settings.LOGGER.error(
            'key {}  not in dictionary. Contents of dictionary:'.format(key))
        for akey, val in dict.items():
            valbgn = getattval(val, 'begin')
            valpt = getattval(val, 'pt')
            valword = getattval(val, 'word')
            valstr = '{}:{}:{}'.format(valbgn, valpt, valword)
            settings.LOGGER.error('{}={}'.format(akey, valstr))
    return key in dict

def getuniqueleaves(stree: SynTree) -> List[SynTree]:
    """
    to obtain a list of unique leaves, i.e.,  for nodes created by indextransform only one result is included
    :param stree:
    :return: list of unique leaves (contains no duplicates)
    """
    rawleaves = getnodeyield(stree)
    rawpositions = [getattval(leave, 'begin') for leave in rawleaves]
    positions = unique_everseen(rawpositions)
    leaves = []
    for position in positions:
        candleaves = [leave for leave in rawleaves if getattval(leave, 'begin') == position ]
        if candleaves != []:
            leaves.append(candleaves[0])
        else:
            uttid = getxsid(stree)
            sentence = getsentence(stree)
            settings.LOGGER.error(f'No leave found for {position} in {uttid}: {sentences}')
    return leaves


def mktoken2nodemap(tokens: List[Token], tree: SynTree) -> Dict[int, SynTree]:
    leaves = getuniqueleaves(tree)  # remove duplicate nodes due to indextransform
    # tokennodes = tree.xpath('.//node[@pt or @pos or @word]')
    # tokennodesdict = {int(getattval(n, 'begin')): n for n in tokennodes}
    noskiptokens = [token for token in tokens if not token.skip]
    if len(noskiptokens) == len(leaves):
        token_node_tuples = zip(noskiptokens, leaves)
        token2nodemap = {token.pos: node for token, node in token_node_tuples}
    else:
        settings.LOGGER.error(f'Token - Node mismatch in {str(noskiptokens)} v. {gettokenpos_str(tree)}')
        token2nodemap = {}
    return token2nodemap



def getqueryresult(syntree: SynTree, xpathquery: Optional[str] = None,
                   noxpathquery: Callable[[SynTree], List[str]] = None) -> Optional[str]:
    debug = False
    if debug:
        showtree(syntree, 'getqueryresults')
    if syntree is None:
        result = None
    else:
        if xpathquery is not None:
            results = syntree.xpath(xpathquery)
        elif noxpathquery is not None:
            results = noxpathquery(syntree)
        else:
            results = []
        if len(results) == 0:
            result = None
        elif len(results) > 1:
            result1 = results[0]
            result = number2intstring(result1)
            # issue a warning
        elif len(results) == 1:
            result1 = results[0]
            result = number2intstring(result1)
        else:
            result = None
    return result


def getattval_fallback(node: SynTree, att: str, fallback: str = '') -> str:
    """Gets the attribute from the current node or goes up in parents to find it

    Args:
        node (SynTree): node to search
        att (str): attribute name
        fallback (str): if nothing is found

    Returns:
        str: attribute value or fallback value if none is found
    """
    while True:
        if node is None:
            return fallback
        val = getattval(node, att)
        if val:
            return val
        parent = node.getparent()
        if parent is None:
            return fallback
        node = parent


def getnodeyield(syntree: SynTree) -> List[SynTree]:
    resultlist = []
    if syntree is None:
        return []
    else:
        for node in syntree.iter():
            if node.tag in ['node'] and 'pt' in node.attrib or 'pos' in node.attrib:
                resultlist.append(node)
        sortedresultlist = sorted(resultlist, key=lambda x: int(
            getattval_fallback(x, 'end', '9999')))
        return sortedresultlist


# deze herformuleren in termen van getnodeyield na testen
def getyield(syntree: SynTree) -> List[str]:
    resultlist = []
    if syntree is None:
        theyield = []
    else:
        for node in syntree.iter():
            if 'pt' in node.attrib or 'pos' in node.attrib:
                if 'word' in node.attrib and 'end' in node.attrib:
                    newel = (node.attrib['word'], int(node.attrib['end']))
                    resultlist.append(newel)
                else:
                    if 'word' not in node.attrib:
                        settings.LOGGER.error('No word in pt or pos node')
                    if 'end' not in node.attrib:
                        settings.LOGGER.error('No end in pt or pos node')
                    for el in node.attrib:
                        settings.LOGGER.info(
                            '{}\t{}'.format(el, node.attrib[el]))
        sortedresultlist = sorted(resultlist, key=lambda x: x[1])
        theyield = [w for (w, _) in sortedresultlist]
    return theyield


def parent(node: SynTree) -> Optional[SynTree]:
    pnodes = node.xpath('parent::node')
    if pnodes == []:
        result = None
    else:
        result = pnodes[0]
    return result


def is_left_sibling(node1: SynTree, node2: SynTree) -> bool:
    sameparent = parent(node1) == parent(node2)
    node1_end = getattval(node1, 'end')
    node2_end = getattval(node2, 'end')
    result = sameparent and node1_end < node2_end
    return result


def get_left_siblings(node: SynTree) -> List[SynTree]:
    thesiblings = node.xpath('../node')
    theleftsiblings = [s for s in thesiblings if is_left_sibling(s, node)]
    return theleftsiblings


def getmarkedutt(m: SynTree, syntree: SynTree) -> str:
    thewordlist = getyield(syntree)
    thepositions = getwordpositions(m, syntree)
    themarkedyield = getmarkedyield(thewordlist, thepositions)
    yieldstr = space.join(themarkedyield)
    return yieldstr


def mark(str: str) -> str:
    result = '*' + str + '*'
    return result


def getwordpositions(matchtree: SynTree, syntree: SynTree) -> List[Position]:
    # nothing special needs to be done for index nodes since they also have begin and end
    positions = []
    for node in matchtree.iter():
        if 'end' in node.attrib:
            positions.append(node.attrib['end'])
    result = [int(p) for p in positions]
    return result


def getmarkedyield(wordlist: List[str], positions: List[Position]) -> List[str]:
    pos = 1
    resultlist = []
    if 0 in positions:
        resultlist.append(mark(''))
    for w in wordlist:
        if pos in positions:
            resultlist.append(mark(w))
        else:
            resultlist.append(w)
        pos += 1
    return resultlist


# addmetadata was wrong and not used and has been commented out. use add_metadata instead
# def addmetadata(stree: SynTree, meta: Metadata) -> SynTree:
#     """
#     adds  meta of class Metadata to stree
#     :param stree:
#     :param meta: type Metadata
#     :return: stree
#     """
#     if stree is None:
#         result = stree
#     elif meta is None:
#         result = stree
#     else:
#         metadatanodes = stree.xpath('//metadata')
#         if metadatanodes == []:
#             metadatanode = etree.Element('metadata')
#             stree.append(metadatanode)
#         else:
#             metadatanode = metadatanodes[
#                 0]  # we append to the first metadata node if there would be multiple (which should not be the case)
#         metadatanode.append(meta)
#         result = stree
#     return result


def iswordnode(thenode: SynTree) -> bool:
    # result = 'pt' in thenode.attrib or 'pos' in thenode.attrib
    result = 'word' in thenode.attrib
    return result


def istrueclausalnode(thenode: SynTree) -> bool:
    thenodecat = getattval(thenode, 'cat')
    result1 = thenodecat in trueclausecats
    if result1:
        ssubfound = False
        for child in thenode:
            if getattval(child, 'cat') == 'ssub':
                ssubfound = True
                break
        result = ssubfound
    else:
        result = False
    return result


def iscompound(node: SynTree) -> bool:
    """
    The function *iscompound* determines whether a node is a node for a compound word.
    This is the case if the *lemma* attribute contains the compound separator
    *compoundsep*

    .. autodata:: sastadev.treebankfunctions::compoundsep
    """
    lemma = getattval(node, 'lemma')
    result = compoundsep in lemma
    return result


def isdiminutive(node: SynTree) -> bool:
    """
    The function *isdiminutive* checks whether *node* is  a node for diminutive word.
    This is the case if the attribute *graad* has the value *dim*.

    """
    graad = getattval(node, 'graad')
    result = graad == 'dim'
    return result


def issubstantivised_verb(node: SynTree) -> bool:
    """
    The function *issubstantivised_verb* checks whether a node is a node for a
    substantivised verb (i.e. if *pt* = *ww* and *positie* = *nom*)

    """
    nodept = getattval(node, 'pt')
    nodepositie = getattval(node, 'positie')
    result = nodept == 'ww' and nodepositie == 'nom'
    return result


def getsiblings(node: SynTree) -> List[SynTree]:
    """
    The function *getsiblings* returns the list of sibling nodes of *node*

    """
    parent = node.getparent()
    siblings = [n for n in parent if n != node]
    return siblings


def showtn(tokennode: SynTree) -> str:
    """requires the node to be a node for a token (word)"""
    if tokennode is None:
        result = ''
    else:
        word = getattval(tokennode, 'word')
        position = getattval(tokennode, 'end')
        result = position + word
    return result


def showtns(tokennodelist: List[SynTree]) -> str:
    result = space.join([showtn(tn) for tn in tokennodelist])
    return result


def all_lower_consonantsnode(node: SynTree) -> bool:
    """
    The function *all_lower_consonantsnode* checks whether *node* is a node for a word
    that consists of all lower case consonants.

    """
    word = getattval(node, 'word')
    result = all([c.islower() for c in word])
    result = result and allconsonants(word)
    return result


def sasta_long(node: SynTree) -> bool:
    """
    The function sasta_long checks whether the length of the *word* attribute of the
    node is greater or equal to *min_sasta_length*:

    .. autodata:: sastadev.treebankfunctions::min_sasta_length

    """
    word = getattval(node, 'word')
    result = len(word) >= min_sasta_length
    return result


def spec_noun(node: SynTree) -> bool:
    """
    The function *spec_noun* checks whether the node is node of *pt* *spec* which is a
    name or name part (as determined by the attributes *pos* and *frame*).

    """
    pt = getattval(node, 'pt')
    pos = getattval(node, 'pos')
    frame = getattval(node, 'frame')
    word = getattval(node, 'word')
    result = (pt == 'spec' and (
        pos == 'name' or frame.startswith('proper_name')))
    result = result and word[0].isupper()
    return result


def is_duplicate_spec_noun(node: SynTree) -> bool:
    """
    The function *is_duplicate_spec_noun* checks whether there is any duplicate of the
    word among its siblings (ignoring case).
    """
    siblings = getsiblings(node)
    result = True
    word = getattval(node, 'word')
    lcword = word.lower()
    for sibling in siblings:
        siblingword = getattval(sibling, 'word')
        lcsiblingword = siblingword.lower()
        result = result and lcword == lcsiblingword
    return result


def onbvnwdet(node: SynTree) -> bool:
    result = getattval(node, 'lemma') in potentialdet_onbvnws
    return result


# this function moved to tblex
# def asta_recognised_lexnode(node: SynTree) -> bool:
#     """
#     The function *asta_recognised_lexnode* determines whether *node* should count as a
#     lexical verb in the ASTA method.
#
#     This is the case if *pt* equals *ww* and the node is not a substantivised verb as
#     determined by the function *issubstantivised_verb*:
#
#     .. autofunction:: sastadev.treebankfunctions::issubstantivised_verb
#
#     """
#     if issubstantivised_verb(node):
#         result = False
#     else:
#         result = getattval(node, 'pt') == 'ww'
#     return result


def isspecdeeleigen(node: SynTree) -> bool:
    pt = getattval(node, 'pt')
    spectype = getattval(node, 'spectype')
    result = pt == 'spec' and spectype == 'deeleigeb'
    return result


def ismonthname(node: SynTree) -> bool:
    lemma = getattval(node, 'lemma')
    result = lemma in monthnames
    return result


# this function moved to tblex
# def asta_recognised_nounnode(node: SynTree) -> bool:
#     """
#     The function *asta_recognised_nounnode* determines whether *node* should count as a
#     noun in the ASTA method.
#
#     This is the case if
#
#     * either the node meets the conditions of *sasta_pseudonym*
#
#        .. autofunction:: sastadev.treebankfunctions::sasta_pseudonym
#
#     * or the node is part of name (pt = *spec*, spectype= *deeleigen*)
#
#        .. autofunction:: sastadev.treebankfunctions::isspecdeeleigen
#
#     * or the node is a month name (these are not always nouns in Alpino)
#
#        .. autofunction:: sastadev.treebankfunctions::ismonthname
#
#     * or the node meets the conditions of *spec_noun*
#
#        .. autofunction:: sastadev.treebankfunctions::spec_noun
#
#     * or the node meets the conditions of *is_duplicate_spec_noun*
#
#        .. autofunction:: sastadev.treebankfunctions::is_duplicate_spec_noun
#
#     * or the node meets the conditions of *sasta_long*
#
#        .. autofunction:: sastadev.treebankfunctions::sasta_long
#
#     * or the node meets the conditions of *recognised_wordnodepos*
#
#        .. autofunction:: sastadev.tblex::recognised_wordnodepos
#
#     * or the node meets the conditions of *recognised_lemmanodepos(node, pos)*
#
#        .. autofunction:: sastadev.treebankfunctions::recognised_lemmanodepos(node, pos)
#
#     However, the node should:
#
#     * neither consist of lower case consonants only, as determined by *all_lower_consonantsnode*:
#
#        .. autofunction:: sastadev.treebankfunctions::all_lower_consonantsnode
#
#     * nor satisfy the conditions of *short_nucl_n*:
#
#        .. autofunction:: sastadev.treebankfunctions::short_nucl_n
#
#     """
#
#     if issubstantivised_verb(node):
#         pos = 'ww'
#     else:
#         pos = 'n'
#     result = sasta_pseudonym(node)
#     result = result or isspecdeeleigen(node)
#     result = result or ismonthname(node)
#     result = result or spec_noun(node)
#     result = result or is_duplicate_spec_noun(node)
#     result = result or sasta_long(node)
#     result = result or recognised_wordnodepos(node, pos)
#     result = result or recognised_lemmanodepos(node, pos)
#     result = result and not (all_lower_consonantsnode(node))
#     result = result and not (short_nucl_n(node))
#     return result

# this function moved to tblex
# def asta_recognised_wordnode(node: SynTree) -> bool:
#     result = sasta_pseudonym(node)
#     result = result or spec_noun(node)
#     result = result or is_duplicate_spec_noun(node)
#     result = result or sasta_long(node)
#     result = result or recognised_wordnode(node)
#     result = result or recognised_lemmanode(node)
#     result = result or isnumber(node)
#     result = result and not (all_lower_consonantsnode(node))
#     result = result and not (short_nucl_n(node))
#     return result


def isnumber(node: SynTree) -> bool:
    word = getattval(node, 'word')
    thematch = numberre.match(word)
    result = thematch is not None
    return result


def sasta_short(inval: str) -> bool:
    """
    The function *sasta_short* determines whether the string *inval* is short, i.e,
    with a length smaller or equal than *sasta_short_length*:

    .. autodata:: sastadev.treebankfunctions::sasta_short_length

    """
    result = len(inval) <= sasta_short_length
    return result


def short_nucl_n(node: SynTree) -> bool:
    """
    The function *short_nucl_n* determines whether *node* is a node for a word with
    *pt* equal to *n*, relation *nucl*, and whose *word* attribute is short (as
    determined by the  function *sasta_short*)

    .. autofunction:: sastadev.treebankfunctions::sasta_short
    """
    pt = getattval(node, 'pt')
    rel = getattval(node, 'rel')
    word = getattval(node, 'word')
    result = pt == 'n' and rel == 'nucl' and sasta_short(word)
    return result


def sasta_pseudonym(node: SynTree) -> bool:
    """
    The function *sasta_pseudonym* determines whether the *word* attribute of *node* is a SASTA pseudonym.

    It uses the *pseudonymre* regular expression, which is created by joining
    the pseudonym regular expressions of the *pseudonym_patternlist* as alternatives. the
    pseudonym regular
    expressions have been created using the constant sasta_pseudonyms:

    .. autodata:: sastadev.anonymization::sasta_pseudonyms
       :noindex:

    .. autodata:: sastadev.anonymization::pseudonym_patternlist

    """
    word = getattval(node, 'word')
    match = pseudonymre.match(word)
    result = match is not None
    return result


nodeformat = '{}/{}{}'
nodeformatplus = nodeformat + '['


# @@need to add a variant that returns a string


def simpleshow(stree: SynTree, showchildren: bool = True, newline: bool = True) -> None:
    simpleshow2(stree, showchildren)
    if newline:
        print()


def simpleshow2(stree: SynTree, showchildren: bool = True) -> None:
    rel = getattval(stree, 'rel')
    cat = getattval(stree, 'cat')
    index = getattval(stree, 'index')
    indexstr = ':' + index if index != '' else ''
    begin = getattval(stree, 'begin')
    end = getattval(stree, 'end')
    theformat = nodeformatplus if showchildren else nodeformat
    if cat != '':
        print(theformat.format(rel, cat, indexstr), end=' ')
        if showchildren:
            for child in stree:
                simpleshow2(child)
            print(']', end=' ')
        else:
            print('{}-{}'.format(begin, end))
    elif getattval(stree, 'pt') != '':
        print(nodeformat.format(rel, showtn(stree), indexstr), end=' ')
    elif getattval(stree, 'pos') != '':
        print(nodeformat.format(rel, showtn(stree), indexstr), end=' ')
    else:
        index = getattval(stree, 'index')
        if index != '':
            print(nodeformat.format(rel, '', indexstr), end=' ')
        else:
            # print('top', end=' ')
            for child in stree:
                simpleshow2(child)
            # print(']', end=' ')


def showflatxml(elem: SynTree) -> str:
    """

    :param elem: xml element
    :return: string that represents the element and its immediate children
    """
    start = '<{}>'.format(elem.tag)
    end = '</{}>'.format(elem.tag)
    middle = ['<{}/>'.format(child.tag) for child in elem]
    middlestr = space.join(middle)
    result = start + middlestr + end
    return result


def uniquenodes(nodelist: List[SynTree]) -> List[SynTree]:
    """

    :param nodelist: list of nodes all from a single syntactic structure
    :return: nodelist without duplicates. Two nodes are considered duplicates if the begin and end attributes are identical
    """
    done = []
    resultlist = []
    for node in nodelist:
        begin = getattval(node, 'begin')
        end = getattval(node, 'end')
        cover = begin, end
        if cover not in done:
            resultlist.append(node)
            done.append(cover)
    return resultlist


# this does not take into account that the antecedent itself can contain an indexed node,
# which must be replaced by an antecedent that may itself contain an index node, etc.
def oldgetindexednodesmap(stree: SynTree) -> Dict[str, SynTree]:
    indexednodes = {}
    if stree is not None:
        for node in stree.iter():
            if 'index' in node.attrib and ('pt' in node.attrib or 'cat' in node.attrib or 'pos' in node.attrib):
                theindex = node.attrib['index']
                indexednodes[theindex] = node
    return indexednodes


def getindexednodesmap(basicdict: Dict[str, SynTree]) -> Dict[str, SynTree]:
    """

    :param basicdict: dictionary of index - SynTree items in which the syntactic structure can contain bare index nodes
    :return: a dictionary for each item in  *basicdict* in which the bare index nodes have been replaced by their antecedents

    The function *getindexednodesmap* creates a new dictionary for each item in *basicdict* in which the bare index nodes have been replaced by
    their antecedents by applying the function *expandtree*:

    .. autofunction:: sastadev.treebankfunctions::expandtree

    """
    newdict = {}
    for i, tree in basicdict.items():
        newdict[i] = expandtree(tree, basicdict, newdict)
    return newdict


def expandtree(tree: SynTree, basicdict: Dict[str, SynTree], newdict: Dict[str, SynTree]) -> Dict[str, SynTree]:
    """

    :param tree: input syntactic structure
    :param basicdict: dictionary with index - SynTree items where the syntactic structure can contain bare index nodes
    :param newdict: a dictionary, initially empty, that is filled by this function with index - SynTree items where the syntactic structure does not contain any bare index nodes
    :return: a syntactic structure based on *tree* in which all bare index nodes have been replaced by their antecedents that do not contain any bare index nodes.

    The function *expandtree* expands a syntactic structure as follows:

    * if the top node is a bare index node with index *theindex*:

       * it is replaced by the newdict[theindex] if *theindex* is in *newdict*
       * it is replaced by the expansion of basicdict[theindex] otherwise. This is a recursive call.
       This recursion cannot go on forever since a node with index *idx* cannot contain a node with index *idx*
       (the underlying type is a directed **acyclic** graph). Once this expansion has been created,
       the expansion is assigned to newdict[idx]

    * otherwise the function is called recursively to all children of the top node, creating a new child list, which is
      appended to a copy if the top node.

    """
    if bareindexnode(tree):
        theindex = getattval(tree, 'index')
        therel = getattval(tree, 'rel')
        if theindex in newdict:
            result = deepcopy(newdict[theindex])
            result.attrib['rel'] = therel
        else:
            result1 = expandtree(basicdict[theindex], basicdict, newdict)
            newdict[theindex] = result1
            result = deepcopy(newdict[theindex])
            result.attrib['rel'] = therel
    else:
        newtree = nodecopy(tree)
        for child in tree:
            newchild = expandtree(child, basicdict, newdict)
            newtree.append(newchild)
        result = newtree
    return result


def getbasicindexednodesmap(stree: SynTree) -> Dict[str, SynTree]:
    """

    :param stree: input syntactic structure
    :return: dictionary with index - SynTree items in which each SynTree is the antecedent for bare
     index  nodes with this index. These antecedents can contain bare index nodes themselves.

    The function *getbasicindexednodesmap* simply assigns a node that is not a bare index node with index *theindex* to
    the resulting dictionary *indexednodes* at key *theindex*.
    """
    indexednodes = {}
    if stree is not None:
        for node in stree.iter():
            if 'index' in node.attrib and not bareindexnode(node):
                theindex = node.attrib['index']
                indexednodes[theindex] = node
    return indexednodes


def nodecopy(node: SynTree) -> Optional[SynTree]:
    """
    The function *nodecopy* copies a node without its children
    :param node: node, an lxml.etree Element
    :return: a node with no children, otherwise a copy of the input node
    """
    if node is None:
        return None
    else:
        newnode = copy(node)
        for ch in newnode:
            newnode.remove(ch)
        return newnode


def bareindexnode(node: SynTree) -> bool:
    result = node.tag == 'node' and terminal(node) and 'index' in node.attrib and \
        'word' not in node.attrib and 'lemma' not in node.attrib and 'cat' not in node.attrib
    # print(props2str(get_node_props(node)), result, file=sys.stderr)
    return (result)


# herdefinieren want met UD hebben terminale nodes wel children (maar geen children met tag=node)


def terminal(node: SynTree) -> bool:
    result = isinstance(
        node, etree._Element) and node is not None and len(node) == 0
    return result


def oldindextransform(stree: SynTree) -> SynTree:
    """
    produces a new stree in which all index nodes are replaced by their antecedent nodes
    :param stree: input stree
    :return: stree with all index nodes replaced by the nodes of their antecedents
    """

    indexednodesmap = getindexednodesmap(stree)
    # for ind, tree in indexednodesmap.items():
    # print(ind)
    # etree.dump(tree)
    result = indextransform2(stree, indexednodesmap)
    return result


def indextransform(stree: SynTree) -> SynTree:
    """
    :param stree: input stree
    :return: stree with all index nodes replaced by the nodes of their antecedents

    The function *indextransform* produces a new stree in which all index nodes are replaced by their antecedent nodes.
    It first gathers the antecedents of bare index nodes in a dictionary (*basicindexednodesmap*) of index-SynTree
    items by means of the function *getbasicindexednodesmap*.

    .. autofunction:: sastadev.treebankfunctions::getbasicindexednodesmap

    The antecedents can contain bare index nodes themselves. So, in a second step, each antecedent is expanded
    so that bare index nodes are replaced by their antecedents. This is done by the function *getindexednodesmap*,
    which creates a new dictionary of index-SynTree items called *indexnodesmap*

    .. autofunction:: sastadev.treebankfunctions::getindexednodesmap

    Finally, the input tree is transformed by the function *indextransform2*, which uses  *indexnodesmap*:

    .. autofunction:: sastadev.treebankfunctions::indextransform2

    """

    basicindexednodesmap = getbasicindexednodesmap(stree)
    # for ind, tree in indexednodesmap.items():
    # print(ind)
    # etree.dump(tree)
    indexnodesmap = getindexednodesmap(basicindexednodesmap)
    result = indextransform2(stree, indexnodesmap)
    return result


# deze robuust maken tegen andere nodes dan node (metadata, alpino_ds etc)
# waarschijnlijk is node.tag == 'node'in baseindexnode voldoende
def indextransform2(stree: SynTree, indexednodesmap: Dict[str, SynTree]) -> Optional[SynTree]:
    """
    The function *indextransform2* takes as input a syntactic structure *stree* and an index-SynTree dictionary.
    It creates a new tree in which each bare index node in *stree* with index *i* is replaced by its antecedent
    (i.e. indexednodesmap[i]), except for the grammatical relation attribute *rel*.

    :param stree: input syntactic structure
    :param indexednodesmap: dictionary with index - SynTree items. No bare index nodes occur in the syntactic structures
    :return:  new tree in which each bare index node in *stree* with index *i* is replaced by its antecedent (i.e. indexednodesmap[i]), except for the grammatical relation attribute *rel*.

    """
    if stree is None:
        return None
    else:
        if bareindexnode(stree):
            theindex = getattval(stree, 'index')
            therel = getattval(stree, 'rel')
            newstree = deepcopy(indexednodesmap[theindex])
            newstree.attrib['rel'] = therel
            # simpleshow(newstree)
            # print()
        else:
            newstree = nodecopy(stree)
            # simpleshow(newstree)
            # print(id(stree))
            # print(id(newstree))
            # print(len(newstree))
            # print(id(newstree.getparent()))
            # print(id(None))
            for child in stree:
                newchild = indextransform2(child, indexednodesmap)
                newstree.append(newchild)

        return newstree


def getstree(fullname: FileName) -> Optional[SynTree]:
    try:
        thefile = open(fullname, 'r', encoding='utf8')
    except FileNotFoundError as e:
        settings.LOGGER.error('File not found: {}'.format(e))
        return None
    except etree.ParseError as e:
        settings.LOGGER.error('Parse Error: {}; file: {}'.format(e, fullname))
        return None
    except OSError as e:
        settings.LOGGER.error('OS Error: {}; file: {}'.format(e, fullname))
        return None
    except Exception:
        settings.LOGGER.error(
            'Error: Unknown error in file {}'.format(fullname))
        return None

    with thefile:
        try:
            tree = etree.parse(thefile)
        except etree.ParseError as e:
            settings.LOGGER.error(
                'Parse Error: {}; file: {}'.format(e, fullname))
            return None
        except UnicodeDecodeError as e:
            settings.LOGGER.error(
                'Unicode error: {} in file {}'.format(e, fullname))
            try:
                windowsfile = open(fullname, 'r')
                tree = etree.parse(windowsfile)
            except ValueError as e:
                settings.LOGGER.error(
                    'Char Descoding Error: {}; file: {}'.format(e, fullname))
                return None
            except etree.ParseError as e:
                settings.LOGGER.error(
                    'Parse Error: {}; file: {}'.format(e, fullname))
                return None
            else:
                return tree
        else:
            return tree


streestrings = {}
streestrings[1] = """
<alpino_ds version="1.6">
  <parser cats="1" skips="5" />
  <node begin="0" cat="top" end="8" id="0" rel="top">
    <node begin="0" conjtype="neven" end="1" frame="complementizer(root)" his="robust_skip" id="1" lcat="--" lemma="en" pos="comp" postag="VG(neven)" pt="vg" rel="--" root="en" sc="root" sense="en" word="en"/>
    <node begin="1" end="2" frame="--" genus="zijd" getal="ev" graad="basis" his="robust_skip" id="2" lcat="--" lemma="uhm" naamval="stan" ntype="soort" pos="--" postag="N(soort,ev,basis,zijd,stan)" pt="n" rel="--" root="uhm" sense="uhm" word="uhm"/>
    <node begin="2" conjtype="neven" end="3" frame="conj(en)" his="robust_skip" id="3" lcat="--" lemma="en" pos="vg" postag="VG(neven)" pt="vg" rel="--" root="en" sense="en" word="en"/>
    <node begin="3" end="4" frame="--" genus="zijd" getal="ev" graad="basis" his="robust_skip" id="4" lcat="--" lemma="uhm" naamval="stan" ntype="soort" pos="--" postag="N(soort,ev,basis,zijd,stan)" pt="n" rel="--" root="uhm" sense="uhm" word="uhm"/>
    <node begin="4" case="nom" def="def" end="5" frame="pronoun(nwh,thi,sg,de,nom,def)" gen="de" genus="masc" getal="ev" his="robust_skip" id="5" lcat="--" lemma="hij" naamval="nomin" num="sg" pdtype="pron" per="thi" persoon="3" pos="pron" postag="VNW(pers,pron,nomin,vol,3,ev,masc)" pt="vnw" rel="--" root="hij" sense="hij" status="vol" vwtype="pers" wh="nwh" word="hij"/>
    <node begin="5" cat="smain" end="8" id="6" rel="--">
      <node begin="5" case="nom" def="def" end="6" frame="pronoun(nwh,thi,sg,de,nom,def)" gen="de" genus="masc" getal="ev" his="normal" his_1="normal" id="7" lcat="np" lemma="hij" naamval="nomin" num="sg" pdtype="pron" per="thi" persoon="3" pos="pron" postag="VNW(pers,pron,nomin,vol,3,ev,masc)" pt="vnw" rel="su" rnum="sg" root="hij" sense="hij" status="vol" vwtype="pers" wh="nwh" word="hij"/>
      <node begin="6" end="7" frame="verb(unacc,sg_heeft,intransitive)" his="normal" his_1="normal" id="8" infl="sg_heeft" lcat="smain" lemma="zijn" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="ben" sc="intransitive" sense="ben" stype="declarative" tense="present" word="is" wvorm="pv"/>
      <node begin="7" end="8" frame="adverb" his="normal" his_1="normal" id="9" lcat="advp" lemma="nogal" pos="adv" postag="BW()" pt="bw" rel="mod" root="nogal" sense="nogal" word="nogal"/>
    </node>
  </node>
  <sentence sentid="32">en uhm en uhm hij hij is nogal</sentence>
<metadata>
<meta type="text" name="charencoding" value="UTF8" />
<meta type="text" name="childage" value="" />
<meta type="text" name="childmonths" value="" />
<meta type="text" name="comment" value="##META text samplenaam = ASTA-06" />
<meta type="text" name="session" value="ASTA_sample_06" />
<meta type="text" name="origutt" value="en uhm en uhm hij hij is nogal " />
<meta type="text" name="parsefile" value="Unknown_corpus_ASTA_sample_06_u00000000046.xml" />
<meta type="text" name="speaker" value="PMA" />
<meta type="int" name="uttendlineno" value="85" />
<meta type="int" name="uttid" value="32" />
<meta type="int" name="uttstartlineno" value="85" />
<meta type="text" name="name" value="pma" />
<meta type="text" name="SES" value="" />
<meta type="text" name="age" value="" />
<meta type="text" name="custom" value="" />
<meta type="text" name="education" value="" />
<meta type="text" name="group" value="" />
<meta type="text" name="language" value="nld" />
<meta type="text" name="months" value="" />
<meta type="text" name="role" value="Other" />
<meta type="text" name="sex" value="" />
<meta type="text" name="xsid" value="32" />
<meta type="int" name="uttno" value="46" />
</metadata>
</alpino_ds>
"""

streestrings[2] = """
<alpino_ds version="1.6">
  <parser cats="3" skips="0" />
  <node begin="0" cat="top" end="17" id="0" rel="top">
    <node begin="0" cat="du" end="16" id="1" rel="--">
      <node begin="0" cat="smain" end="3" id="2" rel="dp">
        <node begin="0" case="nom" def="def" end="1" frame="pronoun(nwh,fir,sg,de,nom,def)" gen="de" getal="ev" his="normal" his_1="normal" id="3" lcat="np" lemma="ik" naamval="nomin" num="sg" pdtype="pron" per="fir" persoon="1" pos="pron" postag="VNW(pers,pron,nomin,vol,1,ev)" pt="vnw" rel="su" rnum="sg" root="ik" sense="ik" status="vol" vwtype="pers" wh="nwh" word="ik"/>
        <node begin="1" end="2" frame="verb(hebben,sg1,transitive_ndev)" his="normal" his_1="normal" id="4" infl="sg1" lcat="smain" lemma="hebben" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="heb" sc="transitive_ndev" sense="heb" stype="declarative" tense="present" word="heb" wvorm="pv"/>
        <node begin="2" case="both" def="indef" end="3" frame="pronoun(nwh,thi,sg,both,both,indef,strpro)" gen="both" his="normal" his_1="normal" id="5" lcat="np" lemma="één" num="sg" numtype="hoofd" per="thi" pos="pron" positie="vrij" postag="TW(hoofd,vrij)" pt="tw" rel="obj1" rnum="sg" root="één" sense="één" special="strpro" wh="nwh" word="een"/>
      </node>
      <node begin="3" cat="smain" end="6" id="6" rel="dp">
        <node begin="3" case="nom" def="def" end="4" frame="pronoun(nwh,fir,sg,de,nom,def)" gen="de" getal="ev" his="normal" his_1="normal" id="7" lcat="np" lemma="ik" naamval="nomin" num="sg" pdtype="pron" per="fir" persoon="1" pos="pron" postag="VNW(pers,pron,nomin,vol,1,ev)" pt="vnw" rel="su" rnum="sg" root="ik" sense="ik" status="vol" vwtype="pers" wh="nwh" word="ik"/>
        <node begin="4" end="5" frame="verb(hebben,sg1,transitive_ndev)" his="normal" his_1="normal" id="8" infl="sg1" lcat="smain" lemma="hebben" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="heb" sc="transitive_ndev" sense="heb" stype="declarative" tense="present" word="heb" wvorm="pv"/>
        <node begin="5" case="both" def="indef" end="6" frame="pronoun(nwh,thi,sg,both,both,indef,strpro)" gen="both" his="normal" his_1="normal" id="9" lcat="np" lemma="één" num="sg" numtype="hoofd" per="thi" pos="pron" positie="vrij" postag="TW(hoofd,vrij)" pt="tw" rel="obj1" rnum="sg" root="één" sense="één" special="strpro" wh="nwh" word="een"/>
      </node>
      <node begin="6" cat="smain" end="16" id="10" rel="dp">
        <node begin="6" case="nom" def="def" end="7" frame="pronoun(nwh,fir,sg,de,nom,def)" gen="de" getal="ev" his="normal" his_1="normal" id="11" lcat="np" lemma="ik" naamval="nomin" num="sg" pdtype="pron" per="fir" persoon="1" pos="pron" postag="VNW(pers,pron,nomin,vol,1,ev)" pt="vnw" rel="su" rnum="sg" root="ik" sense="ik" status="vol" vwtype="pers" wh="nwh" word="ik"/>
        <node begin="7" end="8" frame="verb(hebben,sg1,transitive_ndev)" his="normal" his_1="normal" id="12" infl="sg1" lcat="smain" lemma="hebben" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="heb" sc="transitive_ndev" sense="heb" stype="declarative" tense="present" word="heb" wvorm="pv"/>
        <node begin="8" cat="np" end="16" id="13" rel="obj1">
          <node begin="8" end="9" frame="determiner(een)" his="normal" his_1="normal" id="14" infl="een" lcat="detp" lemma="een" lwtype="onbep" naamval="stan" npagr="agr" pos="det" postag="LID(onbep,stan,agr)" pt="lid" rel="det" root="een" sense="een" word="een"/>
          <node begin="9" end="10" frame="noun(de,count,bare_meas)" gen="de" genus="zijd" getal="ev" graad="basis" his="normal" his_1="normal" id="15" lcat="np" lemma="man" naamval="stan" ntype="soort" num="bare_meas" pos="noun" postag="N(soort,ev,basis,zijd,stan)" pt="n" rel="hd" rnum="sg" root="man" sense="man" word="man"/>
          <node begin="10" cat="rel" end="16" id="16" rel="mod">
            <node begin="10" cat="pp" end="12" id="17" index="1" rel="rhd">
              <node begin="10" end="11" frame="preposition(met,[mee,[en,al]])" his="normal" his_1="normal" id="18" lcat="pp" lemma="met" pos="prep" postag="VZ(init)" pt="vz" rel="hd" root="met" sense="met" vztype="init" word="met"/>
              <node begin="11" case="obl" end="12" frame="rel_pronoun(both,obl)" gen="both" getal="getal" his="normal" his_1="normal" id="19" lcat="np" lemma="wie" naamval="stan" pdtype="pron" persoon="3p" pos="pron" postag="VNW(vb,pron,stan,vol,3p,getal)" pt="vnw" rel="obj1" rnum="sg" root="wie" sense="wie" status="vol" vwtype="vb" wh="rel" word="wie"/>
            </node>
            <node begin="10" cat="ssub" end="16" id="20" rel="body">
              <node begin="12" case="nom" def="def" end="13" frame="pronoun(nwh,fir,sg,de,nom,def)" gen="de" getal="ev" his="normal" his_1="normal" id="21" index="2" lcat="np" lemma="ik" naamval="nomin" num="sg" pdtype="pron" per="fir" persoon="1" pos="pron" postag="VNW(pers,pron,nomin,vol,1,ev)" pt="vnw" rel="su" rnum="sg" root="ik" sense="ik" status="vol" vwtype="pers" wh="nwh" word="ik"/>
              <node begin="13" end="14" frame="verb(hebben,modal_not_u,modifier(aux(inf)))" his="normal" his_1="normal" id="22" infl="modal_not_u" lcat="ssub" lemma="willen" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="wil" sc="modifier(aux(inf))" sense="wil" tense="present" word="wil" wvorm="pv"/>
              <node begin="10" cat="inf" end="16" id="23" rel="vc">
                <node begin="12" end="13" id="24" index="2" rel="su"/>
                <node begin="14" buiging="zonder" end="15" frame="verb(zijn,inf(no_e),aux(inf))" his="normal" his_1="normal" id="25" infl="inf(no_e)" lcat="inf" lemma="gaan" pos="verb" positie="vrij" postag="WW(inf,vrij,zonder)" pt="ww" rel="hd" root="ga" sc="aux(inf)" sense="ga" word="gaan" wvorm="inf"/>
                <node begin="10" cat="inf" end="16" id="26" rel="vc">
                  <node begin="10" end="12" id="27" index="1" rel="pc"/>
                  <node begin="12" end="13" id="28" index="2" rel="su"/>
                  <node begin="15" buiging="zonder" end="16" frame="verb(zijn,inf,pc_pp(met))" his="normal" his_1="normal" id="29" infl="inf" lcat="inf" lemma="trouwen" pos="verb" positie="vrij" postag="WW(inf,vrij,zonder)" pt="ww" rel="hd" root="trouw" sc="pc_pp(met)" sense="trouw-met" word="trouwen" wvorm="inf"/>
                </node>
              </node>
            </node>
          </node>
        </node>
      </node>
    </node>
    <node begin="16" end="17" frame="--" genus="zijd" getal="ev" graad="basis" his="skip" id="30" lcat="--" lemma="uhm" naamval="stan" ntype="soort" pos="--" postag="N(soort,ev,basis,zijd,stan)" pt="n" rel="--" root="uhm" sense="uhm" word="uhm"/>
  </node>
  <sentence sentid="29">ik heb een ik heb een ik heb een man met wie ik wil gaan trouwen uhm</sentence>
<metadata>
<meta type="text" name="charencoding" value="UTF8" />
<meta type="text" name="childage" value="" />
<meta type="text" name="childmonths" value="" />
<meta type="text" name="comment" value="##META text samplenaam = ASTA-06" />
<meta type="text" name="session" value="ASTA_sample_06" />
<meta type="text" name="origutt" value="ik heb een ik heb een ik heb een man met wie ik wil gaan trouwen uhm " />
<meta type="text" name="parsefile" value="Unknown_corpus_ASTA_sample_06_u00000000042.xml" />
<meta type="text" name="speaker" value="PMA" />
<meta type="int" name="uttendlineno" value="78" />
<meta type="int" name="uttid" value="29" />
<meta type="int" name="uttstartlineno" value="78" />
<meta type="text" name="name" value="pma" />
<meta type="text" name="SES" value="" />
<meta type="text" name="age" value="" />
<meta type="text" name="custom" value="" />
<meta type="text" name="education" value="" />
<meta type="text" name="group" value="" />
<meta type="text" name="language" value="nld" />
<meta type="text" name="months" value="" />
<meta type="text" name="role" value="Other" />
<meta type="text" name="sex" value="" />
<meta type="text" name="xsid" value="29" />
<meta type="int" name="uttno" value="42" />
</metadata>
</alpino_ds>
"""

strees = {}
for el in streestrings:
    strees[el] = etree.fromstring(streestrings[el])


def test() -> None:
    for el in strees:
        stree = strees[el]
        lmc = lastmainclauseof(stree)
        print(getmarkedutt(lmc, stree))


def getsentid(stree: SynTree) -> UttId:
    sentidlist = stree.xpath(sentidxpath)
    if sentidlist == []:
        settings.LOGGER.error('Missing sentid')
        result = 'None'
    else:
        result = str(sentidlist[0])
    return result


def testindextransform() -> None:
    for el in strees:
        stree = strees[el]
        print(el)
        simpleshow(stree)
        newstree = indextransform(stree)
        simpleshow(newstree)


def getyieldstr(stree: SynTree) -> str:
    theyield = getyield(stree)
    theyieldstr = space.join(theyield)
    return theyieldstr


def adaptsentence(stree: SynTree) -> SynTree:
    # adapt the sentence
    # find the sentence element's parent and its index
    sentid = getsentid(stree)
    sentencenode = stree.find('.//sentence')
    if sentencenode is None:
        settings.LOGGER.ERROR(
            'No sentence element found for stree with sentid={}'.format(sentid))
        return stree
    sentencenodeparent = sentencenode.getparent()
    sentencenodeindex = sentencenodeparent.index(sentencenode)
    sentencenodeparent.remove(sentencenode)
    # del sentencenodeparent[sentencenodeindex]
    theyield = getyield(stree)
    theyieldstr = space.join(theyield)
    newsentence = etree.Element('sentence')
    newsentence.text = theyieldstr
    newsentence.attrib['sentid'] = sentid
    sentencenodeparent.insert(sentencenodeindex, newsentence)
    return stree


def transplant_node(node1: SynTree, node2: SynTree, stree: SynTree) -> SynTree:
    """
    replace node1 by node2 in stree
    Only do so if node1 and node2 have no children and if their spans are identical
    :param node1: node to be replaced in stree
    :param node2: node to replace node1 in stree
    :param stree: tree in which the replacement takes place
    :return: the stree in which the input parameter is modified
    """
    # find the parent of node1
    # determine the index of node1
    sentid = getsentid(stree)
    parentindex = get_parentandindex(node1, stree)
    if parentindex is None:
        result = stree
    else:
        parent, index = parentindex
        # settings.LOGGER.debug(simpleshow(parent))
        del parent[index]
        # settings.LOGGER.debug(simpleshow(parent))
        parent.insert(index, node2)
        # settings.LOGGER.debug(simpleshow(parent))
        result = stree
        # settings.LOGGER.debug(simpleshow(stree))

    # adapt the sentence
    # find the sentence element's parent and its index
    sentencenode = stree.find('.//sentence')
    sentencenodeparent = sentencenode.getparent()
    sentencenodeindex = sentencenodeparent.index(sentencenode)
    del sentencenodeparent[sentencenodeindex]
    theyield = getyield(stree)
    theyieldstr = space.join(theyield)
    newsentence = etree.Element('sentence')
    newsentence.text = theyieldstr
    newsentence.attrib['sentid'] = sentid
    sentencenodeparent.insert(sentencenodeindex, newsentence)

    return stree


def get_parentandindex(node: SynTree, stree: SynTree) -> Optional[Tuple[SynTree, int]]:
    """

    :param node: node to find the parent of
    :param stree: stree to find the parent of node in
    :return: (parentnode::node, index::int) or None
    """

    nodespan = getspan(node)
    idx = 0
    for child in stree:
        childspan = getspan(child)
        if childspan == nodespan:
            return (stree, idx)
        else:
            chresult = get_parentandindex(node, child)
            if chresult is not None:
                return chresult
        idx += 1
    return None


def getspan(node: SynTree) -> Span:
    nodebegin = getattval(node, 'begin')
    nodeend = getattval(node, 'end')
    nodespan = (nodebegin, nodeend)
    return nodespan


def lbrother(node: SynTree, tree: SynTree) -> Optional[SynTree]:
    nodebegin = getattval(node, 'begin')

    def condition(n): return getattval(n, 'end') == nodebegin

    result = findfirstnode(tree, condition)
    return result


def rbrother(node: SynTree, tree: SynTree) -> Optional[SynTree]:
    nodeend = getattval(node, 'end')

    def condition(n): return getattval(n, 'begin') == nodeend

    result = findfirstnode(tree, condition)
    return result


def infl_lbrother(node: SynTree, tree: SynTree) -> Optional[SynTree]:
    """
    :param node: the node for the relevant word
    :param tree: the syntactic structure that contains *node*
    :return: The function *infl_lbrother* returns the node for the word that immediately precedes the word for *node* if there is one, otherwise None
    """
    nodeyield = getnodeyield(tree)
    for i, n in enumerate(nodeyield):
        if nodeyield[i] == n and i > 0:
            return nodeyield[i - 1]
    return None


def infl_rbrother(node: SynTree, tree: SynTree) -> Optional[SynTree]:
    """
    :param node: the node for the relevant word
    :param tree: the syntactic structure that contains *node*
    :return: The function *infl_lbrother* returns the node for the word that immediately follows the word for *node* if there is one, otherwise None
    """
    nodeyield = getnodeyield(tree)
    for i, n in enumerate(nodeyield):
        if nodeyield[i] == n and i < len(nodeyield) - 1:
            return nodeyield[i + 1]
    return None


def findfirstnode(tree: SynTree, condition: Callable[[SynTree], bool]) -> Optional[SynTree]:
    if condition(tree):
        return tree
    else:
        for child in tree:
            result = findfirstnode(child, condition)
            if result is not None:
                return result
    return None


def hasnominativehead(node: SynTree) -> bool:
    hd = find1(node, './node[@rel="hd"]')
    cnjs = node.xpath('./node[@rel="cnj"]')  # coordinations
    if cnjs != []:
        result = any([hasnominativehead(cnj) for cnj in cnjs])
    elif hd is not None:
        result = getattval(hd, 'naamval') == 'nomin'
    else:
        result = False
    return result

def nominal(node: SynTree) -> bool:
    pt = getattval(node, 'pt')
    cat = getattval(node, 'cat')
    if cat != '':
        result = cat == 'np'
    elif pt != '':
        result = pt in ['n', 'vnw']
    else:
        result = False
    return result


def decomposetree(tree: SynTree) -> Tuple[SynTree, SynTree, SynTree, SynTree, SynTree]:
    metadata, sentence, comments, nod, parser = None, None, None, None, None
    for child in tree:
        if child.tag == 'metadata':
            metadata = child
        elif child.tag == 'sentence':
            sentence = child
        elif child.tag == 'comments':
            comments = child
        elif child.tag == 'node':
            node = child
        elif child.tag == 'parser':
            parser = child
        else:
            settings.LOGGER.error(
                'Unknown tag encountered in tree: {}'.format(child.tag))
    return parser, metadata, node, sentence, comments


comma = ','


def str2list(liststr: str, sep: str = comma) -> List[str]:
    bareliststr = liststr[1:-1]
    rawlist = bareliststr.split(sep)
    cleanlist = [x.strip() for x in rawlist]
    return cleanlist


def strliststr2list(liststr: str, sep: str = comma) -> List[str]:
    bareliststr = liststr[1:-1]
    rawlist = bareliststr.split(sep)
    cleanlist = [x.strip()[1:-1] for x in rawlist]
    return cleanlist


def find1(tree: SynTree, xpathquery: str) -> Optional[SynTree]:
    if tree is None:
        return None
    results = tree.xpath(xpathquery)
    if results == []:
        result = None
    else:
        result = results[0]
    return result


def getxmetatreepositions(tree: SynTree, xmetaname: str, poslistname: str = 'annotationposlist') -> List[PositionStr]:
    query = ".//xmeta[@name='{}']".format(xmetaname)
    xmeta = find1(tree, query)
    if xmeta is None:
        return []
    annposstr = xmeta.get(poslistname)
    annposlist = str2list(annposstr)
    cleantok = find1(tree, './/xmeta[@name="cleanedtokenpositions"]')
    if cleantok is None:
        return []
    tokliststr = cleantok.get('value')
    toklist = str2list(tokliststr)
    result = [str(toklist.index(pos)) for pos in annposlist if pos in toklist]
    return result


# topendxpath = './/node[@cat="top"]/@end'
wordnodemodel = './/node[(@word or (not(@word) and not(@cat) and @index)) and @begin="{}"]'
purewordnodemodel = './/node[@word and @begin="{}"]'


def gettokposlist(tree: SynTree) -> List[PositionStr]:
    cleantok = find1(tree, './/xmeta[@name="cleanedtokenpositions"]')
    if cleantok is None:
        return []
    tokliststr = cleantok.get('value')
    toklist = str2list(tokliststr)
    result = [str(pos) for pos in toklist]
    return result


# origuttpos2treepos
def gettreepos(origpos: PositionStr, reverseindex: List[PositionStr]) -> PositionStr:
    if origpos in reverseindex:
        result = str(reverseindex.index(origpos))
    else:
        settings.LOGGER.error(
            'origpos {} not in reverseindex: {}'.format(origpos, reverseindex))
        result = str(0)
    return result


def deletewordnode(tree: SynTree, begin: Position, wordsonly=False) -> Optional[SynTree]:
    newtree = deepcopy(tree)
    if newtree is None:
        return newtree
    else:
        if wordsonly:
            wordnodexpath = purewordnodemodel.format(str(begin))
        else:
            wordnodexpath = wordnodemodel.format(str(begin))
        thenode = find1(newtree, wordnodexpath)
        if thenode is not None:
            thenode.getparent().remove(thenode)
        # renumber begins and ends must be done outside this functions when all deletions have been done;
        # updatebeginend(newtree, begin)

        # adapt the cleantokenisation
        # done outside this function

        # adapt the sentence: do this after all deletions
        # newtree = adaptsentence(newtree)

        return newtree


def showtree(tree: SynTree, text: Optional[str] = None) -> None:
    if text is not None:
        print(text)
    if tree is not None:
        etree.dump(tree, pretty_print=True)
    else:
        print('None')


def deletechildlessparent(thenode: SynTree) -> None:
    """
    deletes thenode if it has no children, and if its parent is childless after that, applies itself to the parent
    :param thenode:
    :return:
    """
    if list(thenode) == []:
        theparent = thenode.getparent()
        theparent.remove(thenode)
        deletechildlessparent(theparent)


def olddeletewordnodes(tree: SynTree, begins: List[Position]) -> Optional[SynTree]:
    # print('tree:')
    # etree.dump(tree, pretty_print=True)
    newtree = deepcopy(tree)
    # print('newtree:')
    # etree.dump(newtree, pretty_print=True)
    if newtree is None:
        return newtree
    else:
        # wordnodexpath = wordnodemodel.format(str(begin))
        thenodes = []
        for begin in begins:
            thenodes += newtree.xpath(wordnodemodel.format(str(begin)))
        for thenode in thenodes:
            if thenode is not None:
                theparent = thenode.getparent()
                theparent.remove(thenode)
                # if the parent has no sons left, it should be deleted as well
                deletechildlessparent(theparent)
                children = [n for n in theparent]
                (minbegin, maxend) = getbeginend(children)
                theparent.attrib['begin'] = minbegin
                theparent.attrib['end'] = maxend

        #
        # renumber begins and ends ;
        # normalisebeginend(newtree) temporarily put off

        # adapt the cleantokenisation
        # done outside this function

        # adapt the sentence
        newtree = adaptsentence(newtree)

        return newtree


# redefine: no children with tag == 'node'  (because of UD extensions )


def childless(node: SynTree):
    children = [ch for ch in node]
    result = children == []
    return result


def deletewordnodes(tree: SynTree, begins: List[Position], wordsonly=False) -> SynTree:
    newtree = deepcopy(tree)
    newtree = deletewordnodes2(newtree, begins, wordsonly=wordsonly)
    newtree = adaptsentence(newtree)
    return newtree


def deletewordnodes2(tree: SynTree, begins: List[Position], wordsonly=False) -> Optional[SynTree]:
    if tree is None:
        return tree
    for child in tree:
        if child.tag == 'node':
            newchild = deletewordnodes2(child, begins, wordsonly=wordsonly)
        else:
            newchild = child
    for child in tree:
        if child.tag == 'node':
            childbegin = getattval(child, 'begin')
            childbeginint = int(childbegin)
            childisaword = 'word' in child.attrib
            childmustgo = childisaword if wordsonly else True
            if childbeginint in begins and childless(child) and childmustgo:
                tree.remove(child)
            # if its children have been deleted earlier
            elif 'cat' in child.attrib and childless(child):
                tree.remove(child)
    # tree  begin en end bijwerken
    if tree.tag == 'node':
        newchildren = [n for n in tree]
        if newchildren != []:
            (minbegin, maxend) = getbeginend(newchildren)
            tree.attrib['begin'] = minbegin
            tree.attrib['end'] = maxend
    return tree


def olddeletewordnodes2(tree: SynTree, begins: List[Position]):
    if tree is None:
        return tree
    else:
        for child in tree:
            newchild = deletewordnodes2(child, begins)
        if tree.tag == 'node':
            nodebegin = getattval(tree, 'begin')
            children = [child for child in tree]
            if int(nodebegin) in begins:  # only words and indexnodes can be deleted
                theparent = tree.getparent()
                if theparent is not None:
                    if children == []:
                        theparent.remove(tree)
                        # if the parent has no sons left, it should be deleted as well
                        deletechildlessparent(theparent)
                    if theparent.tag == 'node':
                        newchildren = [n for n in theparent]
                        (minbegin, maxend) = getbeginend(newchildren)
                        theparent.attrib['begin'] = minbegin
                        theparent.attrib['end'] = maxend
        return tree


def getorigutt(stree: SynTree) -> Optional[str]:
    origuttlist = stree.xpath(origuttxpath)
    if origuttlist == []:
        origutt = None
    else:
        origutt = origuttlist[0]
    return origutt


def treeinflate(stree: SynTree, start: int = inflate_start, inc: int = inflate_step) -> None:
    """
    The function *treeinflate* adapts the input tree *stree* in such a way that:

    * for word nodes: the int value of the *begin* attribute  (ib) is changed to str(newib = start + ib  *
    inc), **code stil has to be adapted to this**
    and the value of the *end* attribute to str(newib + 1)
    * for phrasal nodes: new values for *begin* and *end* are computed by the function *getbeginend*
    * for other nodes: the same as  for word nodes

    The parameters of this function are:

    * stree: input syntactic structure, which is modified
    * start: not used yet (see below)) (default value = 10)
    * inc: increment, by default set to 10 (not used yet, see below)

    and it returns *None*.

    **Remark** This should be changed for words so that newib = start + (ib * inc) and
    newie =  newib + 1

    """
    # fatstree = deepcopy(stree)
    if stree is None:
        pass
    else:
        for child in stree:
            treeinflate(child, start, inc)
        children = [ch for ch in stree]
        if stree.tag == 'node':
            ib = int(getattval(stree, 'begin'))
            ie = int(getattval(stree, 'end'))
            newib = (ib + 1) * 10
            stree.attrib['begin'] = str(newib)
            if iswordnode(stree):
                stree.attrib['end'] = str(newib + 1)
            elif 'cat' in stree.attrib:
                (b, e) = getbeginend(children)
                stree.attrib['begin'] = b
                stree.attrib['end'] = e
            else:
                stree.attrib['begin'] = str((ib + 1) * 10)
                stree.attrib['end'] = str((ie * 10) + 1)


def deflate(stree: SynTree) -> SynTree:
    newstree = deepcopy(stree)
    deflate2(newstree)
    return newstree

def deflate2(stree: SynTree):
    if stree.tag == 'node':
        ib = int(getattval(stree, 'begin'))
        ie = int(getattval(stree, 'end'))
        newib = (ib //10) - 1
        stree.attrib['begin'] = str(newib)
        newie = (ie - 1) // 10
        stree.attrib['end'] = str(newie)
    for child in stree:
            deflate2(child)


def isidentitymap(dct: Dict[Any, Any]) -> bool:
    result = all([key == value for key, value in dct.items()])
    return result


def updatetokenpos(stree: SynTree, tokenposdict: PositionMap) -> Optional[SynTree]:
    if stree is None:
        return stree
    if isidentitymap(tokenposdict):
        return stree
    resulttree = deepcopy(stree)
    resulttree = updatetokenpos2(resulttree, tokenposdict)
    finaltree = updateindexnodes(resulttree)

    return finaltree


def updatetokenpos2(node: SynTree, tokenposdict: PositionMap):
    if node is None:
        return node
    for child in node:
        newchild = updatetokenpos2(child, tokenposdict)
    if node.tag == 'node':
        if ('pt' in node.attrib or 'pos' in node.attrib) and \
                'end' in node.attrib and 'begin' in node.attrib:
            intend = int(node.attrib['end'])
            if intend in tokenposdict:
                newendint = tokenposdict[intend]
                node.attrib['end'] = str(newendint)
                node.attrib['begin'] = str(newendint - 1)
            else:
                settings.LOGGER.error(
                    'Correcttreebank:updatetokenpos: Missing key in tokenposdict: key={key}'.format(key=intend))
                fulltrees = node.xpath('ancestor::node[@cat="top"]')
                if fulltrees != []:
                    fulltree = fulltrees[0]
                else:
                    fulltree = node
                sent = getyield(fulltree)
                settings.LOGGER.error('utterance={}'.format(sent))
                # etree.dump(resulttree)
                settings.LOGGER.error('tokenposdict={}'.format(tokenposdict))
        elif 'cat' in node.attrib:
            children = [ch for ch in node]
            (b, e) = getbeginend(children)
            node.attrib['begin'] = b
            node.attrib['end'] = e
    return node


def updateindexnodes(stree: SynTree) -> SynTree:
    # presupposes that the non bareindex nodes have been adapted
    sentence = getsentence(stree)
    indexednodesmap = getbasicindexednodesmap(stree)
    newstree = deepcopy(stree)
    for node in newstree.iter():
        if node.tag == 'node':
            if bareindexnode(node):
                idx = getattval(node, 'index')
                if idx not in indexednodesmap:
                    settings.LOGGER.warning(f'No antecedent for index {idx} in {sentence}')
                nodebegin = getattval(node, 'begin')
                nodeend = getattval(node, 'end')
                newbegin = getattval(indexednodesmap[idx], 'begin') if idx in indexednodesmap else nodebegin
                newend = getattval(indexednodesmap[idx], 'end') if idx in indexednodesmap else nodeend
                node.attrib['begin'] = newbegin
                node.attrib['end'] = newend
    return newstree


def treewithtokenpos(thetree: SynTree, tokenlist: List[Token]) -> SynTree:
    resulttree = deepcopy(thetree)
    thetreeleaves = getnodeyield(thetree)
    intbegins = [int(getattval(n, 'begin')) for n in thetreeleaves]
    tokenlistbegins = [t.pos + t.subpos for t in tokenlist]
    if len(intbegins) != len(tokenlistbegins):
        settings.LOGGER.warning('treewithtokenpos: token mismatch')
        settings.LOGGER.warning(
            'treewithtokenpos: tree yield={}'.format(getyield(thetree)))
        settings.LOGGER.warning(
            'treewithtokenpos: tokenlist={}'.format(tokenlist))
        settings.LOGGER.warning(
            'treewithtokenpos: intbegins={}'.format(intbegins))
        settings.LOGGER.warning(
            'treewithtokenpos: tokenlistbegins ={}'.format(tokenlistbegins))
    pospairs = zip(intbegins, tokenlistbegins)
    thetreetokenposdict = {treepos + 1: tokenpos + 1 for treepos, tokenpos in pospairs}
    resulttree = updatetokenpos(resulttree, thetreetokenposdict)
    return resulttree


def getptsubclass(pt):
    if pt in ptsubclassdict:
        return ptsubclassdict[pt]
    else:
        return None


def subclasscompatible(sc1, sc2):
    result = (sc1 == sc2) or \
             (sc1 in ['pr', 'refl'] and sc2 in ['pr', 'refl']) or \
             (sc1 in ['pr', 'pers'] and sc2 in ['pr', 'pers']) or \
             (sc1 in ['init', 'versm'] and sc2 in ['init', 'versm'])
            #  (sc1 in ['pv', 'inf']) and sc2 in ['pv', 'inf']    # put off for dldl07,23 hij kan loop
    return result


def fatparse(utterance: str, tokenlist: List[Token]) -> SynTree:
    """
    parses an utterance and inflates the tree but removes nodes corresponding to tokens marked with skip=True
    :param utterance:
    :param tokenlist:
    :return:
    """
    stree = settings.PARSE_FUNC(utterance)
    fatstree = deepcopy(stree)
    treeinflate(fatstree, start=10, inc=10)
    debug = False
    if debug:
        showtree(fatstree, text='fatparse: fatstree')
    # reducedtokenlist = [token for token in tokenlist if not token.skip]  # this should be removed, must be controlled
    # from outside
    # purefatstree = removeskips(fatstree, tokenlist)
    fatstree = treewithtokenpos(fatstree, tokenlist)
    if debug:
        showtree(fatstree, text='fatparse: fatstree')
    return fatstree


def update_cleantokenisation(stree: SynTree, begin: PositionStr) -> SynTree:
    """
    updates the tokenisation info of the cleaned utterance
    :param stree: tree, will be modified
    :param begin: value of the begin attribute of the deleted wordnode
    :return: None
    """
    intbegin = int(begin)
    oldcleanedtokmeta = find1(stree, '//xmeta[@name="cleanedtokenisation"]')
    cleanedtokmeta = copy(oldcleanedtokmeta)
    oldcleanedtokposmeta = find1(
        stree, '//xmeta[@name="cleanedtokenpositions"]')
    cleanedtokposmeta = copy(oldcleanedtokposmeta)
    parent = oldcleanedtokmeta.getparent()
    if not (cleanedtokmeta is None and cleanedtokposmeta is None):
        cleanedtokstr = cleanedtokmeta.attrib['annotationwordlist']
        cleanedtok = strliststr2list(cleanedtokstr)
        newcleanedtok = cleanedtok[:intbegin] + cleanedtok[intbegin + 1:]
        newcleanedtokstr = str(newcleanedtok)
        cleanedtokmeta.attrib['annotationwordlist'] = newcleanedtokstr
        cleanedtokmeta.attrib['value'] = newcleanedtokstr
        parent.remove(oldcleanedtokmeta)
        parent.append(cleanedtokmeta)

        cleanedtokposstr = cleanedtokposmeta.attrib['annotationwordlist']
        cleanedtokpos = str2list(cleanedtokposstr)
        newcleanedtokpos = cleanedtokpos[:intbegin] + \
            cleanedtokpos[intbegin + 1:]
        newcleanedtokposintlist = [int(istr) for istr in newcleanedtokpos]
        newcleanedtokposstr = str(newcleanedtokposintlist)
        cleanedtokposmeta.attrib['annotationwordlist'] = newcleanedtokposstr
        cleanedtokposmeta.attrib['value'] = newcleanedtokposstr
        parent.remove(oldcleanedtokposmeta)
        parent.append(cleanedtokposmeta)

    return stree


def getbeginend(nodelist: List[SynTree]) -> Span:
    minbegin = 1000
    maxend = 0
    for node in nodelist:
        if bareindexnode(node):
            continue
        nodebegin = getattval(node, 'begin')
        nodeend = getattval(node, 'end')
        if int(nodebegin) < minbegin:
            minbegin = int(nodebegin)
        if int(nodeend) > maxend:
            maxend = int(nodeend)
    result = (str(minbegin), str(maxend))
    return result


def normalisebeginend(stree: SynTree) -> None:
    """
    :param stree: syntactic structure
    :return: stree with the values of begin and end attributes normalised
    """
    # etree.dump(stree, pretty_print=True)
    # begins = [getattval(node, 'begin') for node in stree.xpath('.//node[@pt or @pos]')]  # we must include indexed nodes but not have duplicates
    begins = {getattval(node, 'begin')
              for node in stree.xpath('.//node[count(node)=0]')}
    sortedbegins = sorted(list(begins), key=lambda x: int(x))
    normalisebeginend2(stree, sortedbegins)


def normalisebeginend2(stree: SynTree, sortedbegins: List[PositionStr]) -> None:
    """

    :param stree: syntactic structure
    :param sortedbegins: sorted list of begin values of @pt or @pos nodes
    :return: None
    """
    children = list(stree)   # adapt this to seelct only children with tag node (because of the  ud extensions)
    for child in children:
        normalisebeginend2(child, sortedbegins)
    if stree.tag == "node":
        if children == []:
            nodebegin = getattval(stree, 'begin')
            intnodebegin = int(nodebegin)
            newintbegin = sortedbegins.index(nodebegin)
            newbegin = str(newintbegin)
            newend = str(newintbegin + 1)
            stree.attrib['begin'] = newbegin
            stree.attrib['end'] = newend
        else:
            (minbegin, maxend) = getbeginend(children)
            stree.attrib['begin'] = minbegin
            stree.attrib['end'] = maxend

def denormalisebeginend2(stree: SynTree, sortedbegins: List[PositionStr]) -> None:
    """
    adapts the begins and ends of a tree to the sortedbegins: first word will get the first sortedegin, etc
    :param stree: syntactic structure
    :param sortedbegins: sorted list of begin values of @pt or @pos nodes
    :return: None
    """
    children = list(stree) if stree is not None else [] # adapt this to seelct only children with tag node (because of
    # the  ud extensions)
    for child in children:
        denormalisebeginend2(child, sortedbegins)
    if stree.tag == "node":
        if children == []:
            nodebegin = getattval(stree, 'begin')
            intnodebegin = int(nodebegin)
            newbegin = sortedbegins[intnodebegin]
            newend = str(int(newbegin) + 1)
            stree.attrib['begin'] = newbegin
            stree.attrib['end'] = newend
        else:
            (minbegin, maxend) = getbeginend(children)
            stree.attrib['begin'] = minbegin
            stree.attrib['end'] = maxend


def updatebeginend(stree: SynTree, begin: PositionStr) -> None:  # do not use this anymore
    """
    updates the begin and end values of nodes in a tree in which a word node with begin=begin has been removed
    :param stree: Element_tree, input tree, which is modified
    :param begin: (string representation of an integer): value of the begin attribute of the word node that has been removed
    :return: None
    """
    children = list(stree)
    for child in children:
        updatebeginend(child, begin)
    if stree.tag == "node":
        intbegin = int(begin)
        if children == []:
            nodebegin = getattval(stree, 'begin')
            nodeend = getattval(stree, 'end')
            intnodebegin = int(nodebegin)
            intnodeend = int(nodeend)
            if intnodebegin > intbegin:
                stree.attrib['begin'] = str(intnodebegin - 1)
            if intnodeend > intbegin:
                stree.attrib['end'] = str(intnodeend - 1)
        else:
            (minbegin, maxend) = getbeginend(children)
            stree.attrib['begin'] = minbegin
            stree.attrib['end'] = maxend


def add_metadata(intree: SynTree, metalist: List[Meta]) -> SynTree:
    tree = deepcopy(intree)
    metadata = tree.find('.//metadata')
    if metadata is None:
        metadata = etree.Element('metadata')
        tree.insert(0, metadata)

    for meta in metalist:
        metadata.append(meta.toElement())
    return tree


def attach_metadata(intree: SynTree, metalist: List[SynTree]) -> SynTree:
    tree = deepcopy(intree)
    metadata = tree.find('.//metadata')
    if metadata is None:
        metadata = etree.Element('metadata')
        tree.insert(0, metadata)

    for meta in metalist:
        metadata.append(meta)

    return tree


def getneighbourwordnode(node: SynTree, step: int) -> SynTree:
    syntree = find1(node, './ancestor::node[@cat="top"]')
    theyield = getnodeyield(syntree)
    nodeposition = theyield.index(node)
    neighbournodeposition = nodeposition + step
    if len(theyield) > neighbournodeposition >= 0:
        result = theyield[neighbournodeposition]
    else:
        result = None
    return result


def is_infl_different(props1: dict, props2: dict) -> bool:
    for att in all_inflectional_attributes:
        if att in props1:
            if att in props2:
                if props1[att] != props2[att]:
                    return True
            else:
                return True
        elif att in props2:
            return True
    return False

def mkattrib(word, lemma, pt, dcoi_infl) -> dict:
    resultdict = dcoi_infl
    resultdict['lemma'] = lemma
    resultdict['pt'] = pt
    resultdict['word'] = word
    return resultdict

def getparsedas(tree: SynTree, uttstr:str) -> str:
    cleanedtokenisationliststr = str(find1(tree, f'.//xmeta[@name="{correctionlabels.cleanedtokenisation}"]/@value')) \
                                     if tree is not None else '["**"]'
    cleanedtokenisationlist = eval(cleanedtokenisationliststr)
    cleanedtokenisation = space.join(cleanedtokenisationlist) if cleanedtokenisationlist is not None else uttstr
    parsedas_str = find1(tree,
                 f'.//xmeta[@name="{correctionlabels.parsedas}"]/@value') if tree is not None else '**'
    parsedas_str = cleanedtokenisation if parsedas_str is None else parsedas_str
    return parsedas_str

def getpreorigutt(tree: SynTree) -> str:
    preorigutt_meta = find1(tree, './/xmeta[@name="preorigutt"]/@value') if tree is not None else None
    preorigutt = str(preorigutt_meta) if preorigutt_meta is not None else ''
    return preorigutt



def gettokenpos_str(stree: SynTree) -> str:
    nodes = getnodeyield(stree)
    tokenposlist = [f'{getattval(node, "begin")}:{getattval(node, "word")}' for node in nodes]
    result = space.join(tokenposlist)
    return result

def removeskips(fatstree: SynTree, tokenlist: List[Token]) -> SynTree:
    newfatstree = deepcopy(fatstree)
    for token in tokenlist:
        if token.skip:
            begin = str(token.pos + token.subpos)
            wordnode = find1(newfatstree, f'.//node[@word and @begin="{begin}"]')
            if wordnode is None:
                settings.LOGGER.error(f'No node found for {begin}: {token.word} ')
            else:
                wordnode.getparent().remove(wordnode)
    return newfatstree

if __name__ == '__main__':
    # test()
    testindextransform()
