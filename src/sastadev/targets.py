from sastadev.CHAT_Annotation import CHAT_unintelligible_speech
from sastadev.methods import Method, tarsp, stap, asta
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import find1


target_intarget, target_xsid, target_all, target_byrole, target_bysyn, target_stapvu = 0, 1, 2, 3, 4, 5
intargetxpath = '//meta[@name="intarget"]'
xsidxpath = '//meta[@name="xsid"]'
intargetvalxpath = './/meta[@name="intarget"]/@value'
xsidvalxpath = './/meta[@name="xsid"]/@value'
synxpath = './/meta[@name="syn"]'

rolevalxpath = './/meta[@name="role"]/@value'

targetroles = ['target_child', 'target', 'target_adult']
stapvuxpath = './/meta[@name="origutt" and contains(@value, "[+ VU]")]'

def get_targets(treebank, methodname):
    xsids = treebank.xpath(xsidxpath)
    intargets = treebank.xpath(intargetxpath)
    roles = treebank.xpath(rolevalxpath)
    targetrolesfound = any(map(lambda x: x.lower() in targetroles, roles))
    synannotations = treebank.xpath(synxpath)
    stapvus = treebank.xpath(stapvuxpath)
    if synannotations != [] and xsids == []:
        result = target_bysyn
    elif xsids != []:
        result = target_xsid
    elif intargets != []:
        result = target_intarget
    elif methodname == 'stap' and stapvus != []:
        result = target_stapvu
    elif targetrolesfound:
        result = target_byrole
    else:
        result = target_all
    return result


def get_mustbedone(syntree, targets, method: Method):
    if targets == target_bysyn:
        syns = syntree.xpath(synxpath)
        result = syns != []
    elif targets == target_intarget:
        intargetvals = syntree.xpath(intargetvalxpath)
        result = intargetvals != [] and intargetvals[0] == 'yes'
    elif targets == target_xsid:
        xsids = syntree.xpath(xsidvalxpath)
        result = xsids != []
    elif targets == target_byrole:
        rolevals = syntree.xpath(rolevalxpath)
        result = any(map(lambda x: x.lower() in targetroles, rolevals))
    elif targets == target_stapvu:
        syns = syntree.xpath(stapvuxpath)
        result = syns != []
    else:
        result = True

    if result:  # the CHAT metadata are not yet here, so adapt and refine
        finalresult = result
        # finalresult = include_utterance(syntree, method)
    else:
        finalresult = result
    return finalresult

def include_utterance(syntree: SynTree, method: Method):
    methodname = method.name
    if methodname == tarsp:
        if contains_unintelligible_speech(syntree):
            return False
    return True

# unintelligible_speech_xpath = f"""./xmeta[@name="{CHAT_unintelligible_speech}"]"""
def contains_unintelligible_speech(syntree: SynTree) -> bool:
    origutt = find1(syntree, './/meta[@name="origutt"]/@value')
    lc_origutt = origutt.lower()
    if origutt is not None and ('xx' in lc_origutt or 'xxx' in lc_origutt or '@' in lc_origutt):
        return True
    # xxxs = syntree.xpath(unintelligible_speech_xpath) # for the moment we do it in an ad-hoc manner
    # result = xxxs != []
    return False