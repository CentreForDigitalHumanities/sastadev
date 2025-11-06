import copy
from sastadev import correctionlabels
from sastadev.allresults import AllResults
from sastadev.CHAT_Annotation import CHAT_errormarking, CHAT_wordnoncompletion, CHAT_replacement
from sastadev.deregularise import detailed_detect_error
from sastadev.metadata import bpl_none, Meta
from sastadev.predcvagreement import get_predc_v_mismatches
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import add_metadata, find1, getattval as gav, getnodeyield
from typing import List, Optional

replacementxpath = f""".//xmeta[@name="{correctionlabels.replacement}" or 
                                @name="{CHAT_replacement}" or 
                                @name="{CHAT_wordnoncompletion}" or 
                                @name="{correctionlabels.noncompletion}" or 
                                @name="{correctionlabels.explanationasreplacement}" 
                               ]"""
errormarkingxpath = f""".//xmeta[@name="{CHAT_errormarking}"]"""
tokenisationxpath = f""".//xmet[@name="{correctionlabels.tokenisation}"]"""

sasta = 'SASTA'

# Meta(name, value, annotationwordlist=[], annotationposlist=[], annotatedposlist=[],
#                  annotatedwordlist=[], annotationcharlist=[
#     ], annotationcharposlist=[], annotatedcharlist=[],
#             annotatedcharposlist=[], atype='text', cat=None, subcat=None, source=None, penalty=defaultpenalty,
#             backplacement=defaultbackplacement)

def get_meta_attr(meta: SynTree, attr: str) -> Optional[str]:
    wordliststr = gav(meta, attr)
    wordlist = eval(wordliststr)
    result = wordlist[0] if wordlist != [] else None
    return result



def find_grammar_errors_in_allresults(inallresults: AllResults) -> AllResults:
    allresults = copy.deepcopy(inallresults)
    strees = allresults.analysedtrees
    newstrees = []
    for xsid, stree in strees:
        metalist = find_grammar_errors_in_stree(stree)
        if metalist == []:
            newstree = stree
        else:
            newstree = add_metadata(stree, metalist)
        newstrees.append((xsid, newstree))
    allresults.analysedtrees = newstrees
    return allresults

def find_grammar_errors_in_stree(stree: SynTree) -> List[Meta]:
    results = []
    matches = get_predc_v_mismatches(stree)
    for match in matches:
        verb = find1(match, './node[@rel="hd"]')
        thenodeyield = getnodeyield(match)
        annotatedwordlist = [gav(nd, 'word') for nd in thenodeyield]
        annotatedposlist = [gav(nd, 'end') for nd in thenodeyield]
        if verb is not None:
            meta = Meta(name=correctionlabels.agreementerror,
                        value=correctionlabels.predc_v_agreement_error,
                        cat=correctionlabels.syntax,
                        annotatedposlist=annotatedposlist, annotatedwordlist=annotatedwordlist,
                        subcat=None, source=sasta, backplacement=bpl_none)
            results.append(meta)
    matches = stree.xpath(replacementxpath)
    for match in matches:
        word = get_meta_attr(match, 'annotatedwordlist')
        correction = get_meta_attr(match, 'annotationwordlist')
        wordposition = get_meta_attr(match, 'annotatedposlist')
        if word is not None and correction is not None:
            errorfound, errormsg = detailed_detect_error(word, correction)
            if errorfound:
                annotatedwordlist = [word]
                annotatedposlist = [wordposition]
                meta = Meta(name=correctionlabels.morphologicalerror, value=errormsg,
                            cat=correctionlabels.morphology, annotationwordlist=[correction],
                            annotationposlist=annotatedposlist,
                            annotatedposlist=annotatedposlist, annotatedwordlist=annotatedwordlist,
                            subcat=None, source=sasta, backplacement=bpl_none)
                results.append(meta)

    newresults = find_replacement_error_marking(stree)
    results += newresults
    return results


def get_position(meta: Meta) -> Optional[int]:
    annotationposlist = get_meta_attr(meta, 'annotationposlist')
    return annotationposlist


def find_replacement_error_marking(stree: SynTree) -> List[Meta]:
    resultlist = []
    replacements = stree.xpath(replacementxpath)
    errormarkings = stree.xpath(errormarkingxpath)
    # tokenisationmeta = find1(stree, tokenisationxpath)
    # if tokenisationmeta is None:
    #     return []
    # else:
    #     tokenisation = get_meta_attr(tokenisationmeta, 'annotationwordlist')
    for errormarking in errormarkings:
        errormarking_position = get_position(errormarking)
        if errormarking_position is None:
            continue
        for replacement in replacements:
            replacement_position = get_position(replacement)
            if replacement_position is None:
                continue
            if replacement_position == errormarking_position - 30:
                thevalue = get_meta_attr(errormarking, 'value')
                annotatedwordlist= replacement.get('annotatedwordlist')
                annotatedposlist = replacement.get('annotatedposlist')
                annotationwordlist= replacement.get('annotationwordlist')
                annotationposlist = replacement.get('annotationposlist')
                newmeta = Meta(name=correctionlabels.replacement_error_marking, value=thevalue,
                               annotatedwordlist=annotatedwordlist, annotatedposlist=annotatedposlist,
                               annotationwordlist=annotationwordlist, annotationposlist=annotationposlist,
                               atype='text', cat=correctionlabels.error, subcat=None, source=sasta,
                               backplacement=bpl_none, penalty=0)
                resultlist.append(newmeta)
    return resultlist



