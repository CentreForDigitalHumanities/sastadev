from sastadev.CHAT_Annotation import CHAT_retracing, CHAT_repetition, CHAT_phonological_fragment
from sastadev.cleanCHILDEStokens import cleanedtokenisation
from sastadev.conf import settings
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getattval as gav, getxsid, getorigutt

cleanedtokenisation = 'cleanedtokenisation'
WordCountPair = (int, int)
xmetadata_xpath = './/xmeta'
cleanedtokenisation_xpath = f'.//meta[@name="{cleanedtokenisation}"]'

non_comm_xmetas = [CHAT_retracing, CHAT_repetition, CHAT_phonological_fragment]

def get_comm_word_count(stree: SynTree) -> int:
    xmetadata = stree.xpath(cleanedtokenisation_xpath)
    xsid = getxsid(stree)
    origutt = getorigutt(stree)
    if len(xmetadata) == 0:
        settings.LOGGER.error(f'No cleaned tokenisations in utterance  {xsid}:  origutt={origutt}')
        result = 0
    else:
        xmeta = xmetadata[0]
        annotated_wordlist = gav(xmeta, 'annotated_wordlist')
        result = len(annotated_wordlist)
        if len(xmetadata) > 1:
            settings.LOGGER.error(
                f'Multiple cleaned tokenisations in utterance {xsid}:  origutt={origutt}')
    return result
            
def get_noncomm_word_count(stree: SynTree) -> int:
    xmetadata = stree.xpath(xmetadata_xpath)
    non_comm_count = 0
    for xmeta in xmetadata:
        if gav(xmeta, 'name') in non_comm_xmetas:
            annotated_wordlist = gav(xmeta, 'annotated_wordlist')
            non_comm_count += len(annotated_wordlist)
    return non_comm_count

    