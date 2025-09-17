import copy
import re
from typing import List, Optional, Tuple

from auchann.align_words import AlignmentSettings, align_words
from lxml import etree

# import find1, iswordnode, getattval
import sastadev.stringfunctions as strf
import sastadev.treebankfunctions as tbf
from sastadev.auchannsettings import settings as auchannsettings
from sastadev.chatundo import chatundo
from sastadev.cleanCHILDEStokens import cleantext
from sastadev.conf import settings as sdsettings
from sastadev.lexicon import alldutchwords, known_word, allfillers
from sastadev.metadata import (MetaValue, bpl_replacement, fromElement,
                               mkSASTAMeta)
from sastadev.sastatok import gettokensplusxmeta
# import find1, iswordnode, getattval
# import find1, iswordnode, getattval
from sastadev.sastatoken import Token
from sastadev.sastatypes import SynTree
from sastadev.stringfunctions import simple_tokenise
from sastadev.tokenmd import TokenListMD
from sastadev import correctionlabels

# import CHAT_Annotation as schat  # put off because it causes an error: AttributeError: module 'CHAT_Annotation' has no attribute 'wordpat'

comma = ','

defaultsettings = AlignmentSettings()


sentenceinitialconjunctions = {'en', 'maar'}
fragments = ['o.', 't', 's', 'n', 'k', 'a.', 'a', 'i', 's.', 'd', 'n.', 'e.', 'w', 'h', 'b', 'v.', 'p', 'z', 'r',
             'l', 'f', 'm.', 'g.', '@', 'w.', 'y', 'g', 'j', 'j.', 'b.', 'k.', 'v', 'h.', 'z.', 'c.', 'f.', 'i.', 'e'] \
    + defaultsettings.fragments

space = ' '
CHAT_explanation = 'Explanation'
explannwordlistxpath = f'.//xmeta[@name="{CHAT_explanation}"]/@annotationwordlist'
explannposlistxpath = f'.//xmeta[@name="{CHAT_explanation}"]/@annotationposlist'
explanationtierxpath = './/meta[@name="explanation"]'

interpunction = '.,;?!'


def tokenreplace(oldtokens: List[Token], newtoken: Token) -> List[Token]:
    newtokens = []
    for token in oldtokens:
        if token.pos == newtoken.pos:
            newtokens.append(newtoken)
        else:
            newtokens.append(token)
    return newtokens


def explanationasreplacement(tokensmd: TokenListMD, tree: SynTree) -> Optional[TokenListMD]:
    # interpret single word explanation as replacement # this will work only after retokenistion of the origutt
    result = None
    origmetadata = tokensmd.metadata
    xtokens, xmetalist = gettokensplusxmeta(tree)
    explanations = [xm for xm in xmetalist if xm.name == 'Explanation']
    newtokens = copy.deepcopy(xtokens)
    newmetadata = origmetadata # + xmetalist  # leaving xmetalist out alone does not avoid unnecessary duplications
    for explanation in explanations:
        newwordlist = explanation.annotationwordlist
        oldwordlist = explanation.annotatedwordlist
        tokenposlist = explanation.annotatedposlist
        if len(newwordlist) == 1 and len(tokenposlist) == 1 and len(oldwordlist) == 1:
            newword = newwordlist[0]
            oldwordpos = tokenposlist[0]
            oldword = oldwordlist[0]
            newtoken = Token(newword, oldwordpos)
            oldtoken = Token(oldword, oldwordpos)
            if known_word(newword):
                newtokens = tokenreplace(newtokens, newtoken)
                # bpl = bpl_node if known_word(oldword) else bpl_word
                meta = mkSASTAMeta(oldtoken, newtoken, name=correctionlabels.explanationasreplacement,
                                   value=correctionlabels.explanationasreplacement,
                                   cat=correctionlabels.lexicalerror, backplacement=bpl_replacement)
                newmetadata.append(meta)
                result = TokenListMD(newtokens, newmetadata)
    return result


def islet(token, tree):
    tbf.showtree(tree, 'tree bij islet')
    xpt = f'//node[@pt and @begin="{str(token.pos)}"]'
    node = tbf.find1(tree, xpt)
    result = tbf.getattval(node, 'pt') == 'let'
    return result

# def finaltokenmultiwordexplanation(tokensmd: TokenListMD, tree: SynTree) -> Optional[str]:


def get_prefix_and_core(tokens: List[Token], explanation: List[str]) -> Tuple[List[Token], List[Token]]:
    """
    split the tokens into a tokenlist prefixtokens and a tokenlist todoxtokens where the prefixtokens contains
    an initial interjection, interjection + comma, en/maar if these do not occur in the explanation

    :param tokens:
    :param explanation:
    :return:
    """
    # remove initial interjection, interjection + comma, en/maar if these do not occur in the explanation
    # done: add kijk (eens/maar/ hier/daar...)

    if tokens == [] or explanation == []:
        return [], tokens
    if tokens[0].word.lower() == explanation[0].lower():
        return [], tokens
    if len(tokens) > 3 and \
        tokens[0].word.lower() == 'kijk' and \
        tokens[1].word.lower() in ['eens', 'maar', 'nou', 'hier', 'daar'] and \
        tokens[2].word.lower() == comma:
        prefixtokens = tokens[0:3]
        todoxtokens = tokens[3:]
    elif len(tokens) >= 2 and tokens[0].word.lower() in allfillers and \
            tokens[1].word.lower() in interpunction and len(explanation) >= 1 and \
            tokens[0].word.lower() != explanation[0].lower():
        prefixtokens = tokens[0:2]
        todoxtokens = tokens[2:]
    elif len(tokens) >= 1 and \
            (tokens[0].word.lower() in allfillers or tokens[
                0].word.lower() in sentenceinitialconjunctions) and \
            len(explanation) >= 1 and tokens[0].word.lower() != explanation[0].lower():
        prefixtokens = tokens[0:1]
        todoxtokens = tokens[1:]
    else:
        prefixtokens = []
        todoxtokens = tokens

    return prefixtokens, todoxtokens

def finaltokenmultiwordexplanation(tree: SynTree) -> Optional[str]:
    # get the multiword explanation and the last tokenposition it occupies

    # it is assumed that the chat annotations have not been extracted and no metadata have been produced
    xtokens, xmetalist = gettokensplusxmeta(tree)

    result = None
    #    origmetadata = tokensmd.metadata
    origmetadata = xmetalist
    explanations = [xm for xm in xmetalist if xm.name == correctionlabels.explanation]
    finalmwexplanations = []
    for xm in explanations:
        lxm = len(xm.annotationwordlist)
        lastxmpos = xm.annotationposlist[-1]
        postexplanationtokens = [
            token for token in xtokens if token.pos > lastxmpos]
        resttokens = [token for token in xtokens if not (
            token.pos > lastxmpos)]

        # remove initial interjection, interjection + comma, en/maar if these do not occur in the explanation

        prefixtokens, todoxtokens = get_prefix_and_core(resttokens, xm.annotationwordlist)

        cond1 = lxm > 1
        cond2 = all(
            [token.word in interpunction for token in postexplanationtokens])
        cond3 = len(todoxtokens) <= lxm

        cond = cond1 and cond2 and cond3

        if cond:
            finalmwexplanations.append(xm)
    if len(finalmwexplanations) == 0:
        result = None
    elif len(finalmwexplanations) > 1:
        result = None
        # report an error
    elif len(finalmwexplanations) == 1:
        finalexpl = finalmwexplanations[0]
        words = [token.word for token in todoxtokens]
        prefixwordlist = [token.word for token in prefixtokens]
        postexplanationwords = [token.word for token in postexplanationtokens]
        utt = space.join(prefixwordlist + words + postexplanationwords)
        expl = space.join(
            prefixwordlist + finalexpl.annotationwordlist + postexplanationwords)
        # print(settings.replacements)
        resultalignment = align_words(utt, expl, auchannsettings)
        result = str(resultalignment)
    else:
        result = None
        # report an error

    return result


def finalmultiwordexplanation(stree: SynTree) -> Optional[str]:
    # get the multiword explanation and the last tokenposition it occupies

    explannwrdliststr = tbf.find1(stree, explannwordlistxpath)
    # print(explannwrdliststr)
    explannwrdlist = strf.string2list(explannwrdliststr, quoteignore=True)
    # print(explannwrdlist)

    explannposliststr = tbf.find1(stree, explannposlistxpath)
    # print(explannposliststr)
    explannposlist = strf.string2list(explannposliststr)
    # print(explannposlist)

    ismultiword = len(explannwrdlist) > 1
    # @@maybe add a condition that the length is not significantly shorter than the original utterance

    if ismultiword:
        # any token in the tree with begin > last tokenposition of explanation can only be an interpunction sign
        # check whether it is the last one ignoring interpunction
        # @@ maybe add interjections

        postexplanationtuplelist = []
        explannposlast = int(explannposlist[-1]) * 10
        # print(explannposlast)

        explisfinal = True
        for node in stree.iter():
            if explisfinal:
                if tbf.iswordnode(node):
                    beginstr = tbf.getattval(node, 'begin')
                    if beginstr != '':
                        begin = int(beginstr)
                        word = tbf.getattval(node, 'word')
                        # print(f'begin={begin}, word={word}')
                        if begin > explannposlast:
                            nodept = tbf.getattval(node, 'pt')
                            # print(f'nodept={nodept}')
                            if nodept not in {'let'}:
                                explisfinal = False
                            else:
                                postexplanationtuplelist.append((begin, word))

        if explisfinal:
            result = explannwrdlist
        else:
            result = None
        sortedpostexplanationtuplelist = sorted(
            postexplanationtuplelist, key=lambda x: x[0])
        sortedpostexplanationlist = [x[1]
                                     for x in sortedpostexplanationtuplelist]
    else:
        result, sortedpostexplanationlist = None, []
    # print(f'result={result}, sortedpostexplanationlist={sortedpostexplanationlist}')
    return result, sortedpostexplanationlist


def getalignment(tree: SynTree) -> Optional[str]:
    origutt = tbf.find1(tree, './/meta[@name="origutt"]/@value')
    # print(origutt)
    cleanuttelem = tbf.find1(tree, './/sentence')
    cleanutt = cleanuttelem.text
    explanationlist, postexplanationlist = finalmultiwordexplanation(tree)
    explanationstr = space.join(
        explanationlist + postexplanationlist) if explanationlist is not None else None
    # print(f'explanationstr={explanationstr}')

    if explanationstr is not None:
        alignment = align_words(cleanutt, explanationstr, auchannsettings)
    else:
        alignment = None
    return alignment


def getexplanationfromexplanationtier(stree: SynTree) -> Optional[str]:
    dutchexplanations = []
    expltiers = stree.xpath(explanationtierxpath)
    for expltier in expltiers:
        expltiervalue = tbf.getattval(expltier, 'value')
        dutchexplanation = get_dutch_explanation(expltiervalue)
        if dutchexplanation is not None:
            dutchexplanations.append(dutchexplanation)
    if dutchexplanations == []:
        return None
    else:
        if len(dutchexplanations) > 1:
            # issue a warning
            pass
        return dutchexplanations[0]

explanation_variants = ['probable meaning: ', 'probable meaning ', 'meaning: ', 'meaning ']
sorted_explanation_variants = sorted(explanation_variants, key= lambda x: len(x), reverse=True)
def get_dutch_explanation(explanation: str) -> Optional[str]:
    remainder = ''
    for variant in sorted_explanation_variants:
        if explanation.startswith(variant):
            remainder = explanation[len(variant):]
            remainder = re.sub(r'([\.\?!,;])', r' \1 ', remainder)
    if remainder == '':
        return None
    elif alldutchwords(remainder):
        return remainder
    else:
        return None


def finalexplanation_adapttreebank(treebank):
    newtreebank = etree.Element('treebank')
    for tree in treebank:
        newtree = finalexplanation_adapttree(tree)
        if newtree is None:
            newtreebank.append(tree)
            sdsettings.LOGGER.warning('Final Explanation correction failed')
        else:
            newtreebank.append(newtree)
    return newtreebank


def is_proper_alignment(utterance: str, raw_explanation: str, alignment: str) -> bool:
    undone_alignment = chatundo(alignment)
    raw_applied_alignment, _ = cleantext(alignment, repkeep=False)
    applied_alignment = space.join(simple_tokenise(raw_applied_alignment))
    explanation = space.join(simple_tokenise(raw_explanation))

    result1 = True
    result2 = True
    if undone_alignment != utterance:
        # issue a warning or message
        sdsettings.LOGGER.info(f'Improper alignment (undo): <{undone_alignment}> != <{utterance}>')
        result1 = False
    if applied_alignment != explanation:
        # issue a warning
        sdsettings.LOGGER.info(f'Improper alignment (aply): <{applied_alignment}> != <{explanation}>')
        result2 = False

    result = result1 and result2
    return result









def get_tier_alignment(tokens: List[Token], explanation: str) -> Optional[str]:
    explanationlist = simple_tokenise(explanation)
    prefixtokens, coretokens = get_prefix_and_core(tokens, explanationlist)
    prefixwords = [token.word for token in prefixtokens]
    prefixstr = space.join(prefixwords)
    if len(coretokens) <= len(explanationlist):
        corewords = [token.word for token in coretokens]
        coresentence = space.join(corewords)
        core_alignment = str(align_words(coresentence, explanation))
        full_alignment = f'{prefixstr} {core_alignment}'

        # check for proper alignment  (no words split up into multiple words)
        alignment_ok = is_proper_alignment(coresentence, explanation, core_alignment)
        if not alignment_ok:
            full_alignment = None

    else:
        full_alignment = None

    return full_alignment

def finalexplanation_adapttree(tree: SynTree) -> SynTree:
    # @@TODO: Unfinished@@
    #    alignment = finaltokenmultiwordexplanation(tokensmd,tree)
    alignment = finaltokenmultiwordexplanation(tree)
    if alignment is None:
        explanationstr = getexplanationfromexplanationtier(tree)
        if explanationstr is not None:
            nodeyield = tbf.getnodeyield(tree)
            tokenlist = [Token(tbf.getattval(node, 'word'), i+1) for i, node in enumerate(nodeyield)]
            alignment = get_tier_alignment(tokenlist, explanationstr)


    if alignment is not None:
        # make the realoriguttmetadata @@todo@@

        # get the original meta data:
        intreemetadataxml = tree.xpath('.//meta')
        intreemetadata = []
        for el in intreemetadataxml:
            newmeta = fromElement(el)
            intreemetadata.append(newmeta)
        #        intreemetadata = [fromElement(el) for el in intreemetadataxml]

        # adapt the metadata
        newmetadata = []
        for meta in intreemetadata:
            if meta.uel == 'origutt':
                newmeta = MetaValue('pre_origutt', 'text', meta.text)
                newmetadata.append(newmeta)
                origuttmeta = MetaValue('origutt', 'text', alignment)
                newmetadata.append(origuttmeta)
            else:
                newmetadata.append(meta)

        # clean the alignment
        cleanutttokens, chatmetadata = cleantext(
            alignment, False, tokenoutput=True)

        newmetadata += chatmetadata
        cleanutt = space.join([token.word for token in cleanutttokens])

        newtree = sdsettings.PARSE_FUNC(cleanutt)
        sentelem = tbf.find1(tree, './/sentence')
        sentid = sentelem.attrib['sentid']
        # tbf.showtree(newtree, 'newly parsed tree')
        if newtree is None:
            newtree = tree
            sdsettings.LOGGER.warning(
                'Parsing for <{cleanutt}> failed. No changes applied')
        else:
            newsentelem = tbf.find1(newtree, './/sentence')
            newsentelem.attrib['sentid'] = sentid if newsentelem is not None else '@@'
            newmetaelements = [meta.toElement() for meta in newmetadata]
            newmetadataElement = etree.Element('metadata')
            for newmetaelement in newmetaelements:
                newmetadataElement.append(newmetaelement)

            newtree.insert(0, newmetadataElement)
        # tbf.showtree(newtree, 'newly parsed tree with metadata')
    else:
        newtree = tree
    return newtree

    # parse the utterance, add the metadata return the tree
