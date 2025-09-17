from typing import List

from sastadev.allresults import mkresultskey
from sastadev.CHAT_Annotation import CHAT_replacement, CHAT_wordnoncompletion
from sastadev.correctionlabels import (
    alpinoimprovement,
    ambiguityavoidance,
    codareduction,
    contextcorrection,
    dehyphenation,
    disambiguation,
    emphasis,
    error,
    explanationasreplacement,
    finalndrop,
    grammarerror,
    inflectionerror,
    informalpronunciation,
    lexicalerror,
    morphologicalerror,
    noncompletion,
    regionalform,
    regionalvariantorlexicalerror,
    repetition,
    repeatedword,
    replacement,
    pronunciationvariant,
    spellingcorrection,
    unknownword,
    unknownwordsubstitution,
    wordunknowntoalpino,
    wrongpronunciation,
)
from sastadev.lexicon import valid_ambiguous_words
from sastadev.metadata import (
    ALLSAMPLECORRECTIONS,
    BASICREPLACEMENTS,
    EXTRAGRAMMATICAL,
    SASTA,
    THISSAMPLECORRECTIONS,
    HISTORY
)
from sastadev.methods import asta
from sastadev.sastatypes import ExactResults, ExactResultsDict, SAS_Result_List, SynTree
from sastadev.ASTApostfunctions import mluxqid, samplesizeqid
from sastadev.stringfunctions import normalise_word
from sastadev.treebankfunctions import (
    getattval,
    getmeta,
    getnodeyield,
    getxsid,
    getyieldstr,
)


mlureskey = mkresultskey(mluxqid)
samplesizereskey = mkresultskey(samplesizeqid)

wordreplacementtypes = [
    alpinoimprovement,
    ambiguityavoidance,
    codareduction,
    contextcorrection,
    disambiguation,
    dehyphenation,
    emphasis,
    error,
    explanationasreplacement,
    finalndrop,
    grammarerror,
    inflectionerror,
    informalpronunciation,
    lexicalerror,
    morphologicalerror,
    noncompletion,
    regionalform,
    regionalvariantorlexicalerror,
    repeatedword,
    repetition,
    replacement,
    pronunciationvariant,
    spellingcorrection,
    unknownword,
    unknownwordsubstitution,
    wordunknowntoalpino,
    wrongpronunciation,
    CHAT_replacement,
    CHAT_wordnoncompletion,
]

namecondition = " or ".join([f'@name="{wrt}"' for wrt in wordreplacementtypes])

sources = [BASICREPLACEMENTS, ALLSAMPLECORRECTIONS, THISSAMPLECORRECTIONS, HISTORY]

sourcecondition = "or ".join([f'@source="{SASTA}/{source}"' for source in sources])

fullcondition = f"({namecondition}) or ({sourcecondition})"

extragrammatical_xpath = f""".//xmeta[@name="{EXTRAGRAMMATICAL}"]"""

def getnormalisedwnposition(wn: SynTree, stree: SynTree) -> int:
    theyield = getnodeyield(stree)
    for i, node in enumerate(theyield):
        if node == wn:
            return i + 1
    return 0


def wnisanASTAX(wn: SynTree, tree: SynTree, exactresult: ExactResults) -> bool:
    wnposition = getnormalisedwnposition(wn, tree)
    if wnposition == 0:
        return False
    foundastax = [
        el
        for el in exactresult
        if el[1] == wnposition and el[0] in [mlureskey, samplesizereskey]
    ]
    result = foundastax != []
    return result

def is_recognised_extra_grammatical(wn: SynTree, tree: SynTree) -> bool:
    wnbegin = getattval(wn, 'begin')
    extragrammatical_metadata = tree.xpath(extragrammatical_xpath)
    for extragrammatical_meta in extragrammatical_metadata:
        if wnbegin in getattval(extragrammatical_meta, 'annotatedposlist'):
            return True
    return False


def filterbymetadata(
    rawresults: SAS_Result_List, exact_results_dict: ExactResultsDict, method_name: str
) -> List[SynTree]:
    """
    Removes nodes from a list of nodes if they have already been replaced by
    SASTA. These can be found in the metadata of the utterance.
    and remove nodes, under the ASTA method, for words that have also been marked for SampleSize (SSZX) or MLU (MLUX)
    """
    unknownwordnodes = []
    for item in rawresults:
        (wn, message, suggestions) = item
        wnword = getattval(wn, 'word')
        if wnword == '':
            unknownwordnodes.append(item)
            continue
        normalised_wnword = normalise_word(wnword)
        if normalised_wnword in valid_ambiguous_words:
            continue
        fulltrees = wn.xpath("ancestor::alpino_ds")
        fulltree = fulltrees[0] if fulltrees != [] else None
        uttid = getxsid(fulltree)
        session = getmeta(fulltree, "session")
        wnbegin = getattval(wn, "begin")
        mdxpath = f"""./ancestor::alpino_ds/descendant::xmeta[({fullcondition}) and 
                       (@annotatedposlist="[{wnbegin}]" or @annotationposlist="[{wnbegin}]")]"""
        replacements = wn.xpath(mdxpath)
        exact_results = exact_results_dict[uttid] if uttid in exact_results_dict else []
        if exact_results == []:
            print(
                f'{session}: Empty exactresults: {getattval(wn, "word")} in {uttid}: {getyieldstr(fulltree)}'
            )
        isASTAX = (
            wnisanASTAX(wn, fulltree, exact_results) if method_name == asta else False
        )
        recognised_extra_grammatical = is_recognised_extra_grammatical(wn, fulltree)
        if replacements == [] and not isASTAX and not recognised_extra_grammatical:
            unknownwordnodes.append((wn, message, suggestions))
    return unknownwordnodes
