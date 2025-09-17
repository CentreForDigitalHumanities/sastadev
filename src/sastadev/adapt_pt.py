import copy
from sastadev.conf import settings
from sastadev.dcoi import dcoi_features
from sastadev.sastatypes import SynTree

wrong_pt_lemmas = [('in', 'adj', 'vz', 'ld', 'VZ(init)')]


defaultproperties = {'vz': {'vztype': 'init'}}

def adapt_pt(stree: SynTree) -> SynTree:
    newstree = copy.deepcopy(stree)
    for lemma, badpt, goodpt, newrel, postag in wrong_pt_lemmas:
        query = f""".//node[@lemma="{lemma}" and @pt="{badpt}"]"""
        wrongnodes = newstree.xpath(query)
        for wrongnode in wrongnodes:
            wrongnode.set('pt', goodpt)
            wrongnode.set('postag', postag)

            # delete the badpt properties
            if badpt in dcoi_features:
                for att in dcoi_features[badpt]:
                    if att in wrongnode.attrib:
                        wrongnode.attrib.pop(att)
            else:
                settings.LOGGER.error(f'No entry for {badpt} in sastadev.dcoi.dcoi_features. No changes applied')
                return stree

            #add the goodpt properties
            if goodpt in defaultproperties:
                for att, val in defaultproperties[goodpt].items():
                    wrongnode.set(att, val)
                wrongnode.set('rel', newrel)
            else:
                settings.LOGGER.error(f'No entry for {goodpt} in default_features. No changes applied')
                return stree
    return newstree