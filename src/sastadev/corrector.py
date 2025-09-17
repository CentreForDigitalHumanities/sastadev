"""
to be added
"""

import copy
import re
from typing import Callable, Dict, List, Optional, Tuple

from sastadev.alpino import getdehetwordinfo
from sastadev.basicreplacements import (basicexpansions, basicreplacementpairs, basicreplacements, ervzvariantsdict,
                                        getdisambiguationdict, is_er_pronoun)
from sastadev.CHAT_Annotation import CHAT_retracing
from sastadev.childesspellingcorrector import (children_correctionsdict, children_correctspelling,  allfrqdict)
from sastadev import correctionlabels
from sastadev.correctionparameters import CorrectionParameters
from sastadev.cleanCHILDEStokens import cleantokens
from sastadev.conf import settings
from sastadev.dedup import (cleanwordofnort, filled_pause_exceptions, find_duplicates2,
                            find_janeenouduplicates, find_simpleduplicates,
                            find_substringduplicates2, getfilledpauses,
                            getprefixwords, getrepeatedtokens,
                            getunwantedtokens, nodesfindjaneenou)
from sastadev.deregularise import correctinflection, separable_prefixes
from sastadev.find_ngram import (Ngram, findmatches, ngram1, ngram2, ngram7,
                                 ngram10, ngram11, ngram16, ngram17)
from sastadev.history import (childescorrections, childescorrectionsexceptions)
from sastadev.iedims import getjeforms
from sastadev.lexicon import (alt_pt_ww_n_pairdict, WordInfo, de, definite_determiners, dets, getwordinfo, het,
                              informlexicon, isa_namepart, isa_inf, isa_vd, possessive_determiners,
                              tswnouns, validnotalpinocompoundword, validword, vuwordslexicon,
                              wordsunknowntoalpinolexicondict)
from sastadev.macros import expandmacros
from sastadev.metadata import (Meta, bpl_word_delprec, bpl_indeze, bpl_node, bpl_none, bpl_word,
                               bpl_wordlemma, defaultbackplacement,
                               defaultpenalty, filled_pause, fstoken, intj,
                               janeenou, longrep, mkSASTAMeta, modifypenalty as mp, repeatedjaneenou, repeatedseqtoken, shortrep,
                               substringrep, unknownsymbol,
                               SASTA, ADULTSPELLINGCORRECTION, ALLSAMPLECORRECTIONS, BASICREPLACEMENTS, CONTEXT, HISTORY, THISSAMPLECORRECTIONS,
                               CHILDRENSPELLINGCORRECTION,
                               EXTRAGRAMMATICAL
                              )
from sastadev.queryfunctions import get_aanloop_and_core, getuitloop
from sastadev.sasta_explanation import explanationasreplacement
from sastadev.sastatoken import Token, tokenlist2stringlist
from sastadev.sastatypes import (BackPlacement, MethodName, Nort, Penalty,
                                 Position, SynTree, UttId)
from sastadev.smallclauses import smallclauses
from sastadev.spellingerrors import getbabylemma, isbabyword, correctbaby
from sastadev.stringfunctions import (chatxxxcodes, consonants, dutchdeduplicate,
                                      endsinschwa, fullworddehyphenate, ispunctuation,
                                      monosyllabic, sentencefinalpuncs, vowels)
from sastadev.sva import getsvacorrections
from sastadev.tblex import getaanloop_core_uitloop
from sastadev.toe import lonelytoe
from sastadev.tokenmd import TokenListMD, TokenMD, mdlist2listmd
from sastadev.treebankfunctions import (fatparse, getattval, getmeta, getnodeyield, gettokenpos_str, getxsid,
                                        isdefdet, keycheck,
                                        mktoken2nodemap, showtree)

Correction = Tuple[List[Token], List[Meta]]
MetaCondition = Callable[[Meta], bool]

basepenalties = {ADULTSPELLINGCORRECTION: 600, ALLSAMPLECORRECTIONS: 400, BASICREPLACEMENTS: 100, CHILDRENSPELLINGCORRECTION: 600,
                 CONTEXT: 200, HISTORY:500, THISSAMPLECORRECTIONS: 300
                 }

tarsp = 'tarsp'
stap = 'stap'
asta = 'asta'

hyphen = '-'
errormsgsep = '&'

replacepattern = '{} [: {} ]'
metatemplate = '##META {} {} = {}'
slash = '/'
space = ' '

enexceptions = {'inne', 'mette', 'omme', 'oppe', 'vanne'}
leggendict = {'leg': 'lig', 'legt': 'ligt', 'leggen': 'liggen'}
aposfollowers = {'ochtends', 'middags', 'avonds', 'nachts', 'morgens', 'werelds', 'lands', 'anderendaags',
                 'winters', 'zomers', 'namiddags',
                 'zondags', 'maandags', 'dinsdags', 'woensdags', 'donderdags', 'vrijdags', 'zaterdags'}

#: The constant *disambiguationdict* contains words that should be replaced by a
#: different word to avoid unwanted readings of the original word. It is filled by a
#: call to the function *getdisambiguationdict* from the module *basicreplacements*.
#:
#: .. autofunction:: sastadev.basicreplacements::getdisambiguationdict
#:
disambiguationdict = getdisambiguationdict()

#: The constant *wrongdet_excluded_words* contains words that lead to incorrect
#: replacement of uter determiners (e.g. *die zijn* would be replaced by *dat zijn*) and
#: therefore have to be excluded from determiner replacement.
wrongdet_excluded_words = ['zijn', 'dicht', 'met', 'ik', 'mee', 'wat', 'alles', 'niet', 'spelen']

#: The constant *e2een_excluded_nouns* contains words that lead to incorrect
#: replacement of e or schwa  and
#: therefore have to be excluded from determiner replacement.
e2een_excluded_nouns = ['kijke', 'kijken', 'weer']

comma = ","

initialmaarvgxpath = expandmacros(""".//node[%maarvg%]""")


class Ngramcorrection:
    def __init__(self, ngram, fpositions, cpositions, metafunction):
        self.ngram: Ngram = ngram
        self.fpositions: Tuple[Position, Position] = fpositions
        self.cpositions: Tuple[Position, Position] = cpositions
        self.metafunction = metafunction


def mkmeta(att: str, val: str, type: str = 'text') -> str:
    result = metatemplate.format(type, att, val)
    return result


def anychars(chars: str) -> str:
    result = '[' + chars + ']'
    return result


def opt(pattern: str) -> str:
    result = '(' + pattern + ')?'
    return result


def replacement(inword: str, outword: str) -> str:
    result = replacepattern.format(inword, outword)
    return result


# duppattern = r'(.)\1{2,}'
# dupre = re.compile(duppattern)
#: The pattern *gaatiepattern* identifies words ending in *tie* preceded by at least a
#: vowel and optionally a consonant.
gaatiepattern = r'^.*' + anychars(vowels) + opt(anychars(consonants)) + 'tie$'
gaatiere = re.compile(gaatiepattern)
gaattiepattern = r'^.*' + anychars(vowels) + 'ttie$'
gaattiere = re.compile(gaattiepattern)
neutersgnoun = 'boekje'  # select here an unambiguous neuter noun


def isdet(node: SynTree) -> bool:
    if node is None:
        return False
    nodept = getattval(node, 'pt')
    node_pdtype = getattval(node, 'pdtype')
    node_lemma = getattval(node, 'lemma')
    result = nodept == 'lid' or (nodept == 'vnw' and (node_pdtype == 'det' or node_lemma in ['wat']))
    return result


def isaverb(wrd:str) -> bool:
    wordinfos = getwordinfo(wrd)
    verbwordinfos = [wordinfo for wordinfo in wordinfos if wordinfo[0] == 'ww']
    result = verbwordinfos != []
    return result




def startswithsvp(wrd: str) -> Tuple[bool, str]:
    for svp in separable_prefixes:
        if wrd.startswith(svp):
            return True, svp
    return False, ''


def isaninftoken(token: Optional[Token]) -> bool:
    if token is None:
        return False
    result = isa_inf(token.word)
    return result


def skiptokens(tokenlist: List[Token], skiptokenlist: List[Token]) -> List[Token]:
    '''

    :param tokenlist:
    :param skiptokenlist:
    :return: a tokenlist identical to the input tokenlist but with the tokens that also occur with the same pos
    in skiptokenlist marked with skip=True
    '''
    skippositions = {token.pos for token in skiptokenlist}
    resultlist = []
    for token in tokenlist:
        if token.pos in skippositions:
            newtoken = Token(token.word, token.pos, skip=True)
        else:
            newtoken = token
        resultlist.append(newtoken)
    return resultlist


def speakeristargetchild(stree: SynTree) -> bool:
    role = getmeta(stree, 'role')
    result = role.lower() != 'target_child'
    return result

def nottargetchild(stree: SynTree) -> bool:
    result = not speakeristargetchild(stree)
    return result

def ngramreduction(reducedtokens: List[Token], token2nodemap: Dict[Token, SynTree], allremovetokens: List[Token],
                   allremovepositions: List[Position], allmetadata: List[Meta], ngramcor: Ngramcorrection) \
        -> Tuple[List[Token], List[Token], List[Meta]]:
    # metadat function should still be added / abstracted
    (fb, fe) = ngramcor.fpositions
    (cb, ce) = ngramcor.cpositions
    reducedleaves = [token2nodemap[tok.pos] for tok in reducedtokens if keycheck(tok.pos, token2nodemap)]

    vnwpvvnwpvmatches = findmatches(ngramcor.ngram, reducedleaves)
    allfalsestarttokens = []
    metadata = []
    for match in vnwpvvnwpvmatches:
        positions = [pos for pos in range(match[0], match[1])]
        falsestartpositions = [tok.pos for i, tok in enumerate(
            reducedtokens) if i in positions[fb:fe]]
        falsestarttokens = [
            tok for tok in reducedtokens if tok.pos in falsestartpositions]
        allfalsestarttokens += falsestarttokens
        correcttokenpositions = [tok.pos for i, tok in enumerate(
            reducedtokens) if i in positions[cb:ce]]
        correcttokens = [
            tok for tok in reducedtokens if tok.pos in correcttokenpositions]
        allremovetokens += falsestarttokens
        allremovepositions += falsestartpositions
        metadata += ngramcor.metafunction(falsestarttokens,
                                          falsestartpositions, correcttokens)
    reducedtokens = [
        tok for tok in reducedtokens if tok not in allfalsestarttokens]
    allmetadata += metadata
    return reducedtokens, allremovetokens, allmetadata


def inaanloop(tok, tokens) -> bool:
    if len(tokens) == 0:
        return False
    if tokens[0] == tok:
        if len(tokens) == 1:
            return False
        else:
            return tokens[1].word == comma
    else:
        return False

def inuitloop(tok, tokens) -> bool:
    if len(tokens) < 2:
        return False
    elif tokens[-1].word in sentencefinalpuncs:
        thetoken = tokens[-2]
        prectoken = tokens[-3] if len(tokens) > 2 else None
    else:
        thetoken = tokens[-1]
        prectoken = tokens[-2]
    result = tok == thetoken and prectoken is not None and prectoken.word == comma
    return result
def mustberemoved(tok, toknode, reducedtokens, reducednodeyield) -> bool:
    wordprops = vuwordslexicon[tok.word]
    aanloop, core = get_aanloop_and_core(reducednodeyield)
    removeinaanloop = '1' in wordprops and toknode in aanloop
    removefirst = '1' in wordprops and ',' not in wordprops and tok == reducedtokens[0]
    core, uitloop = getuitloop(core)
    removeinuitloop = '3' in wordprops and toknode in uitloop
    removelast = '3' in wordprops and ',' not in wordprops and tok == reducedtokens[-1]
    removeincore = '2' in vuwordslexicon[tok.word] and not toknode not in uitloop and \
                   toknode not in aanloop
    result = removeinaanloop or removefirst or removeinuitloop or removelast or removeincore
    return result


def reduce(tokens: List[Token], tree: Optional[SynTree]) -> Tuple[List[Token], List[Meta]]:
    if tree is None:
        settings.LOGGER.error(
            'No tree for :{}\nNo reduction applied'.format(tokens))
        return ((tokens, []))

    tokennodes = tree.xpath('.//node[@pt or @pos or @word]')
    tokennodesdict = {int(getattval(n, 'begin')): n for n in tokennodes}
    token2nodemap = {token.pos: tokennodesdict[token.pos]
                     for token in tokens if keycheck(token.pos, tokennodesdict)}

    reducedtokens = tokens
    allmetadata = []

    allremovetokens = []
    allremovepositions = []

    # throw out unwanted symbols - -- # etc
    unwantedtokens = getunwantedtokens(reducedtokens)
    unwantedpositions = [tok.pos for tok in unwantedtokens]
    allremovetokens += unwantedtokens
    allremovepositions += unwantedpositions
    reducedtokens = [n for n in reducedtokens if n not in unwantedtokens]
    metadata = [mkSASTAMeta(token, token, EXTRAGRAMMATICAL,
                            unknownsymbol, correctionlabels.syntax) for token in unwantedtokens]
    allmetadata += metadata

    # remove  filled pauses

    filledpausetokens = getfilledpauses(reducedtokens)
    filledpausepositions = [token.pos for token in filledpausetokens]
    allremovetokens += filledpausetokens
    allremovepositions += filledpausepositions
    reducedtokens = [
        tok for tok in reducedtokens if tok not in filledpausetokens]
    reducednodes = [token2nodemap[tok.pos]
                    for tok in reducedtokens if keycheck(tok.pos, token2nodemap)]
    metadata = [mkSASTAMeta(token, token, EXTRAGRAMMATICAL,
                            filled_pause, correctionlabels.syntax) for token in filledpausetokens]
    allmetadata += metadata

    # remove vuwords partially dependent on their position
    reducednodes = [token2nodemap[token.pos] for token in reducedtokens if keycheck(token.pos, token2nodemap)]
    vutokens = [tok for tok in reducedtokens if tok.word in vuwordslexicon and
                mustberemoved(tok, token2nodemap[tok.pos], reducedtokens, reducednodes)
                ]
    allremovetokens += vutokens
    reducedtokens = [n for n in reducedtokens if n not in vutokens]
    metadata = [mkSASTAMeta(token, token, EXTRAGRAMMATICAL,
                            intj, correctionlabels.syntax) for token in vutokens]
    allmetadata += metadata

    # we do not use the notanalyzewords.txt hopefully covered by following
    # we must exclude here the vuwords unless they are in the appropriate position (hoor at the end, but toe only at the beginning
    # remove tsw incl goh och hé oke but not ja, nee, nou
    tswtokens = [n for n in reducedtokens if n.pos in token2nodemap
                 and n.word not in filled_pause_exceptions
                 and getattval(token2nodemap[n.pos], 'pt') == 'tsw'
                 and getattval(token2nodemap[n.pos], 'lemma') not in {'ja', 'nee', 'nou'}
                 and getattval(token2nodemap[n.pos], 'lemma') not in tswnouns
                 and getattval(token2nodemap[n.pos], 'lemma') not in vuwordslexicon
                 ]
    tswpositions = [n.pos for n in tswtokens]
    allremovetokens += tswtokens
    allremovepositions == tswpositions
    reducedtokens = [n for n in reducedtokens if n not in tswtokens]
    metadata = [mkSASTAMeta(token, token, EXTRAGRAMMATICAL,
                            intj, correctionlabels.syntax) for token in tswtokens]
    allmetadata += metadata

    # remove words in the aanloop
    aanloops, core, uitloops = getaanloop_core_uitloop(tree)
    aanlooptokens = [tok for tok in reducedtokens if any([token2nodemap[tok.pos] in aanloop for aanloop in aanloops])]
    allremovetokens += aanlooptokens
    reducedtokens = [n for n in reducedtokens if n not in aanlooptokens]
    metadata = [mkSASTAMeta(token, token, EXTRAGRAMMATICAL,
                            correctionlabels.aanloop, correctionlabels.syntax) for token in aanlooptokens]
    allmetadata += metadata

    # remove words in the uitloop
    rawuitlooptokens = [tok for tok in reducedtokens
                        if any([token2nodemap[tok.pos] in uitloop for uitloop in uitloops])]
    # keep the final punctuation symbol in because it may affect the parse
    uitlooptokens = rawuitlooptokens[:-1] \
                if rawuitlooptokens != [] and rawuitlooptokens[-1].word in sentencefinalpuncs \
                else rawuitlooptokens
    allremovetokens += uitlooptokens
    reducedtokens = [n for n in reducedtokens if n not in uitlooptokens]
    metadata = [mkSASTAMeta(token, token, EXTRAGRAMMATICAL,
                            correctionlabels.uitloop, correctionlabels.syntax) for token in uitlooptokens]
    allmetadata += metadata

    # find duplicatenode repetitions of ja, nee, nou
    janeenouduplicatenodes = find_janeenouduplicates(reducedtokens)
    allremovetokens += janeenouduplicatenodes
    reducedtokens = [
        n for n in reducedtokens if n not in janeenouduplicatenodes]
    reducednodes = [token2nodemap[tok.pos]
                    for tok in reducedtokens if keycheck(tok.pos, token2nodemap)]
    metadata = [mkSASTAMeta(token, token, EXTRAGRAMMATICAL, repeatedjaneenou, correctionlabels.syntax, subcat=correctionlabels.repetition)
                for token in janeenouduplicatenodes]
    allmetadata += metadata

    # ASTA sec 6.3 p. 11
    # remove ja nee nou

    janeenounodes = nodesfindjaneenou(reducednodes)
    janeenoutokens = [tok for tok in reducedtokens if
                      keycheck(tok.pos, token2nodemap) and token2nodemap[tok.pos] in janeenounodes]
    janeenoupositions = [token.pos for token in janeenoutokens]
    allremovetokens += janeenoutokens
    allremovepositions += janeenoupositions
    reducedtokens = [tok for tok in reducedtokens if tok not in janeenoutokens]
    metadata = [mkSASTAMeta(token, token, EXTRAGRAMMATICAL,
                            janeenou, correctionlabels.syntax) for token in janeenoutokens]
    allmetadata += metadata

    # short repetitions
    def oldcond(x: Nort, y: Nort) -> bool:
        return len(cleanwordofnort(x)) / len(cleanwordofnort(y)) < .5 and not informlexicon(cleanwordofnort(x))

    def cond(x: Nort, y: Nort) -> bool:
        return len(cleanwordofnort(x)) / len(cleanwordofnort(
            y)) < .5  # check on lexicon put off actually two variants should be tried if the word is an existin gword

    shortprefixtokens = getprefixwords(reducedtokens, cond)
    shortprefixpositions = [token.pos for token in shortprefixtokens]
    repeatedtokens = getrepeatedtokens(reducedtokens, shortprefixtokens)
    allremovetokens += shortprefixtokens
    allremovepositions += shortprefixpositions
    metadata = [
        mkSASTAMeta(token, repeatedtokens[token], repeatedseqtoken, shortrep, correctionlabels.tokenisation,
                    subcat=correctionlabels.repetition) for
        token in reducedtokens if token in repeatedtokens]
    allmetadata += metadata
    reducedtokens = [
        tok for tok in reducedtokens if tok not in shortprefixtokens]

    # long repetitions
    def longcond(x: Nort, y: Nort) -> bool:
        return len(cleanwordofnort(x)) / len(cleanwordofnort(y)) >= .5 and not informlexicon(cleanwordofnort(x))

    longprefixtokens = getprefixwords(reducedtokens, longcond)
    longprefixpositions = [token.pos for token in longprefixtokens]
    repeatedtokens = getrepeatedtokens(reducedtokens, longprefixtokens)
    allremovetokens += longprefixtokens
    allremovepositions += longprefixpositions
    metadata = [
        mkSASTAMeta(token, repeatedtokens[token], correctionlabels.repeatedword, longrep,
                    correctionlabels.tokenisation,
                    subcat=correctionlabels.repetition) for
        token in reducedtokens if token in repeatedtokens]
    allmetadata += metadata
    reducedtokens = [
        tok for tok in reducedtokens if tok not in longprefixtokens]

    # find unknown words that are a substring of their successor
    substringtokens, _ = find_substringduplicates2(reducedtokens)
    substringpositions = [token.pos for token in substringtokens]
    repeatedtokens = getrepeatedtokens(reducedtokens, substringtokens)
    allremovetokens += substringtokens
    allremovepositions += substringpositions
    metadata = [mkSASTAMeta(token, repeatedtokens[token], substringrep, substringrep, correctionlabels.tokenisation,
                            subcat=correctionlabels.repetition) for token in reducedtokens if token in repeatedtokens]
    allmetadata += metadata
    reducedtokens = [
        tok for tok in reducedtokens if tok not in substringtokens]

    # simple duplicates
    dupnodetokens = find_simpleduplicates(reducedtokens)
    dupnodepositions = [token.pos for token in dupnodetokens]
    repeatedtokens = getrepeatedtokens(reducedtokens, dupnodetokens)
    allremovetokens += dupnodetokens
    allremovepositions += dupnodepositions
    metadata = [mkSASTAMeta(token, repeatedtokens[token], correctionlabels.repeatedword,
                            correctionlabels.repeatedword, correctionlabels.tokenisation,
                            subcat=correctionlabels.repetition) for token in reducedtokens if token in repeatedtokens]
    allmetadata += metadata
    reducedtokens = [tok for tok in reducedtokens if tok not in dupnodetokens]

    # duplicate sequences
    dupnodetokens, dupinfo = find_duplicates2(reducedtokens)
    dupnodepositions = [token.pos for token in dupnodetokens]
    duppairs = []
    for token in dupnodetokens:
        for othertok in reducedtokens:
            if token.pos in dupinfo.longdups and othertok.pos == dupinfo.longdups[token.pos]:
                nwt = othertok
                duppairs.append((token, nwt))
                break
    allremovetokens += dupnodetokens
    allremovepositions += dupnodepositions
    metadata = [mkSASTAMeta(token, nwt, repeatedseqtoken,
                            repeatedseqtoken, correctionlabels.tokenisation, subcat=correctionlabels.repetition)
                for token, nwt in duppairs]
    allmetadata += metadata
    reducedtokens = [tok for tok in reducedtokens if tok not in dupnodetokens]

    # remove unknown words if open class DO NOT DO this
    # unknown_word_tokens = [tok for tok in reducedtokens if getattval(token2nodemap[tok.pos], 'pt') in openclasspts
    #                        and not (asta_recognised_wordnode(token2nodemap[tok.pos]))]
    # unknown_word_positions = [token.pos for token in unknown_word_tokens]
    # allremovetokens += unknown_word_tokens
    # allremovepositions += unknown_word_positions
    # metadata = [mkSASTAMeta(token, token, 'ExtraGrammatical',
    #                         unknownword, correctionlabels.tokenisation)
    #             for token in reducedtokens if token in unknown_word_tokens]
    # allmetadata += metadata
    # reducedtokens = [n for n in reducedtokens if n not in unknown_word_tokens]

    # ngram based cases

    # vnw pv vnw pv

    def metaf(falsestarttokens: List[Token], falsestartpositions: List[Position], correcttokens: List[Token]) \
            -> List[Meta]:
        return \
            [Meta(CHAT_retracing, correctionlabels.retracing, annotatedposlist=falsestartpositions,
                  annotatedwordlist=[c.word for c in falsestarttokens],
                  annotationposlist=[c.pos for c in correcttokens],
                  annotationwordlist=[c.word for c in correcttokens], cat=correctionlabels.retracing, subcat=None, source=SASTA,
                  penalty=defaultpenalty, backplacement=bpl_none)] + \
            [mkSASTAMeta(ftoken, ctoken, correctionlabels.retracing, fstoken, CHAT_retracing)
             for ftoken, ctoken in zip(falsestarttokens, correcttokens)]

    vnwpvvnwpvcor = Ngramcorrection(ngram1, (0, 2), (2, 4), metaf)
    reducedtokens, allremovetokens, allmetadata = ngramreduction(reducedtokens, token2nodemap, allremovetokens,
                                                                 allremovepositions, allmetadata, vnwpvvnwpvcor)

    vzdetvzdetcor = Ngramcorrection(ngram2, (0, 2), (2, 4), metaf)
    reducedtokens, allremovetokens, allmetadata = ngramreduction(reducedtokens, token2nodemap, allremovetokens,
                                                                 allremovepositions, allmetadata, vzdetvzdetcor)

    vgdetvgdetcor = Ngramcorrection(ngram7, (0, 2), (2, 4), metaf)
    reducedtokens, allremovetokens, allmetadata = ngramreduction(reducedtokens, token2nodemap, allremovetokens,
                                                                 allremovepositions, allmetadata, vgdetvgdetcor)
    vnwipvjxpvjvnwi = Ngramcorrection(ngram10, (0, 2), (3, 5), metaf)
    reducedtokens, allremovetokens, allmetadata = ngramreduction(reducedtokens, token2nodemap, allremovetokens,
                                                                 allremovepositions, allmetadata, vnwipvjxpvjvnwi)
    lemilemjlemilemj = Ngramcorrection(ngram11, (0, 2), (3, 5), metaf)
    reducedtokens, allremovetokens, allmetadata = ngramreduction(reducedtokens, token2nodemap, allremovetokens,
                                                                 allremovepositions, allmetadata, lemilemjlemilemj)

    dinjdknj = Ngramcorrection(ngram16, (0, 2), (3, 5), metaf)
    reducedtokens, allremovetokens, allmetadata = ngramreduction(reducedtokens, token2nodemap, allremovetokens,
                                                                 allremovepositions, allmetadata, dinjdknj)

    tevtev = Ngramcorrection(ngram17, (0, 2), (2, 4), metaf)
    reducedtokens, allremovetokens, allmetadata = ngramreduction(reducedtokens, token2nodemap, allremovetokens,
                                                                 allremovepositions, allmetadata, tevtev)

    # reducedleaves = [token2nodemap[tok.pos] for tok in reducedtokens]
    #
    # vnwpvvnwpvmatches = findmatches(ngram1, reducedleaves)
    # allfalsestarttokens = []
    # metadata = []
    # for match in vnwpvvnwpvmatches:
    #     positions = [pos for pos in range(match[0], match[1])]
    #     falsestartpositions = [tok.pos for i, tok in enumerate(reducedtokens) if i in positions[0:2]]
    #     falsestarttokens = [tok for tok in reducedtokens if tok.pos in falsestartpositions]
    #     allfalsestarttokens += falsestarttokens
    #     correcttokenpositions = [tok.pos for i, tok in enumerate(reducedtokens) if i in positions[2:5]]
    #     correcttokens = [tok for tok in reducedtokens if tok.pos in correcttokenpositions]
    #     allremovetokens += falsestarttokens
    #     allremovepositions += falsestartpositions
    #     metadata += [Meta(correctionlabels.retracing, 'Retracing with Correction',  annotatedposlist=falsestartpositions,
    #                  annotatedwordlist=[c.word for c in falsestarttokens], annotationposlist=[c.pos for c in correcttokens],
    #                  annotationwordlist=[c.word for c in correcttokens], cat=correctionlabels.retracing, subcat=None, source=SASTA,
    #                     penalty=defaultpenalty, backplacement=bpl_none)]
    #     metadata += [mkSASTAMeta(ftoken, ctoken, 'Retracing with Correction', fstoken,  correctionlabels.retracing, )
    #                 for ftoken, ctoken  in zip(falsestarttokens, correcttokens)]
    #
    # reducedtokens = [tok for tok in reducedtokens if tok not in allfalsestarttokens]
    # allmetadata += metadata

    # remove trailing comma's

    if len(reducedtokens) > 2 and  reducedtokens[-2].word == comma and reducedtokens[-1].word in sentencefinalpuncs:
        allremovetokens.append(reducedtokens[-2])
        reducedtokens = reducedtokens[:-2] + [reducedtokens[-1]]
    if reducedtokens != [] and reducedtokens[-1].word == comma:
        allremovetokens.append(reducedtokens[-1])
        reducedtokens = reducedtokens[:-1]


    skipmarkedtokens = skiptokens(tokens, allremovetokens)

    # return (reducedtokens, allremovetokens, allmetadata)
    return (skipmarkedtokens, allmetadata)




def combinesorted(toklist1: List[Token], toklist2: List[Token]) -> List[Token]:
    result = toklist1 + toklist2
    sortedresult = sorted(result, key=lambda tok: tok.pos)
    return sortedresult


def getcorrections(rawtokens: List[Token], correctionparameters: CorrectionParameters,
                   tree: Optional[SynTree] = None) -> List[Correction]:
    allmetadata = []
    # rawtokens = sasta_tokenize(utt)
    wordlist = tokenlist2stringlist(rawtokens)
    utt = space.join(wordlist)
    origutt = utt
    # print(utt)

    # check whether the tree has the same yield
    origtree = tree
    treeyield = getnodeyield(tree)
    treewordlist = [getattval(n, 'word') for n in treeyield]

    if treewordlist != wordlist:
        revisedutt = space.join(wordlist)
        tree = fatparse(revisedutt, rawtokens)

    tokens, metadata = cleantokens(rawtokens, repkeep=False)
    allmetadata += metadata
    tokensmd = TokenListMD(tokens, [])

    # check whether there is a utterance final multiword explanation, and if so, align it with the utterance
    # use this aligned utterance as the correction, clean it, parse it

    # reducedtokens, allremovedtokens, metadata = reduce(tokens)
    reducedtokens, metadata = reduce(tokens, tree)
    reducedtokensmd = TokenListMD(reducedtokens, [])
    allmetadata += metadata

    alternativemds = getalternatives(reducedtokensmd, tree, '0', correctionparameters, allmetadata)
    # unreducedalternativesmd = [TokenListMD(combinesorted(alternativemd.tokens, allremovedtokens), alternativemd.metadata) for alternativemd in alternativemds]

    intermediateresults = alternativemds if alternativemds != [] else [tokensmd]

    results = []
    for ctmd in intermediateresults:
        # correction = tokenlist2stringlist(ctmd.tokens)
        correction = ctmd.tokens
        themetadata = allmetadata + ctmd.metadata
        results.append((correction, themetadata))


    return results


def getalternatives(origtokensmd: TokenListMD,  tree: SynTree, uttid: UttId,
                    correctionparameters: CorrectionParameters, metadata: List[Meta]):
    methodname = correctionparameters.method.name
    newtokensmd = explanationasreplacement(origtokensmd, tree)
    if newtokensmd is not None:
        tokensmd = newtokensmd
    else:
        tokensmd = origtokensmd

    tokens = tokensmd.tokens
    allmetadata = tokensmd.metadata
    # newtokens = []
    # alternatives = []
    alternativetokenmds = {}
    validalternativetokenmds = {}
    tokenctr = 0
    for token in tokens:
        tokenmd = TokenMD(token, allmetadata)
        alternativetokenmds[tokenctr] = getalternativetokenmds(
            tokenmd, tokens, tokenctr, tree, uttid, correctionparameters)
        validalternativetokenmds[tokenctr] = getvalidalternativetokenmds(
            tokenmd, alternativetokenmds[tokenctr], methodname)
        tokenctr += 1

    # get all the new token sequences
    tokenctr = 0
    lvalidalternativetokenmds = len(validalternativetokenmds)
    altutts: List[List[TokenMD]] = [[]]
    newutts = []
    while tokenctr < lvalidalternativetokenmds:
        for tokenmd in validalternativetokenmds[tokenctr]:
            for utt in altutts:
                newutt = copy.copy(utt)
                newutt.append(tokenmd)
                newutts.append(newutt)
        altutts = newutts
        newutts = []
        tokenctr += 1

    # now turn each sequence of (token, md) pairs into a pair (tokenlist, mergedmetadata)
    newaltuttmds = []
    for altuttmd in altutts:
        if altuttmd != []:
            newaltuttmd = mdlist2listmd(altuttmd)
            newaltuttmds.append(newaltuttmd)

    # basic expansions
    # put off, taken care of in getvalidalternatives:  + [tokensmd]
    allalternativemds = newaltuttmds

    newresults = []
    for uttmd in allalternativemds:
        expansionmds = getexpansions(uttmd)
        newresults += expansionmds
    allalternativemds += newresults

    # combinations of tokens or their alternatives: de kopje, de stukkie, heeft gevalt

    newresults = []
    for uttmd in allalternativemds:
        # utterance = space.join([token.word for token in uttmd.tokens])
        utterance, _ = mkuttwithskips(uttmd.tokens) # this leaves the skip words out
        noskiptokens = [t for t in uttmd.tokens if not t.skip]
        fatntree = fatparse(utterance, noskiptokens)
        newresults += getwrongdetalternatives(uttmd, fatntree, uttid)
    allalternativemds += newresults

    # lonely toe
    newresults = []
    for uttmd in allalternativemds:
        utterance, _ = mkuttwithskips(uttmd.tokens)
        noskiptokens = [t for t in uttmd.tokens if not t.skip]
        fatntree = fatparse(utterance, noskiptokens)
        newresults += lonelytoe(uttmd, fatntree)
    allalternativemds += newresults

    newresults = []
    for uttmd in allalternativemds:
        # utterance = space.join([token.word for token in uttmd.tokens])
        utterance, _ = mkuttwithskips(uttmd.tokens)
        noskiptokens = [t for t in uttmd.tokens if not t.skip]
        fatntree = fatparse(utterance, noskiptokens)
        debug = False
        if debug:
            showtree(fatntree)
        uttalternativemds = getsvacorrections(uttmd, fatntree, uttid)
        newresults += uttalternativemds
    allalternativemds += newresults

    newresults = []
    for uttmd in allalternativemds:
        # utterance = space.join([token.word for token in uttmd.tokens])
        utterance, _ = mkuttwithskips(uttmd.tokens)
        noskiptokens = [t for t in uttmd.tokens if not t.skip]
        fatntree = fatparse(utterance, noskiptokens)
        newresults += correctPdit(uttmd, fatntree, uttid)
    allalternativemds += newresults

    newresults = []
    for uttmd in allalternativemds:
        utterance, _ = mkuttwithskips(uttmd.tokens)
        noskiptokens = [t for t in uttmd.tokens if not t.skip]
        fatntree = fatparse(utterance, noskiptokens)
        newresults += smallclauses(uttmd, fatntree)
        # showtree(fatntree, text='fatntree')
    allalternativemds += newresults

    # final check whether the alternatives are improvements. It is not assumed that the original tokens is included in the alternatives
    finalalternativemds = lexcheck(tokensmd, allalternativemds, methodname)

    return finalalternativemds


skiptemplate = "[ @skip {} ]"


def oldmkuttwithskips(tokens: List[Token], toskip: List[Token]) -> str:
    sortedtokens = sorted(tokens, key=lambda x: x.pos)
    resultlist = []
    for token in sortedtokens:
        if token in toskip:
            resultlist.append(skiptemplate.format(token.word))
        else:
            resultlist.append(token.word)
    result = space.join(resultlist)
    return result


def mkuttwithskips(tokens: List[Token], delete: bool = True) -> Tuple[str, List[Position]]:
    """
    makes a tuple with an utterance in which the skip words are left out (if delete==True or marked for Alpino input
    (if delete==False), and a list of token positions of the words in the utterance
    :param tokens:
    :param delete:
    :return:
    """
    sortedtokens = sorted(tokens, key=lambda x: (x.pos, x.subpos))
    resultlist = []
    tokenposlist = []
    for token in sortedtokens:
        if token.skip:
            if not delete:
                resultlist.append(skiptemplate.format(token.word))
                tokenposlist.append(token.pos + token.subpos)
        else:
            resultlist.append(token.word)
            tokenposlist.append(token.pos + token.subpos)
    result = space.join(resultlist)

    return result, tokenposlist


def OLDgetexpansions(uttmd: TokenListMD) -> List[TokenListMD]:
    '''

    :param uttmd: the list of tokens in the utterance with its metadata
    :return: zero or more alternative lists of tokens with metadata

    The function *getexpansions* generates alternative tokenlists plus metadata for
    words that are contractions and must be expanded into a sequence of multiple tokens.
    It checks whether a word is a contraction by checking whether it occurs in the
    dictionary *basicexpansions* from the module *basicreplacements*

        .. autodata:: sastadev.basicreplacements::basicexpansions
            :no-value:

    '''

    expansionfound = False
    newtokens = []
    tokenctr = 0
    # newtokenctr = 0
    tokenposlist = []
    newmd = uttmd.metadata
    for tokenctr, token in enumerate(uttmd.tokens):
        if token.word in basicexpansions:
            expansionfound = True
            for (rlist, c, n, v) in basicexpansions[token.word]:
                rlisttokenctr = 0
                for rlisttokenctr, rw in enumerate(rlist):
                    if rlisttokenctr == 0:
                        newtoken = Token(rw, token.pos)
                    else:
                        newtoken = Token(rw, token.pos, subpos=rlisttokenctr)
                    newtokens.append(newtoken)
                    tokenposlist.append(token.pos)
                    nwt = Token(space.join(rlist), token.pos)
                meta1 = mkSASTAMeta(token, nwt, n, v, c, subcat=None, penalty=defaultpenalty,
                                    backplacement=bpl_none)
                newmd.append(meta1)

        else:
            newtoken = Token(token.word, token.pos)
            newtokens.append(newtoken)
            tokenposlist.append(token.pos)

    # adapt the metadata
    if expansionfound:
        meta2 = Meta('OrigCleanTokenPosList', tokenposlist, annotatedposlist=[],
                     annotatedwordlist=[], annotationposlist=tokenposlist,
                     annotationwordlist=[], cat=correctionlabels.tokenisation, subcat=None, source=SASTA, penalty=0,
                     backplacement=bpl_none)
        newmd.append(meta2)
        result = [TokenListMD(newtokens, newmd)]
    else:
        result = []

    return result


def getsingleitemexpansions(token: Token, intokenposlist) -> List[Tuple[TokenListMD, List[int]]]:
    lcword = token.word
    outtokenposlist = copy.copy(intokenposlist)
    if lcword in basicexpansions:
        results = []
        for (rlist, c, n, v, p) in basicexpansions[lcword]:
            outtokenposlist = copy.copy(intokenposlist)
            newtokens = []
            newmd = []
            for rlisttokenctr, rw in enumerate(rlist):

                if rlisttokenctr == 0:
                    newtoken = Token(rw, token.pos)
                else:
                    newtoken = Token(rw, token.pos, subpos=rlisttokenctr)
                newtokens.append(newtoken)
                outtokenposlist.append(token.pos)
                nwt = Token(space.join(rlist), token.pos)
                fullpenalty = basepenalties[BASICREPLACEMENTS] + p
            meta1 = mkSASTAMeta(token, nwt, n, v, c, subcat=None, penalty=fullpenalty,
                                backplacement=bpl_none, source=f'{SASTA}/{BASICREPLACEMENTS}')
            newmd.append(meta1)
            result = (TokenListMD(newtokens, newmd), outtokenposlist)
            results.append(result)
    else:
        outtokenposlist.append(token.pos)
        results = [(TokenListMD([token], []), outtokenposlist)]

    return results


def combine(headresult: Tuple[TokenListMD, List[int]], tailresult: Tuple[TokenListMD, List[int]]) \
        -> Tuple[TokenListMD, List[int]]:
    '''

    :param headresult: an  expansion result for the head
    :param tailresult: an expansion result for the tail
    :return: the combination of the head result and the tailresult

    The function *combine* combines a result for the head of an input token list with a result of the tail of
    the input token list.
    It simply concatenates the token lists of the results, and the metadata of the results,
    and generates the tokenposlist for their combination.

    '''
    newtokens = headresult[0].tokens + tailresult[0].tokens
    newmd = headresult[0].metadata + tailresult[0].metadata
    newtokenposlist = tailresult[1]
    result = (TokenListMD(newtokens, newmd), newtokenposlist)
    return result


def getexpansions2(tokenlist: List[Token], intokenposlist: List[int]) -> List[Tuple[TokenListMD, List[int]]]:
    '''

    :param tokenlist: the list of tokens in the utterance
    :param intokenposlist: the list of token positions so far, initially the empty list
    :return: zero or more alternative lists of tuples of
       * tokens with metadata
       * accumulated list of token positions

    The function *getexpansions2* generates alternative tokenlists plus metadata for
    words that are contractions and must be expanded into a sequence of multiple tokens.
    It applies the function *getsingleitemexpansions* to the head (first) element of the *tokenlist* and
    recursively applies itself to the tail of *intokenlist*, after which it combines the results by the *combine* function.

        .. autofunction::  sastadev.corrector::getsingleitemexpansions

        .. autofunction:: sastadev.corrector::combine

    It checks whether a word is a contraction by checking whether it occurs in the
    dictionary *basicexpansions* from the module *basicreplacements*

        .. autodata:: sastadev.basicreplacements::basicexpansions
            :no-value:

    '''
    finalresults = []
    if tokenlist == []:
        outtokenposlist = copy.copy(intokenposlist)
        finalresults = [(TokenListMD([], []), outtokenposlist)]
    else:
        headresults = getsingleitemexpansions(tokenlist[0], intokenposlist)
        for headresult in headresults:
            tailresults = getexpansions2(tokenlist[1:], headresult[1])
            results = [combine(headresult, tailresult)
                       for tailresult in tailresults]
            finalresults += [(TokenListMD(result[0].tokens,
                                          result[0].metadata), result[1]) for result in results]
    return finalresults


def gettokenyield(tokens: List[Token]) -> str:
    words = [token.word for token in tokens]
    result = space.join(words)
    return result


def getexpansions(uttmd: TokenListMD) -> List[TokenListMD]:
    '''

    :param uttmd: the list of tokens in the utterance with its metadata
    :return: a possibly empty list of alternative lists of tokens with metadata

    The function *getexpansions* generates alternative tokenlists plus metadata for
    words that are contractions and must be expanded into a sequence of multiple tokens.

    It does so by a call to the function *getexpansions2*, which recursively generates all alternatives with expansions:

    .. autofunction:: sastadev.corrector::getexpansions2

    '''
    newtokenmds = []

    results = getexpansions2(uttmd.tokens, [])
    for result in results:
        result0yield = gettokenyield(result[0].tokens)
        uttmdyield = gettokenyield(uttmd.tokens)
        if result0yield != uttmdyield:  # otherwise we get unnecessary and undesired duplicates
            tokenposlist = result[1]
            meta2 = Meta('OrigCleanTokenPosList', tokenposlist, annotatedposlist=[],
                         annotatedwordlist=[], annotationposlist=tokenposlist,
                         annotationwordlist=[], cat=correctionlabels.tokenisation, subcat=None, source=SASTA, penalty=0,
                         backplacement=bpl_none)
            newmd = uttmd.metadata
            newmd += result[0].metadata
            newmd.append(meta2)
            newtokenmd = TokenListMD(result[0].tokens, newmd)
            newtokenmds.append(newtokenmd)

    return newtokenmds

    # adapt the metadata
    # finalresults = []
    # for result in results:
    #     meta2 = Meta('OrigCleanTokenPosList', tokenposlist, annotatedposlist=[],
    #                  annotatedwordlist=[], annotationposlist=tokenposlist,
    #                  annotationwordlist=[], cat=correctionlabels.tokenisation, subcat=None, source=SASTA, penalty=defaultpenalty,
    #                  backplacement=bpl_none)
    #     newmd = result.metadata
    #     newmd.append(meta2)
    #     finalresult = [TokenListMD(result.tokens, newmd)]
    #     finalresults.append(finalresult)


def lexcheck(intokensmd: TokenListMD, allalternativemds: List[TokenListMD], methodname:MethodName) -> List[TokenListMD]:
    finalalternativemds = [intokensmd]
    for alternativemd in allalternativemds:
        diff_found = False
        include = True
        intokens = intokensmd.tokens
        outtokens = alternativemd.tokens
        if len(intokens) != len(outtokens):
            diff_found = True
        else:
            for (intoken, outtoken) in zip(intokens, outtokens):
                if intoken != outtoken:
                    diff_found = True
                    if not validword(outtoken.word, methodname):
                        include = False
                        break
        if diff_found and include:
            finalalternativemds.append(alternativemd)
    return finalalternativemds


# moved to metadata
# def mkSASTAMeta(token, nwt, name, value, cat, subcat=None, penalty=defaultpenalty, backplacement=defaultbackplacement):
#    result = Meta(name, value, annotatedposlist=[token.pos],
#                     annotatedwordlist=[token.word], annotationposlist=[nwt.pos],
#                     annotationwordlist=[nwt.word], cat=cat, subcat=subcat, source=SASTA, penalty=penalty,
#                     backplacement=backplacement)
#    return result


def updatenewtokenmds(newtokenmds: List[TokenMD], token: Token, newwords: List[str], beginmetadata: List[Meta],
                      name: str, value: str, cat: str, subcat: Optional[str] = None, source=SASTA,
                      penalty: Penalty = defaultpenalty, backplacement: BackPlacement = defaultbackplacement) \
        -> List[TokenMD]:
    for nw in newwords:
        skipval = True if nw == 'skip' else False
        nwt = Token(nw, token.pos, skip=skipval)
        meta = mkSASTAMeta(token, nwt, name=name, value=value, cat=cat, subcat=subcat, source=source, penalty=penalty,
                           backplacement=backplacement)
        metadata = [meta] + beginmetadata
        newwordtokenmd = TokenMD(nwt, metadata)
        newtokenmds.append(newwordtokenmd)
    return newtokenmds


def multi_updatenewtokenmds(newtokenmds: List[TokenMD], token: Token, newtokens: List[Token], beginmetadata: List[Meta],
                      newmetadata: List[Meta]) -> List[TokenMD]:
    for nwt, nmeta in zip(newtokens, newmetadata):
        metadata = [nmeta] + beginmetadata
        newwordtokenmd = TokenMD(nwt, metadata)
        newtokenmds.append(newwordtokenmd)
    return newtokenmds



# def gettokensplusxmeta(tree: SynTree) -> Tuple[List[Token], List[Meta]]: moved to sastatok.py


def findxmetaatt(xmetalist: List[Meta], name: str, cond: MetaCondition = lambda x: True) -> Optional[Meta]:
    cands = [xm for xm in xmetalist if xm.name == name and cond(xm)]
    if cands == []:
        result = None
    else:
        result = cands[0]
    return result


# def explanationasreplacement(tokensmd: TokenListMD, tree: SynTree) -> Optional[TokenListMD]: moved to sasta_explanation
# some words are known but very unlikely as such
#: The constant *specialdevoicingwords* contains known words that start with a
#: voiceless consonant for which the word starting with the corresponding voiced
#: consonant is much more likely in young children's speech.
specialdevoicingwords = {'fan'}


def isdefdet(token: Token) -> bool:
    if token is None:
        return False
    wordinfos = getwordinfo(token.word)
    for wordinfo in wordinfos:
        (pt, _, infl, lemma) = wordinfo
        if lemma in definite_determiners:
            return True
        if lemma in possessive_determiners:
            return True
        # @@ to be extended  genitive nouns CELEX hardly has information on genetives
        # if nodept == 'n' and nodecase == 'gen':
        #     return True
    return False

def is_adj_e(token: Token) -> bool:
    if token is None:
        return False
    wordinfos = getwordinfo(token.word)
    for wordinfo in wordinfos:
        (pt, _, infl, _) = wordinfo
        if pt == 'adj' and infl in ['E', 'PE', 'CE']:
            return True
    return False

def get_lemma(token: Token, tokenpos:str) -> str:
    if token is None:
        return False
    wordinfos = getwordinfo(token.word)
    for wordinfo in wordinfos:
        (pt, _, _, lemma) = wordinfo
        if pt == tokenpos:
            return lemma
    return token.word


def isnoun(token: Token) -> bool:
    if token is None:
        return False
    wordinfos, _ = getdehetwordinfo(token.word)
    for wordinfo in wordinfos:
        (pt, _, _, _) = wordinfo
        if pt in ['n']:
            return True
    return False


def isnounsg(token: Token) -> bool:
    if token is None:
        return False
    wordinfos, _ = getdehetwordinfo(token.word)
    for wordinfo in wordinfos:
        (_, _, infl, _) = wordinfo
        if infl in ['e', 'de']:
            return True
    return False

def isnounsgneut(token: Token) -> bool:
    if token is None:
        return False
    wordinfos, _ = getdehetwordinfo(token.word)
    for wordinfo in wordinfos:
        (_, dehet, infl, _) = wordinfo
        if (infl == 'e'  and dehet == het) or infl == 'de':
            return True
    return False


def isdimsg(token: Token) -> bool:
    if token is None:
        return False
    wordinfos, _ = getdehetwordinfo(token.word)
    for wordinfo in wordinfos:
        (_, _, infl, _) = wordinfo
        if infl in ['de']:
            return True
    return False


def canhavept(token: Token, wpt: str) -> bool:
    if token is None:
        return False
    wordinfos = getwordinfo(token.word)
    for wordinfo in wordinfos:
        (pt, _, _, _) = wordinfo
        if pt == wpt:
            return True
    return False


def isnounpl(token: Token) -> bool:
    if token is None:
        return False
    wordinfos, _ = getdehetwordinfo(token.word)
    for wordinfo in wordinfos:
        (_, _, infl, _) = wordinfo
        if infl in ['m', 'dm']:
            return True
    return False


def hasgender(token: Token, reqgender: int) -> bool:
    if token is None:
        return False
    wordinfos, _ = getdehetwordinfo(token.word)
    for wordinfo in wordinfos:
        (_, gender, _, _) = wordinfo
        if gender == reqgender:
            return True
    return False

def isinfinitive(token: Token) -> bool:
    if token is None:
        return False
    wordinfos = getwordinfo(token.word)
    for wordinfo in wordinfos:
        (_, _ , infl, _) = wordinfo
        if infl == 'i':
            return True
    return False

def iscomparative(token: Token) -> bool:
    if token is None:
        return False
    wordinfos = getwordinfo(token.word)
    for wordinfo in wordinfos:
        (_, _ , infl, _) = wordinfo
        if 'C' in infl:
            return True
    return False

def issuperlative(token: Token) -> bool:
    if token is None:
        return False
    wordinfos = getwordinfo(token.word)
    for wordinfo in wordinfos:
        (_, _ , infl, _) = wordinfo
        if 'S' in infl:
            return True
    return False


def canbenonnoun(token: Token) -> bool:
    if token is None:
        return False
    wordinfos = getwordinfo(token.word)
    for wordinfo in wordinfos:
        (pt, _ , _, _) = wordinfo
        if pt != 'n':
            return True
    return False


def initdevoicing(token: Token, voiceless: str, voiced: str, methodname: MethodName, newtokenmds: List[TokenMD], beginmetadata: List[Meta]) \
        -> List[TokenMD]:
    '''
    The function *initdevoicing* takes as input *token*, checks whether it is an
    unknown word or a special known word. If the token's word starts with *voiceless*
    it creates a newword with the tokens's word initial character replaced by *voiced*.
    If the result is a known word, *newtokenmds* is updated with the new replacement
    and *beginmetadata*, and it returns *newtokenmds*.

    A known word is *special* if it is contained in the variable *specialdevoicingwords*.

    .. autodata:: sastadev.corrector::specialdevoicingwords

    '''
    # initial s -> z, f -> v
    if not validword(token.word, methodname) or token.word in specialdevoicingwords :
        if token.word[0] == voiceless:
            newword = voiced + token.word[1:]
            if validword(newword, methodname):
                newtokenmds = updatenewtokenmds(newtokenmds, token, [newword], beginmetadata,
                                                name=correctionlabels.pronunciationvariant,
                                                value='Initial {} devoicing'.format(
                                                    voiced),
                                                cat=correctionlabels.pronunciation, backplacement=bpl_word)

    return newtokenmds


def pfauxinnodes(tokennodes: List[SynTree]) -> bool:
    for tokennode in tokennodes:
        tokennodelemma = getattval(tokennode, 'lemma')
        if tokennodelemma in ['hebben', 'zijn']:
            return True
    return False

def adaptpenalty(wrong: str, correct: str, p: Penalty) -> Penalty:
    cc = childescorrections[wrong]
    for hc in cc:
        if hc.correction == correct:
            sumfrq = sum([hc.frequency for hc in cc])
            relfrq = hc.frequency / sumfrq
            penalty = max(1, int(defaultpenalty * (1 - relfrq))) + p
            return penalty
    return p


def nocorrectparse(tree: SynTree) -> bool:
    tops = tree.xpath('.//node[@cat="top"]')
    if len(tops) != 1:
        return False
    top = tops[0]
    realtopchildren = [ node for node in top if  getattval(node, 'pt') not in ['let', 'tsw']]
    result = len(realtopchildren) != 1
    return result

def getalternativetokenmds(tokenmd: TokenMD,  tokens: List[Token], tokenctr: int,
                           tree: SynTree, uttid: UttId, correctionparameters: CorrectionParameters) -> List[TokenMD]:
    methodname = correctionparameters.method.name
    token = tokenmd.token
    beginmetadata = tokenmd.metadata
    newtokenmds: List[TokenMD] = []
    tokennodes = getnodeyield(tree)

    schwandropfound = False
    postviefound = False
    deduplicated = False
    if token.skip:
        return newtokenmds

    # ignore interpunction
    if ispunctuation(token.word):
        return newtokenmds

    # decapitalize initial token  except when it is a known name
    # do  this only for ASTA
    if correctionparameters.method.name in {asta} and tokenctr == 0 and token.word.istitle() and not isa_namepart(
            token.word):
        newword = token.word.lower()

        newtokenmds = updatenewtokenmds(newtokenmds, token, [newword], beginmetadata,
                                        name=correctionlabels.charactercase, value='Lower case', cat=correctionlabels.orthography)

    # dehyphenate
    if not validnotalpinocompoundword(token.word, methodname)  and hyphen in token.word:
        newwords = fullworddehyphenate(token.word, lambda x: validnotalpinocompoundword(x, methodname))
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.dehyphenation, value=correctionlabels.dehyphenation, cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)

    # deduplicate jaaaaa -> ja; heeeeeel -> heel
    if not validword(token.word, methodname) and token.word != 'ee':
        newwords = dutchdeduplicate(token.word, lambda x: validword(x, methodname), exceptions=chatxxxcodes)
        deduplicated = newwords != []
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.emphasis, value='Phoneme lengthening', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)

    # aha oho uhu ehe
    ahapattern = r'([aeouy])h\1'
    ahare = re.compile(ahapattern)
    if not validnotalpinocompoundword(token.word, methodname) and ahare.search(token.word):
        newwords = [ahare.sub(r'\1', token.word)]
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.emphasis, value='Phoneme Duplication', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)
    # iehie ijhij
    iehiepattern = r'(ie|ij)h\1'
    iehiere = re.compile(iehiepattern)
    if not validword(token.word, methodname)  and iehiere.search(token.word):
        newwords = [iehiere.sub(r'\1', token.word)]
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.emphasis, value='Phoneme Duplication', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)

    # basic replacements replace as by als, isse by is
    # here come the replacements
    if token.word in basicreplacements:
        for (r, c, n, v, p) in basicreplacements[token.word]:
            newpenalty = basepenalties[BASICREPLACEMENTS] + adaptpenalty(token.word, r, p-defaultpenalty)
            newwords = [r]
            bpl = bpl_wordlemma if is_er_pronoun(r) and token.word not in ervzvariantsdict else bpl_word
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=n, value=v, cat=c, source=f'{SASTA}/{BASICREPLACEMENTS}',
                                            backplacement=bpl, penalty=newpenalty)

    # final r realized as w weew, ew
    if not validword(token.word, methodname)  and token.word.endswith('w') and \
        validword(f'{token.word[:-1]}r', methodname):
        newwords = [f'{token.word[:-1]}r']
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.informalpronunciation, value='Final r -> w',
                                        cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)
    # aller- misspelled as alle
    if (not validword(token.word, methodname) and
        token.word.startswith('alle') and not token.word.startswith('aller') and
        (token.word.endswith('st') or token.word.endswith('ste')) and
        validword(f'{token.word[4:]}', methodname)):
        newwords = [f'aller{token.word[4:]}']
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.informalpronunciation, value='r-drop',
                                        cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)


    # # r realized as l
    # lpositions =
    # if not known_word(token.word) and token.word.find('l') != -1 and known_word(f'{token.word[:-1]}r'):
    #     newwords = [f'{token.word[:-1]}r']
    #     newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
    #                                     name=correctionlabels.informalpronunciation, value='Final r -> w',
    #                                     cat=correctionlabels.pronunciation,
    #                                     backplacement=bpl_word)



    # wrong past participle emaakt -> gemaakt
    if not validword(token.word, methodname)  and token.word.startswith('e') and validword(f'g{token.word}', methodname):
        newwords = [f'g{token.word}']
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.informalpronunciation, value='Initial g dropped', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)

    # wrong transcription of 's + e-participle past participle  semaakt -> 's emaakt -> is gemaakt
    if not validword(token.word, methodname) and token.word.startswith('se') and \
            validword(f'g{token.word[1:]}', methodname):
        newwords = [f"is g{token.word[1:]}"]
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.informalpronunciation, value='Initial g dropped', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word_delprec)


    # wrong past participle  semaakt -> gemaakt
    if not validword(token.word, methodname) and token.word.startswith('se') and \
            validword(f'g{token.word[1:]}', methodname):
        newwords = [f'g{token.word[1:]}']
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.informalpronunciation, value='Initial g replaced by s', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)

    # wrong past participle  maakt -> gemaakt
    if 0 <= tokenctr < len(tokennodes):
        prevtoken = tokens[tokenctr - 1] if tokenctr > 0 else None
        nexttoken = tokens[tokenctr + 1] if tokenctr < len(tokens) - 1 else None
        thetokennode = tokennodes[tokenctr]
        thetokennodept = getattval(thetokennode, 'pt')
        thetokennodewvorm = getattval(thetokennode, 'wvorm')
        thetokennoderel = getattval(thetokennode, 'rel')
        if thetokennodept == 'ww' and thetokennodewvorm != 'vd' and \
                isa_vd(f'ge{token.word}') and \
                (pfauxinnodes(tokennodes[:tokenctr]) or thetokennoderel == '--') and \
                not isaninftoken(prevtoken) and \
                not isaninftoken(nexttoken):
            newwords = [f'ge{token.word}']
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.morphologicalerror, value='Missing ge prefix', cat=correctionlabels.morphology,
                                            backplacement=bpl_word)
    else:
        tokennodestr = space.join([getattval(n, 'word') for n in tokennodes])
        tokenstr = space.join([token.word for token in tokens])
        settings.LOGGER.error(f'tokenctr has value ({tokenctr}) out of range 0..{len(tokennodes)}\ntokennodes: {tokennodestr}\n tokens:    {tokenstr}')



    moemoetxpath = './/node[@lemma="moe" and @pt!="n" and not(%onlywordinutt%)]'
    expanded_moemoetxpath = expandmacros(moemoetxpath)
    if token.word == 'moe' and tree.xpath(expanded_moemoetxpath) != [] and (
            tokenctr == 0 or tokens[tokenctr - 1].word != 'beetje'):
        newwords = ['moet']
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.informalpronunciation, value='Final t-deletion', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)

    # some words can be a noun or a verb but Alpino always analyses them as a verb, we try a noun as alternative
    if token.word in alt_pt_ww_n_pairdict:
        prevtokennode = tokennodes[tokenctr - 1] if tokenctr > 0 else None
        prevprevtokennode = tokennodes[tokenctr - 2] if tokenctr > 1 else None
        prevprevtokennodept = getattval(prevprevtokennode, 'pt')
        if isdet(prevtokennode) or (prevprevtokennodept in ['adj'] and isdet(prevprevtokennode)):
            newwords = [alt_pt_ww_n_pairdict[token.word]]
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.alternativept, value=newwords[0], cat=correctionlabels.lexicon,
                                            backplacement=bpl_wordlemma)


    # 's and s could be is, but do not try it when followed by ochtends etc
    if token.word in ["'s", "s"] and nexttoken.word not in aposfollowers:
        newwords = ['is']
        valvalue = 'reduced pronunciation'
        catval = correctionlabels.pronunciation
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.informalpronunciation, value=valvalue, cat=catval,
                                        backplacement=bpl_word)


    # clause intial maar must be parsed as conjunction not as an adverb: we replace it by "en" to avoid the ambiguity
    if token.word == 'maar':
        initialmaars = tree.xpath(initialmaarvgxpath)
        for initialmaar in initialmaars:
            if initialmaar == tokennodes[tokenctr]:
                newwords = ['en']
                newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.maarambiguityavoidance, value='en', cat=correctionlabels.ambiguityavoidance,
                                        backplacement=bpl_wordlemma, penalty=5)

    # dee -> deze of deed
    if token.word == 'dee':
        newwords = ['deze']
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.wrongpronunciation, value='Coda reduction', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word, penalty=5)
        newwords = ['deed']
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.informalpronunciation, value='Final t-deletion', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word)

    # beurt -> gebeurt
    if token.word == 'beurt':
        newwords = ['gebeurt']
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.wrongpronunciation, value='Unstressed syllable drop',
                                        cat=correctionlabels.pronunciation,
                                        backplacement=bpl_word, penalty=5)

    if token.word in leggendict and nocorrectparse(tree):
        newwords = [leggendict[token.word]]
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.regionalvariantorlexicalerror,
                                        value=correctionlabels.leggenliggen,
                                        cat=correctionlabels.lexicon,
                                        backplacement=bpl_word, penalty=5)



    # e or schwa -> een de het dat, deletio; en rejected, dat(vg) only after a verb
    nexttoken = tokens[tokenctr+1] if tokenctr < len(tokens) - 1 else None
    prevtoken = tokens[tokenctr - 1] if tokenctr > 0 else None
    if token.word in ['e', 'ə']:
        if isnounsg(nexttoken) and nexttoken.word not in e2een_excluded_nouns:
            newwords = ['een']
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.wrongpronunciation, value=correctionlabels.finalndrop,
                                            cat=correctionlabels.pronunciation,
                                            subcat=correctionlabels.codareduction,
                                            backplacement=bpl_word, penalty=mp(30))

        if hasgender(nexttoken, de)  or isnounpl(nexttoken):
            newwords = ['de']
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.wrongpronunciation,
                                            value=correctionlabels.onsetreduction,
                                            cat=correctionlabels.pronunciation,
                                            subcat=correctionlabels.onsetreduction,
                                            backplacement=bpl_word, penalty=mp(40))


        if ((hasgender(nexttoken, het) or isdimsg(nexttoken) )and isnounsg(nexttoken)) or \
            (prevtoken is not None and prevtoken.word == 'aan' and isinfinitive(nexttoken)) or \
            canbenonnoun(nexttoken):
            newwords = ['het']
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.wrongpronunciation,
                                            value=correctionlabels.onsetandcodadrop,
                                            cat=correctionlabels.pronunciation,
                                            subcat=correctionlabels.onsetandcodadrop,
                                            backplacement=bpl_word, penalty=mp(50))

         # it is expected that replacement by dat as a determiner or pronoun is always beaten by 'het'. so this will
        # only be selected when dat has a different function, e.g. subordinate conjuntion as in TD24,9. This is
        # false. Instead we conditioned it to apply only after verbs: still goes wromg for hebben e auto

        # if canhavept(prevtoken,'ww'):
        #     newwords = ['dat']
        #     newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
        #                                     name=correctionlabels.wrongpronunciation,
        #                                     value=correctionlabels.onsetandcodadrop,
        #                                     cat=correctionlabels.pronunciation,
        #                                     subcat=correctionlabels.onsetandcodadrop,
        #                                     backplacement=bpl_word, penalty=mp(90))


        if hasgender(nexttoken, het) and isnounsg(nexttoken):
            newwords = ['het']
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.wrongpronunciation,
                                            value=correctionlabels.onsetandcodadrop,
                                            cat=correctionlabels.pronunciation,
                                            subcat=correctionlabels.onsetandcodadrop,
                                            backplacement=bpl_word, penalty=mp(50))


        # if True:
        #     newwords = ['en']
        #     newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
        #                                     name=correctionlabels.wrongpronunciation,
        #                                     value=correctionlabels.finalndrop,
        #                                     cat=correctionlabels.pronunciation,
        #                                     subcat=correctionlabels.codareduction,
        #                                     backplacement=bpl_word, penalty=mp(60))

        if True:
            newwords = ['']
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.unknownword,
                                            value=correctionlabels.unknownword,
                                            cat=correctionlabels.pronunciation,
                                            subcat=correctionlabels.unknownword,
                                            backplacement=bpl_none, penalty=mp(70))

    if token.word in ['ee']:
        if isnounsg(nexttoken):
            newwords = ['een']
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.wrongpronunciation, value=correctionlabels.finalndrop,
                                            cat=correctionlabels.pronunciation,
                                            subcat=correctionlabels.codareduction,
                                            backplacement=bpl_word, penalty=mp(30))

    if token.word in ['n', 't']:
        newwords = [f"'{token.word}"]
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.spellingcorrection, value=correctionlabels.apomiss,
                                        cat=correctionlabels.orthography,
                                        subcat=correctionlabels.apomiss,
                                        backplacement=bpl_word, penalty=mp(30))

        nexttoken = tokens[tokenctr + 1] if tokenctr < len(tokens) - 1 else None
        if nexttoken is None or not isnoun(nexttoken):
            newwords = ['']
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=EXTRAGRAMMATICAL, value=filled_pause,
                                            cat=correctionlabels.syntax,
                                            backplacement=bpl_word, penalty=mp(100))


    # een blauwe tentje -> een blauw tentje; een grotere tentje -> een groter tentje
    # print(getxsid(tree))
    token_node = tokennodes[tokenctr]
    if tokenctr < len(tokens):
        if is_adj_e(token) and \
           not issuperlative(token) and \
           isnounsgneut(nexttoken) and \
           (prevtoken is None or not isdefdet(prevtoken)):
            newwords = [token.word[:-1]] if iscomparative(token) else [get_lemma(token, 'adj')]
            if newwords != [token.word]:    # otherwise we will have an infinite recursion eg. andere -> andere
                # ASTA_06 13
                newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                name=correctionlabels.agreementerror, value=correctionlabels.incorrect_e_suffix,
                                                cat=correctionlabels.syntax,
                                            backplacement=bpl_node, penalty=mp(100))

    # words unknown to Alpino e.g *gymmen* is replaced by *trainen*
    if token.word in wordsunknowntoalpinolexicondict:
        for newword in wordsunknowntoalpinolexicondict[token.word]:
            newwords = [newword]
            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                    name=correctionlabels.wordunknowntoalpino, value=correctionlabels.unknownword,
                                            cat=correctionlabels.lexicon,
                                    backplacement=bpl_wordlemma)


    # replace unknown words by similar words from the context --tarsp and stap only, for asta more needs to be doen
    if not validword(token.word, methodname) and correctionparameters.method.name in {tarsp, stap}:
        xsid = getxsid(tree)
        thecontextdict = correctionparameters.contextdict
        if xsid in thecontextdict and token.word in thecontextdict[xsid]:
            (prevwords, postwords) = thecontextdict[xsid][token.word]
            newcandidates = postwords if postwords != [] else prevwords
            for newcandidate in newcandidates:
                if newcandidate == token.word:   # otherwasie we will have an eternal loop
                    continue
                penalty = basepenalties[CONTEXT]
                newwords = [newcandidate]
                newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                name=correctionlabels.contextcorrection,
                                                value=correctionlabels.unknownword, cat=correctionlabels.lexicon,
                                                source=f'{SASTA}/{CONTEXT}', backplacement=bpl_word, penalty=penalty)

    # find document specific replacements
    if not validword(token.word, methodname) and \
            token.word in correctionparameters.thissamplecorrections and \
            token.word not in childescorrectionsexceptions:
        cc = correctionparameters.thissamplecorrections[token.word]
        sumfrq = sum([hc.frequency for hc in  cc])
        for hc in cc:
            relfrq = hc.frequency / sumfrq
            penalty = basepenalties[THISSAMPLECORRECTIONS] + max(1, int(defaultpenalty * (1 - relfrq)))
            newwords = [hc.correction]
            if (token.word, hc.correction) not in basicreplacementpairs and hc.correction != '':  # no deletions
                if hc.correctiontype == correctionlabels.noncompletion:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.noncompletion, value='', cat=correctionlabels.pronunciation,
                                                    source=f'{SASTA}/{THISSAMPLECORRECTIONS}',
                                                    backplacement=bpl_word, penalty=penalty)
                elif hc.correctiontype == correctionlabels.replacement:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.replacement, value='', cat='TBD',
                                                    source=f'{SASTA}/{THISSAMPLECORRECTIONS}',
                                                    backplacement=bpl_word, penalty=penalty)
                elif hc.correctiontype == correctionlabels.explanation:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.explanation, value='', cat='TBD',
                                                    source=f'{SASTA}/{THISSAMPLECORRECTIONS}',
                                                    backplacement=bpl_word, penalty=penalty)

    # find correction from all samples processed so far
    if methodname in [tarsp, stap] and \
        not validword(token.word, methodname) and \
        token.word in correctionparameters.allsamplecorrections and \
            token.word not in childescorrectionsexceptions:
        cc = correctionparameters.allsamplecorrections[token.word]
        sumfrq = sum([hc.frequency for hc in cc])
        for hc in cc:
            relfrq = hc.frequency / sumfrq
            penalty = basepenalties[ALLSAMPLECORRECTIONS] + max(1, int(defaultpenalty * (1 - relfrq)))
            newwords = [hc.correction]
            if (token.word, hc.correction) not in basicreplacementpairs and hc.correction != '':
                if hc.correctiontype == correctionlabels.noncompletion:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.noncompletion, value='', cat=correctionlabels.pronunciation,
                                                    source=f'{SASTA}/{ALLSAMPLECORRECTIONS}',
                                                    backplacement=bpl_word, penalty=penalty)
                elif hc.correctiontype == correctionlabels.replacement:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.replacement, value='', cat='TBD',
                                                    source=f'{SASTA}/{ALLSAMPLECORRECTIONS}',
                                                    backplacement=bpl_word, penalty=penalty)
                elif hc.correctiontype == correctionlabels.explanation:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.explanation, value='', cat='TBD',
                                                    source=f'{SASTA}/{ALLSAMPLECORRECTIONS}',
                                                    backplacement=bpl_word, penalty=penalty)


    # merge the corrections from this sampe with the samplecorrections and update the file NOT HERE. moved
    # mergedsamplecorrections = mergecorrections(samplecorrections, thissamplecorrections )
    # putcorrections(mergedsamplecorrections, samplecorrectionsfullname)
    # find organisation specific replacements

    # find childes replacements, preferably with vocabulary from the same age

    if correctionparameters.options.dohistory and \
            methodname in [tarsp, stap] and not validword(token.word, methodname) and \
            token.word in childescorrections and \
            token.word not in childescorrectionsexceptions:
        cc = childescorrections[token.word]
        sumfrq = sum([hc.frequency for hc in cc])
        for hc in cc:
            relfrq = hc.frequency / sumfrq
            penalty = basepenalties[HISTORY] + max(1, int(defaultpenalty * (1 - relfrq)))
            newwords = [hc.correction]
            if (token.word, hc.correction) not in basicreplacementpairs  and hc.correction != '':
                if hc.correctiontype == correctionlabels.noncompletion:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.noncompletion, value='', cat=correctionlabels.pronunciation,
                                                    source=f'{SASTA}/{HISTORY}',
                                                    backplacement=bpl_word, penalty=penalty)
                elif hc.correctiontype == correctionlabels.replacement:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.replacement, value='', cat='TBD',
                                                    source=f'{SASTA}/{HISTORY}',
                                                    backplacement=bpl_word, penalty=penalty)
                elif hc.correctiontype == correctionlabels.explanation:
                    newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                                    name=correctionlabels.explanation, value='', cat='TBD',
                                                    source=f'{SASTA}/{HISTORY}',
                                                    backplacement=bpl_word, penalty=penalty)

                # gaatie
    if not validword(token.word, methodname):
        newwords = gaatie(token.word)
        if newwords != []:
            postviefound = True
        newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                        name=correctionlabels.wordcombination, value='Cliticisation', cat=correctionlabels.pronunciation,
                                        backplacement=bpl_none)

    # extend to gaat-ie -- done

    # dediacritisize

    # iedims
    # only -ie form: 'duppie', 'jochie', 'jonkie', 'juffie', 'makkie', 'moppie', 'saffie',
    # 'sjekkie', 'slapie', 'spekkie', 'ukkie' (?) voor/in het echie (*echtje)

    # common in standard written language: 'bakkie', 'duppie', 'fikkie', 'gympie', 'jochie', 'jonkie',
    # 'juffie', 'koppie', 'moppie', 'punkie', 'saffie', 'sjekkie', 'slapie', 'spekkie', 'stekkie', 'ukkie', 'wijfie'

    knowniedimwords = ['bakkie', 'drukkie', 'duppie', 'fikkie', 'gympie', 'koppie', 'kwassie',
                       'moppie', 'punkie', 'saffie',   'stekkie', 'wijfie']


    if (not validnotalpinocompoundword(token.word, methodname) or token.word in knowniedimwords) and \
            (token.word.endswith('ie') or token.word.endswith('ies')):
        newwords = getjeforms(token.word)
        for newword in newwords:
            if validword(newword, methodname):
                newtokenmds = updatenewtokenmds(newtokenmds, token, [newword], beginmetadata,
                                                name=correctionlabels.regionalform, value='ieDim', cat=correctionlabels.morphology, backplacement=bpl_word)

    # overregularised verb forms: gevalt -> gevallen including  incl  wrong verb forms: gekeekt -> gekeken
    if not validword(token.word, methodname):
        nwms = correctinflection(token.word)
        for nw, metavalue in nwms:
            if validword(nw, methodname):
                newtokenmds += updatenewtokenmds(newtokenmds, token, [nw], beginmetadata,
                                                 name=correctionlabels.morphologicalerror, value=metavalue,
                                                 cat=correctionlabels.morphology,
                                                 backplacement=bpl_word)

    # wrong verb forms: gekeekt -> gekeken: done!

    # me ze (grote/oudere/ kleine) moeder /vader/zusje/ broer -> mijn me is done by Alpino, here we do ze
    # next xpath does not work because it must be preceded by a . !!
    # zexpathmodel = """//node[@word="ze" and @begin={begin} and (@rel="--"  or (@rel="obj1" and parent::node[@cat="pp"])) and @end = ancestor::node[@cat="top"]/descendant::node[@pt="n"]/@begin]"""
    if token.word == 'ze' or token.word == 'su':
        # find the node that corresponds to this token in the tree
        # zexpath = zexpathmodel.format(begin=str(tokenctr))
        # zenode = find1(tree, zexpath)
        tokennodes = getnodeyield(tree)
        zenode = tokennodes[tokenctr]
        if tokenctr < len(tokens) - 1:
            nexttoken = tokens[
                tokenctr + 1]  # do not take it from the tree because it may have been replaced by something else, e.g. avoid: ze dee -> ze deed -/-> z'n deed!
            zerel = getattval(zenode, 'rel')
            zeparent = zenode.getparent()
            zeparentcat = getattval(zeparent, 'cat')
            # nextpt = getattval(nextnode, 'pt')
            nexttokeninfo = getwordinfo(nexttoken.word)
            nexttokenpts = {pt for (pt, _, _, _) in nexttokeninfo}
            if (zerel == '--' or zerel == 'mwp' or (zerel == 'obj1' and zeparentcat == 'pp')) and 'n' in nexttokenpts:
                newword = "z'n"
                newtokenmds = updatenewtokenmds(newtokenmds, token, [newword], beginmetadata,
                                                name=correctionlabels.pronunciationvariant, value='N-less informal possessive pronoun',
                                                cat=correctionlabels.pronunciation, backplacement=bpl_word)

    # e-> e(n)
    if not validword(token.word, methodname) and token.word not in basicreplacements and token.word not in enexceptions:
        if endsinschwa(token.word) and not monosyllabic(token.word):
            newword = token.word + 'n'
            if validword(newword, methodname):
                schwandropfound = True
                newtokenmds = updatenewtokenmds(newtokenmds, token, [newword], beginmetadata,
                                                name=correctionlabels.pronunciationvariant, value='N-drop after schwa',
                                                cat=correctionlabels.pronunciation, backplacement=bpl_word)

    # initial s -> z
    newtokenmds = initdevoicing(token, 's', 'z', methodname, newtokenmds, beginmetadata)
    # initial f -> v
    newtokenmds = initdevoicing(token, 'f', 'v', methodname, newtokenmds, beginmetadata)

    # replaceambiguous words with one reading not known by the child by a nonambiguous word with the same properties
    if correctionparameters.method.name in {'tarsp', 'stap'}:
        if token.word in disambiguationdict:
            cond, newword = disambiguationdict[token.word]
            if cond(token, tree):
                newtokenmds = updatenewtokenmds(newtokenmds, token, [newword], beginmetadata,
                                                name=correctionlabels.disambiguation, value='Avoid unknown reading',
                                                cat=correctionlabels.lexicon, backplacement=bpl_wordlemma)

    dupvowel = '[aeou]'
    aasre = rf'{dupvowel}\1s$'
    vvs = {'aas', 'oos', 'ees', 'uus'}
    # Lauraas -> Laura's; autoos -> auto's
    if not validword(token.word, methodname) and token.word[-3:] in vvs and validword(token.word[:-2], methodname):
        newword = f"{token.word[:-2]}'s"
        newtokenmds = updatenewtokenmds(newtokenmds, token, [newword], beginmetadata,
                                        name=correctionlabels.spellingcorrection, value='Missing Apostrophe',
                                        cat=correctionlabels.orthography, backplacement=bpl_word)


    # babies -> baby's, babietje(s) -> baby'tje(s)
    if not validword(token.word, methodname) and isbabyword(token.word) and \
            validword(getbabylemma(token.word), methodname):
        newword = correctbaby(token.word)
        newtokenmds = updatenewtokenmds(newtokenmds, token, [newword], beginmetadata,
                                        name=correctionlabels.spellingcorrection,
                                        value=errormsgsep.join(['Missing Apostrophe',"Incorrect y-ie alternation" ]),
                                        cat=correctionlabels.orthography, backplacement=bpl_word,
                                        penalty=-defaultpenalty)   # we reward this change rather than penalizing it

    # ...en -> e: groten  -> grote (if adjective); goten -> grote

    # drop e at the end incl duplicated consonants (ooke -> ook; isse -> is ? DOne, basicreplacements

    # losse e -> een / het / de / drop

    # replace unknown part1+V verb by the most frequent part2+verb in CHILDES
    # e.g opbijten -> afbijten
    if not validword(token.word, methodname):
        issvp, thesvp = startswithsvp(token.word)
        part2 = token.word[len(thesvp):]
        if issvp and isaverb(part2):
            newcandidates = [(f'{svp}{part2}', allfrqdict[f'{svp}{part2}']) for svp in separable_prefixes if svp != thesvp
                             and f'{svp}{part2}' in allfrqdict]
            sortednewcandidates = sorted(newcandidates, key= lambda x: x[1], reverse=True )
            if sortednewcandidates != []:
                newwords = [sortednewcandidates[0][0]]
            else:
                newwords = []

            newtokenmds = updatenewtokenmds(newtokenmds, token, newwords, beginmetadata,
                                            name=correctionlabels.unknownwordsubstitution, value=token.word,
                                            cat=correctionlabels.lexicon, backplacement=bpl_word, source=f'{SASTA}/{BASICREPLACEMENTS}')



    if correctionparameters.options.dospellingcorrection  and \
             not validword(token.word, methodname) and applyspellingcorrectionisok(token.word) and \
            not schwandropfound and not postviefound and not token.word[0].isupper() and not deduplicated and \
            not(token.word.endswith('ie') or token.word.endswith('ies')) and token.word[-3:] not in vvs:
        if correctionparameters.method.name in {'tarsp', 'stap'}:
            corrtuples = children_correctspelling(token.word, children_correctionsdict, max=5)
            subsource = CHILDRENSPELLINGCORRECTION
        elif correctionparameters.method.name in {'asta'}:
            corrtuples = []
            subsource = ADULTSPELLINGCORRECTION
            # put off because it causes a lot of errors: the X-words should all have been removed
            # corrtuples = adult_correctspelling(token.word, adult_correctionsdict, max=5)
        else:
            corrtuples = []
        for corr, penalty in corrtuples:
            newpenalty = basepenalties[subsource] + penalty
            if corr != token.word and validword(corr, methodname):
                newtokenmds = updatenewtokenmds(newtokenmds, token, [corr], beginmetadata,
                                                name=correctionlabels.spellingcorrection, value=corr,
                                                cat=correctionlabels.orthography,
                                                source=f'{SASTA}/{subsource}',
                                                backplacement=bpl_word, penalty=newpenalty)

    for newtokenmd in newtokenmds:
        morenewtokenmds = getalternativetokenmds(
            newtokenmd, tokens, tokenctr, tree, uttid, correctionparameters)
        newtokenmds += morenewtokenmds

    return newtokenmds

def applyspellingcorrectionisok(word):
    result = word not in basicreplacements and word not in basicexpansions and \
             len(word) > 4 and word not in enexceptions
    return result

def getvalidalternativetokenmds(tokenmd: TokenMD, newtokenmds: List[TokenMD], methodname:MethodName) -> List[TokenMD]:
    validnewtokenmds = [
        tokenmd for tokenmd in newtokenmds if validword(tokenmd.token.word, methodname)]
    # and now we add the original tokenmd
    validnewtokenmds += [tokenmd]
    return validnewtokenmds



def gaatie(word: str) -> List[str]:
    '''
    The function *gaatie*
    * replaces a word of the form *X-ie* by the string f'{X} ie' if X is a verb form
    * replaces a word of the form *XVttie* by the string f'{X}{V}t ie where V is vowel and XVt is a verb form
    * replaces  a word that matches with  *gaatiepattern*  (e.g.
    *gaatie*) by a sequence of two words where the first word equals word[:-2] (
    *gaat*) and is a known word and the second word equals word[-2:] (*ie*).

    .. autodata:: sastadev.corrector::gaatiepattern
    '''
    results = []
    # kan-ie, moet-ie, gaat-ie, wil-ie
    if word.endswith('-ie') and informlexicon(word[:-3]):
        result = space.join([word[:-3], 'ie'])
        results.append(result)
    # moettie, gaattie,
    if gaattiere.match(word) and informlexicon(word[:-3]):
        result = space.join([word[:-3], 'ie'])
        results.append(result)
    if gaatiere.match(word):
        # and if it is a verb this is essential because now tie is also split into t ie
        if informlexicon(word[:-2]):
            result = space.join([word[:-2], word[-2:]])
            results.append(result)
    return results


def oldgaatie(word: str) -> List[str]:
    '''
    The function *gaatie* replaces  a word that matches with  *gaatiepattern*  (e.g.
    *gaatie*) by a sequence of two words where the first word equals word[:-2] (
    *gaat*) and is a known word and the second word equals word[-2:] (*ie*).

    .. autodata:: sastadev.corrector::gaatiepattern
    '''
    results = []
    if gaatiere.match(word):
        # and if it is a verb this is essential because now tie is also split into t ie
        if informlexicon(word[:-2]):
            result = space.join([word[:-2], word[-2:]])
            results.append(result)
    return results


def old_getwrongdetalternatives(tokensmd: TokenListMD, tree: SynTree, uttid: UttId) -> List[TokenListMD]:
    '''
    The function *getwrongdetalternatives* takes as input a TokenListMD *tokensmd*,  the
    original parse of the utterance (*tree*) and the *uttid* of the utterance.

    It inspects each token in the token list of *tokensmd* that should not be skipped
    and that is a utrum determiner. If the token that immediately follows this
    determiner is not a token to be ignored we obtain the gender properties of the
    token's word (there can be multiple if it is ambiguous). If one of the properties
    is neuter gender and none is uter, then the uter determiner is replaced by its neuter
    variant as a new alternative.

    The token following must be ignored if it has the property *skip=True* or if it
    belongs to words that would lead to wrong corrections, as specified in the constant
    *wrongdet_excluded_words*:

    .. autodata:: sastadev.corrector::wrongdet_excluded_words

    The properties of the token following are determined by the function
    *getdehetwordinfo* from the module *alpino*:

    .. autofunction:: sastadev.alpino::getdehetwordinfo
    '''
    correctiondone = False
    tokens = tokensmd.tokens
    metadata = tokensmd.metadata
    ltokens = len(tokens)
    tokenctr = 0
    newtokens = []
    while tokenctr < ltokens:
        token = tokens[tokenctr]
        if not token.skip and token.word in dets[de] and tokenctr < ltokens - 1:
            nexttoken = tokens[tokenctr + 1]
            # we want to exclude some words
            if nexttoken.skip:
                wordinfos: List[WordInfo] = []
            elif nexttoken.word in wrongdet_excluded_words:
                wordinfos = []
            else:
                wordinfos, _ = getdehetwordinfo(nexttoken.word)
            if wordinfos != []:
                for wordinfo in wordinfos:  # if there are multiple alternatives we overwrite and therefore get the last alternative
                    (pos, dehet, infl, lemma) = wordinfo
                    if dehet == het and infl in ['e', 'de']:
                        # newcurtoken = replacement(token, swapdehet(token))
                        newcurtokenword = swapdehet(token.word)
                        newcurtoken = Token(newcurtokenword, token.pos)
                        meta = mkSASTAMeta(token, newcurtoken, name=correctionlabels.grammarerror, value='deheterror',
                                           cat=correctionlabels.error,
                                           backplacement=bpl_node)
                        metadata.append(meta)
                        correctiondone = True
                    else:
                        newcurtokenword = token.word
                newtokens.append(Token(newcurtokenword, token.pos))
            else:
                newcurtokenword = token.word
                newtokens.append(token)
        else:
            newtokens.append(token)
        tokenctr += 1
    result = TokenListMD(newtokens, metadata)
    if correctiondone:
        results = [result]
    else:
        results = []
    return results


def getwrongdetalternatives(tokensmd: TokenListMD, tree: SynTree, uttid: UttId) -> List[TokenListMD]:
    '''
    The function *getwrongdetalternatives* takes as input a TokenListMD *tokensmd*,  the
    original parse of the utterance (*tree*) and the *uttid* of the utterance.

    It inspects each token in the token list of *tokensmd* that should not be skipped
    and that is a utrum determiner. If the token that immediately follows this
    determiner is not a token to be ignored we obtain the gender properties of the
    token's word (there can be multiple if it is ambiguous). If one of the properties
    is neuter gender and none is uter, then the uter determiner is replaced by its neuter
    variant as a new alternative.

    The token following must be ignored if it has the property *skip=True* or if it
    belongs to words that would lead to wrong corrections, as specified in the constant
    *wrongdet_excluded_words*:

    .. autodata:: sastadev.corrector::wrongdet_excluded_words

    The properties of the token following are determined by the function
    *getdehetwordinfo* from the module *alpino*:

    .. autofunction:: sastadev.alpino::getdehetwordinfo
    '''
    correctiondone = False
    tokens = tokensmd.tokens
    metadata = tokensmd.metadata
    ltokens = len(tokens)
    tokenctr = 0
    newtokens = []
    thedets = dets[de] + dets[het]
    while tokenctr < ltokens:
        token = tokens[tokenctr]
        if not token.skip and token.word in thedets and tokenctr < ltokens - 1:
            nexttoken = tokens[tokenctr + 1]
            # we want to exclude some words
            if nexttoken.skip:
                wordinfos: List[WordInfo] = []
            elif nexttoken.word in wrongdet_excluded_words:
                wordinfos = []
            else:
                wordinfos, _ = getdehetwordinfo(nexttoken.word)
            if wordinfos != []:
                for wordinfo in wordinfos:  # if there are multiple alternatives we overwrite and therefore get the last alternative
                    (pos, dehet, infl, lemma) = wordinfo
                    if token.word in dets[de]  and ((dehet == het and infl in ['e', 'de']) or 'de' in infl):
                        # newcurtoken = replacement(token, swapdehet(token))
                        newcurtokenword = swapdehet(token.word)
                        newcurtoken = Token(newcurtokenword, token.pos)
                        meta = mkSASTAMeta(token, newcurtoken, name=correctionlabels.grammarerror, value='deheterror', cat=correctionlabels.error,
                                           backplacement=bpl_node)
                        metadata.append(meta)
                        correctiondone = True
                    elif token.word in dets[het]  and ((dehet == de and infl in ['e']) or infl in ['m', 'dm']):
                        # newcurtoken = replacement(token, swapdehet(token))
                        newcurtokenword = swapdehet(token.word)
                        newcurtoken = Token(newcurtokenword, token.pos)
                        meta = mkSASTAMeta(token, newcurtoken, name=correctionlabels.grammarerror, value='hetdeerror', cat=correctionlabels.error,
                                           backplacement=bpl_node)
                        metadata.append(meta)
                        correctiondone = True

                    else:
                        newcurtokenword = token.word
                newtokens.append(Token(newcurtokenword, token.pos))
            else:
                newcurtokenword = token.word
                newtokens.append(token)
        else:
            newtokens.append(token)
        tokenctr += 1
    result = TokenListMD(newtokens, metadata)
    if correctiondone:
        results = [result]
    else:
        results = []
    return results


def getindezemwp(prevtokennode: SynTree, tokennode: SynTree) -> bool:
    ok = True
    ok = ok and getattval(prevtokennode, 'lemma') in {'in'}
    ok = ok and getattval(prevtokennode, 'rel') in {'mwp'}
    ok = ok and getattval(tokennode, 'lemma') in {'deze'}
    ok = ok and getattval(tokennode, 'rel') in {'mwp'}
    return ok


def correctPdit(tokensmd: TokenListMD, tree: SynTree, uttid: UttId) -> List[TokenListMD]:
    '''
    The function *correctPdit* replaces demonstrative pronouns immediately preceded by
    an adposition by the pronoun *hem*. It sets the value of the *backplacement*
    attribute of the metadata to *bpl_node* so that it will be replaced again by the
    original node after the parse has been done, unless the original parse contained the multiword
    unit *in deze*. Then the *backplacement* attribute gets the value *bpl_indeze* so
    that in a later stage some special replacements will be performed.

    The function takes as input:

    * *tokensmd* of type *TpkenListMD* : the list of tokens wit hassociated metadata

    *tree* of type *SynTree*: the parse of the original utterance

    *uttid* of type *UttId*: the utterance identifier of the utterance (currently not
    used)

    It yields a list  containing the alternatives generated (of type List[TokenListMD].
    '''
    correctiondone = False
    tokennodes = getnodeyield(tree)
    rawtokens = tokensmd.tokens
    tokens = [t for t in rawtokens if not t.skip]
    metadata = tokensmd.metadata
    newtokens = []
    tokenctr = 0
    nonskiptokenctr = 0
    prevtoken = None
    themap = mktoken2nodemap(tokens, tree)
    for token in rawtokens:
        if token.skip:
            newtokens.append(token)
            continue
        # tokennode = next(filter(lambda x: getattval(x, 'begin') == str(
        #            token.pos + token.subpos), tokennodes), None)
        thekey = token.pos + token.subpos
        if thekey in themap:
            tokennode = themap[thekey]
        else:
            settings.LOGGER.error(f'No node found for token position {thekey} in {gettokenpos_str(tree)}. themap='
                                  f'{str(themap)}.')
            prevtoken = token
            continue
        tokenlemma = getattval(tokennode, 'lemma')
        if not token.skip and prevtoken is not None and not prevtoken.skip and tokenlemma in {'dit', 'dat', 'deze',
                                                                                              'die'}:
            tokenrel = getattval(tokennode, 'rel')
            tokenpt = getattval(tokennode, 'pt')
            prevtokennode = tokennodes[nonskiptokenctr - 1] if tokenctr > 0 else None
            if prevtokennode is not None:
                prevpt = getattval(prevtokennode, 'pt')
                prevparent = prevtokennode.getparent()
                prevparentrel, prevparentcat = getattval(
                    prevparent, 'rel'), getattval(prevparent, 'cat')
                indezemwp = getindezemwp(prevtokennode, tokennode)
                if (prevpt == 'vz' and prevparentcat != 'pp' and tokenrel not in {'det'} and tokenpt == 'vnw') or \
                        indezemwp:
                    newtoken = Token('hem', token.pos, subpos=token.subpos)
                    bpl = bpl_indeze if indezemwp else bpl_node
                    meta = mkSASTAMeta(token, newtoken, name=correctionlabels.alpinoimprovement, value='hem',
                                       cat=correctionlabels.alpinoimprovement,
                                       backplacement=bpl, penalty=15)
                    metadata.append(meta)
                    newtokens.append(newtoken)
                    correctiondone = True
                else:
                    newtokens.append(token)
            else:
                newtokens.append(token)
        else:
            newtokens.append(token)
        tokenctr += 1
        if not token.skip:
            nonskiptokenctr += 1
        prevtoken = token
    result = TokenListMD(newtokens, metadata)
    if correctiondone:
        results = [result]
    else:
        results = []
    return results


def parseas(w: str, code: str) -> str:
    result = '[ @add_lex {} {} ]'.format(code, w)
    return result


def swapdehet(dedet: str) -> Optional[str]:
    if dedet in dets[de]:
        deindex = dets[de].index(dedet)
    else:
        deindex = -1
    if dedet in dets[het]:
        hetindex = dets[het].index(dedet)
    else:
        hetindex = -1
    if deindex >= 0:
        result = dets[het][deindex]
    elif hetindex >= 0:
        result = dets[de][hetindex]
    else:
        result = None
    return result


def outputalternatives(tokens, alternatives, outfile):
    for el in alternatives:
        print(tokens[el], slash.join(alternatives[el]), file=outfile)


def mkchatutt(intokens: List[str], outtokens: List[str]) -> List[str]:
    result = []
    for (intoken, outtoken) in zip(intokens, outtokens):
        newtoken = intoken if intoken == outtoken else replacement(
            intoken, outtoken)
        result.append(newtoken)
    return result


def altmkchatutt(intokens: List[str], outtoken: str) -> List[str]:
    result = []
    for intoken in intokens:
        newtoken = intoken if intoken == outtoken else replacement(
            intoken, outtoken)
        result.append(newtoken)
    return result
