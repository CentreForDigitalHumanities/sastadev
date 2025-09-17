from sastadev import correctionlabels
from sastadev.celexlexicon import celexpv2dcoi
from sastadev.lexicon import informlexicon, getwordinfo
from sastadev.basicreplacements import basicreplacements
from sastadev.deregularise import detailed_detect_error
from sastadev.metadata import bpl_none, Meta
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import getattval as gav
from typing import List, Optional

sasta = 'SASTA'
grammarerrors = 'grammarerrors'
thesource = f'{sasta}/{grammarerrors}'

infl_properties = {}
infl_properties['ww'] = ['wvorm', 'pvtijd', 'pvagr', 'buiging']
infl_properties['n'] = ['graad', 'getal', 'naamval']
infl_properties['vnw'] = ['vwtype', 'naamval', 'persoon', 'getal', 'status']
infl_properties['adj'] = ['graad', 'buiging', 'naamval']

errorlabels = {'wvorm': 'mood', 'pvtijd': 'tense', 'pvagr': 'verb inflection', 'positie': 'modification',
               'buiging': 'nominal inflection', 'graad': 'degree', 'getal': 'number', 'naamval': 'case',
               'vwtype': 'pronoun type', 'persoon': 'person' }

def get_meta_attr(meta: SynTree, attr: str) -> Optional[str]:
    wordliststr = gav(meta, attr)
    wordlist = eval(wordliststr)
    result = wordlist[0] if wordlist != [] else None
    return result


def inflection_overgeneralisation(meta: Meta, stree: SynTree) -> List[Meta]:
    resultlist = []
    word = get_meta_attr(meta, 'annotatedwordlist')
    correction = get_meta_attr(meta, 'annotationwordlist')
    wordposition = get_meta_attr(meta, 'annotatedposlist')
    errorfound, errormsg = detailed_detect_error(word, correction)
    if errorfound:
        annotatedwordlist = [word]
        annotatedposlist = [wordposition]
        meta = Meta(name=correctionlabels.morphologicalerror, value=errormsg,
                    cat=correctionlabels.morphology, annotationwordlist=[correction],
                    annotationposlist=annotatedposlist,
                    annotatedposlist=annotatedposlist, annotatedwordlist=annotatedwordlist,
                    subcat=None, source=thesource, backplacement=bpl_none)
        resultlist.append(meta)
    return resultlist

def check_basic_replacement(meta: Meta, stree: SynTree) -> List[Meta]:
    resultlist = []
    word = get_meta_attr(meta, 'annotatedwordlist')
    correction = get_meta_attr(meta, 'annotationwordlist')
    wordposition = get_meta_attr(meta, 'annotatedposlist')
    if word in basicreplacements:
        replacements = basicreplacements[word]
        for corr, cat, name, val, pen in replacements:
            if correction == corr:
                annotatedwordlist = [word]
                annotatedposlist = [wordposition]
                meta = Meta(name=name, value=val,
                            cat=cat, annotationwordlist=[correction],
                            annotationposlist=annotatedposlist,
                            annotatedposlist=annotatedposlist, annotatedwordlist=annotatedwordlist,
                            subcat=None, source=thesource, backplacement=bpl_none)
                resultlist.append(meta)
    return resultlist

def check_infl(meta: Meta, stree: SynTree) -> List[Meta]:
    resultlist = []
    word = get_meta_attr(meta, 'annotatedwordlist')
    correction = get_meta_attr(meta, 'annotationwordlist')
    word_position = get_meta_attr(meta, 'annotatedposlist')
    correction_position = get_meta_attr(meta, 'annotationposlist')
    correction_node = stree.xpath(f',//node[@end="{correction_position}"]')
    correction_pt = gav(correction_node, 'pt')
    if informlexicon(word):
        wordinfos = getwordinfo(word)
        for wordinfo in wordinfos:
            (pt, dehet, infl, lemma) = wordinfo
            if correction_pt != pt:
                newmetas = check_pron(word, correction, meta)
            elif correction_pt == 'ww':
                wordprops = celexpv2dcoi(word, infl, lemma)
                correctionprops = {att: gav(correction_node, att) for att in infl_properties['ww']}
                errormsgs = compare_properties(wordprops, correctionprops)
                for errormsg in errormsgs:
                    meta = Meta(name=correctionlabels.grammarerror, value=errormsg,
                                cat=correctionlabels.morphology, annotationwordlist=[correction],
                                annotationposlist=[correction_position],
                                annotatedposlist=[word_position], annotatedwordlist=[word],
                                subcat=None, source=thesource, backplacement=bpl_none)
                    resultlist.append(meta)
    return resultlist


def check_pron(word: str, correction: str, meta) -> List[Meta]:
    pass

def compare_properties(wordprops:dict, corrprops:dict, pt:str) -> List[str]:
    errorsfound = []
    for att in infl_properties[pt]:
        if mismatch(wordprops, corrprops, att):
            errormsg = f'{errorlabels[att]} Error'
            errorsfound.append(errormsg)
            if att == 'wvorm':
                return errorsfound
    return errorsfound



def mismatch(wordprops: dict, corrprops:dict, att:str) -> bool:
    if att in wordprops and att not in corrprops:
        return True
    if att not in wordprops and att in corrprops:
        return True
    if att in wordprops and att in corrprops:
        return wordprops[att] != corrprops[att]
    return False


