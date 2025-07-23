from lxml import etree
import os
from sastadev.conf import settings
from sastadev.constants import intreebanksfolder
from sastadev.history import gathercorrections, mergecorrections, HistoryCorrection
import sastadev.sastatok


def tryhistory():
    dataset = 'vklstap'
    filenames = ['stap_02.xml']
    fullpath = os.path.join(settings.DATAROOT, dataset, intreebanksfolder)
    fullnames = [os.path.join(fullpath, fn) for fn in filenames]
    for fullname in fullnames:
        fulltreebank = etree.parse(fullname)
        treebank = fulltreebank.getroot()
        thehistory = gathercorrections(treebank)
        for wrong in thehistory:
            print(wrong)
            for correction in thehistory[wrong]:
                print(f'--{correction}')



def trymerge():
    hcdict1 = {'lape': [HistoryCorrection(wrong='lape', correction='slapen', correctiontype='Explanation', frequency=100),
               HistoryCorrection(wrong='lape', correction='geslapen', correctiontype='Explanation', frequency=50)],
               'sape': [HistoryCorrection(wrong='sape', correction='slapen', correctiontype='Replacement',
                                         frequency=33)]
               }
    hcdict2 = {
               'lape': [HistoryCorrection(wrong='lape', correction='slapen', correctiontype='Explanation', frequency=33),
               HistoryCorrection(wrong='lape', correction='slapen', correctiontype='Replacewment', frequency=66)],
               'valle': [HistoryCorrection(wrong='valle', correction='gevallen', correctiontype='NonCompletion',
                                         frequency= 99)],
               'n': [HistoryCorrection(wrong='n', correction='een', correctiontype='NonCompleteion',
                                         frequency=133)]
               }
    newhcdict = mergecorrections(hcdict1, hcdict2)
    print(newhcdict)

if __name__ == '__main__':
    # tryhistory()
    trymerge()
