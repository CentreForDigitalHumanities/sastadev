from sastadev.basicreplacements import Rvzlist
from sastadev.CHAT_Annotation import CHAT_phonological_fragment
from sastadev.cleanCHILDEStokens import cleantext
from sastadev.sastatypes import SynTree
from sastadev.sastatoken import Token
from sastadev.stringfunctions import schwa
from sastadev.treebankfunctions import getorigutt
from typing import List


def get_er_vz(token: Token, tree: SynTree) -> List[str]:
    """
    changes a vz into er+vz when preceded by phonological fragment schwa
    """
    results= []

    # the token must be an adposition that can be combined with er
    if token.word.lower() not in Rvzlist:
        return []

    # we first must get the original utterance
    origutt = getorigutt(tree)

    # we must clean it to get the chat metadata
    cleanedtokens, chatmetadata = cleantext(origutt, tokenoutput=True, repkeep=False)

    # get the schwa phonological fragments, if any
    schwametadata = [meta for meta in chatmetadata if meta.name==CHAT_phonological_fragment and
                     (meta.value==[f'&{schwa}'] or meta.value==[f'&+{schwa}'])]

    for schwameta in schwametadata:
        # check if it immediately precedes the token
        nexttoken  = min([tk for tk in cleanedtokens if tk.pos > schwameta.annotatedposlist[0]], key=lambda tk: tk.pos)
        if nexttoken.pos == token.pos:
            results.append(f'er{token.word}')

    return results








