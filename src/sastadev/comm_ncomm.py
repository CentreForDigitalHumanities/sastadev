from sastadev.CHAT_Annotation import CHAT_retracing, CHAT_repetition, CHAT_phonological_fragment
from sastadev.cleanCHILDEStokens import cleanedtokenisation
from sastadev.conf import settings
from sastadev.sastatypes import SynTree, TreeBank, UttId
from sastadev.stringfunctions import punctuationchars
from sastadev.treebankfunctions import getattval as gav, getxsid, getorigutt
from typing import Dict, List, Tuple

cleanedtokenisation = 'cleanedtokenisation'
WordCountPair = (int, int)
xmetadata_xpath = './/xmeta'
cleanedtokenisation_xpath = f'.//xmeta[@name="{cleanedtokenisation}"]'

non_comm_xmetas = [CHAT_retracing, CHAT_repetition]   #, CHAT_phonological_fragment]

def get_comm_word_count(stree: SynTree) -> int:
    xmetadata = stree.xpath(cleanedtokenisation_xpath)
    xsid = getxsid(stree)
    origutt = getorigutt(stree)
    if len(xmetadata) == 0:
        settings.LOGGER.error(f'No cleaned tokenisations in utterance  {xsid}:  origutt={origutt}')
        result = 0
    else:
        xmeta = xmetadata[0]
        annotation_wordlist = eval(gav(xmeta, 'annotationwordlist'))
        clean_annotation_wordlist = [wrd for wrd in annotation_wordlist if wrd not in punctuationchars]
        result = len(clean_annotation_wordlist)
        if len(xmetadata) > 1:
            settings.LOGGER.error(
                f'Multiple cleaned tokenisations in utterance {xsid}:  origutt={origutt}')
    return result
            
def get_noncomm_word_count(stree: SynTree, xmetas=non_comm_xmetas) -> int:
    xmetadata = stree.xpath(xmetadata_xpath)
    non_comm_count = 0
    for xmeta in xmetadata:
        if gav(xmeta, 'name') in xmetas:
            annotation_wordlist = eval(gav(xmeta, 'annotationwordlist'))
            non_comm_count += len(annotation_wordlist)
    return non_comm_count

def get_tb_comm_word_count(treebank: TreeBank) -> List[Tuple[UttId, int]]:
    resultlist = []
    for stree in treebank:
        xsid = getxsid(stree)
        if xsid != '0':
            comm_word_count = get_comm_word_count(stree)
            newtuple = (xsid, comm_word_count)
            resultlist.append(newtuple)
    return resultlist

def get_tb_noncomm_word_count(treebank: TreeBank, xmetas=non_comm_xmetas) -> List[Tuple[UttId, int]]:
    resultlist = []
    for stree in treebank:
        xsid = getxsid(stree)
        if xsid != '0':
            noncomm_word_count = get_noncomm_word_count(stree, xmetas)
            newtuple = (xsid, noncomm_word_count)
            resultlist.append(newtuple)
    return resultlist

# the next two ones are not used - must be dealt with in a different way to make the distinction between
# false start and selfcorrections, and some retracings are actually repetitions
def get_tb_repetition_word_count(treebank: TreeBank) -> List[Tuple[UttId, int]]:
    result = get_tb_noncomm_word_count(treebank, xmetas=[CHAT_repetition])
    return result

def get_tb_retracing_word_count(treebank: TreeBank) -> List[Tuple[UttId, int]]:
    result = get_tb_noncomm_word_count(treebank, xmetas=[CHAT_retracing])
    return result
