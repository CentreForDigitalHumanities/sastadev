
from sastadev.lexicon import informlexicon
from sastadev.methods import Method
from sastadev.sastatypes import ExactResultsDict, SynTree, TreeBank
from sastadev.stringfunctions import monosyllabic
from sastadev.treebankfunctions import getattval as gav, getxsid, getmeta
from typing import List, Tuple

compoundsep = '_'

def getunknownwordnodes(
    nt: TreeBank, exactresults: ExactResultsDict, method: Method
) -> List[Tuple[SynTree, str, list]]:
    """
    identifies nodes that are unknown words and that have not been replaced by SASTA by known words
    :param nt:
    :param _:
    :param method:
    :return:
    """

    mn = method.name
    rawresults = []
    rawunknownwordnodes = []
    for tree in nt:
        uttid = getxsid(tree)
        if uttid == "0":
            continue
        session = getmeta(tree, "session")
        junk = 0
        wordnodes = [wn for wn in tree.xpath('.//node[@pt!="tsw"]')]
        rawunknownwordnodes = [
            wn
            for wn in wordnodes
            if not isvalidword(
                wn.attrib["word"].lower(), mn, includealpinonouncompound=False
            )
            and not compoundsep in wn.attrib["lemma"]
            and not isrobustname(wn)
            and gav(wn, "pt") != "tsw"
            and not gav(wn, "word").isnumeric()
            and not isnumericordinal(gav(wn, "word"))
        ]
    rawresults += [
        (unknownwordnode, f'{unknownwordmessage}: {gav(unknownwordnode, "word")}', [])
        for unknownwordnode in rawunknownwordnodes
    ]
    results = filterbymetadata(rawresults, exactresults, method.name)
    return results


suspicious_compound_message = 'unlikely compound'
suffixes = ['en', 'er']
def get_suspicious_compounds(nt: TreeBank, exactresults: ExactResultsDict, method: Method) \
        -> List[Tuple[SynTree, str, list]]:
    """
    identifies nodes that are unknown words and that have been analysed as a compound but
    that contain as last component a single syllabel word ending in frequet inflectional suffixes such as -en, -er
    :param nt:
    :param _:
    :param method:
    :return:
    """
    rawresults = []
    for tree in nt:
        uttid = getxsid(tree)
        if uttid == "0":
            continue
        session = getmeta(tree, "session")
        junk = 0
        wordnodes = [wn for wn in tree.xpath('.//node[@pt!="tsw" and @pt!="let"]')]
        for wordnode in wordnodes:
            word = gav(wordnode, 'word')
            lcword = word.lower()
            lemma = gav(wordnode, 'lemma')
            pt = gav(wordnode, 'pt')
            if pt == 'n' and compoundsep in lemma and not informlexicon(lcword):
                parts = lemma.split(compoundsep)
                lastpart = parts[-1]
                if monosyllabic(lastpart):
                    for suffix in suffixes:
                        if lastpart.endswith(suffix):
                            messagefunction = get_message_with_word_function(suspicious_compound_message)
                            result = (wordnode, messagefunction(wordnode), [])
                            rawresults.append(result)
    results = filterbymetadata(rawresults, exactresults, method.name)
    return results
