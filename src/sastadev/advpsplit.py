import copy
from lxml import etree
import os
from sastadev.conf import settings
from sastadev.constants import correctedsuffix, outtreebanksfolder, treesfolder
from sastadev.sastatypes import SynTree
from sastadev.stringfunctions import lpad
from sastadev.treebankfunctions import getattval as gav

advpxpath = './/node[@cat="advp" and count(node) = 2]'

smain_node = etree.Element('node', attrib={'cat': 'smain'})
no_split_head_lemmas = ['te']
no_split_modifier_lemmas = ['bijna', 'heel', 'helemaal', 'nog', 'precies', 'ver' ]
no_split_modifier_head_pairs = [('niet', 'meer'), ]

def getfullname(datasetname, samplename, uttid) -> str:
    correctedname = f'{samplename}{correctedsuffix}'
    fullpath = os.path.join(settings.DATAROOT, datasetname,
                            outtreebanksfolder, treesfolder, correctedname)
    filename = f'{correctedname}_{lpad(uttid)}.xml'
    fullname = os.path.join(fullpath, filename)
    return fullname

testexamples = [('auristrain', 'DLD14', '23')]
fullnames = [getfullname(datasetname, samplename, uttid) for datasetname, samplename, uttid in testexamples ]


def transformadvps(instree: SynTree) -> SynTree:
    stree = copy.deepcopy(instree)
    advps = stree.xpath(advpxpath)
    for advp in advps:
        head = None
        modifier = None
        for child in advp:
            if gav(child, 'rel') == 'hd':
                head = child
            elif gav(child, 'rel') != 'hd':
                modifier = child
        if head is None or child is None:
            return instree
        if gav(head, 'lemma') not in no_split_head_lemmas and \
                gav(modifier, 'lemma') not in no_split_modifier_lemmas:
            advp_parent = advp.getparent()
            if gav(advp_parent, 'cat') == 'top':
                new_smain_node = copy.copy(advp)
                for child in new_smain_node:
                    new_smain_node.remove(child)
                new_smain_node.set('cat', 'smain')
                head.set('rel', 'mod')
                new_smain_node.append(modifier)
                new_smain_node.append(head)
                advp_parent.remove(advp)
                advp_parent.append(new_smain_node)
            else:
                advp_rel = gav(advp, 'rel')
                head.set('rel', advp_rel)
                advp_parent.append(modifier)
                advp_parent.append(head)
                advp_parent.remove(advp)
            return stree
        else:
            return instree

def tryme():
    for fullname in fullnames:
        fulltree = etree.parse(fullname)
        tree = fulltree.getroot()
        print(f'\n\n*****tree*****')
        etree.dump(tree)
        newtree = transformadvps(tree)

        print(f'*****newtree*****')
        etree.dump(newtree)



if __name__ == '__main__':
    tryme()
