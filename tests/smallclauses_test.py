import os

from sastadev.constants import intreebanksfolder
from sastadev.sastatoken import Token, show
from sastadev.smallclauses import bg, getleavestr, smallclauses, word
from sastadev.tokenmd import TokenListMD
from sastadev.treebankfunctions import getnodeyield, getstree
from sastadev.conf import settings


def getfn(dataset, filename):
    result = os.path.join(settings.DATAROOT, dataset, intreebanksfolder, filename)
    return result


testbank = getfn('sctest', "smallclausetest.xml")
schlichtingtreebank = getfn('schlichting', 'TARVB2_ID2.xml')
mieke06 = getfn('miekeplat', "TARSP_MIEKE06_ID.xml")
mieke08 = getfn('miekeplat', "TARSP_MIEKE08_ID.xml")
aurisraw = getfn('Eliska', 'AURIS_ELISKA_ORIGINAL_ID.xml')
tarsp02 = os.path.join(settings.DATAROOT, 'VKLTarsp', intreebanksfolder, 'Tarsp_02.xml')
tarsp06 = os.path.join(settings.DATAROOT, 'VKLTarsp', intreebanksfolder, 'Tarsp_06.xml')
schlichtingall = os.path.join(
    settings.DATAROOT, 'Schlichtingall', intreebanksfolder, 'TREEBANK_SCHLICHTING_CHAT_ID.xml')


def main():
    smalltest = False
    if smalltest:
        fullnames = [testbank]
    else:
        fullnames = [schlichtingtreebank, mieke06, mieke08,
                     aurisraw, tarsp02, tarsp06, schlichtingall]
    for infullname in fullnames:
        print(f'\n{infullname}\n')
        fulltreebank = getstree(infullname)
        if fulltreebank is not None:
            treebank = fulltreebank.getroot()
            for tree in treebank:
                leaves = getnodeyield(tree)
                tokens = [Token(word(leave), bg(leave)) for leave in leaves]
                tokensmd = TokenListMD(tokens, [])
                resultlist = smallclauses(tokensmd, tree)
                if resultlist != []:
                    print('input:  ', getleavestr(leaves))
                    print('output: ', show(resultlist[0].tokens))
                    print('result: ', resultlist[0].metadata)


if __name__ == '__main__':
    main()
