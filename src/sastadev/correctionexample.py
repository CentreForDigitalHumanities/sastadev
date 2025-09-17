import os
from optparse import OptionParser
from typing import List

from lxml import etree

from sastadev.__main__ import mkerrorreport
from sastadev.alpinoparsing import parse
from sastadev.correctionparameters import CorrectionParameters
from sastadev.correcttreebank import correcttreebank, corrn, errorwbheader
from sastadev.targets import target_all
from sastadev.xlsx import mkworkbook

tarsp = 'tarsp'

def write2excel(allorandalts, base):
    errorloggingfullname = f'{base}_errorlogging.xlsx'
    allerrorrows: List[str] = []
    for orandalts in allorandalts:
        if orandalts is not None:
            allerrorrows += orandalts.OrigandAlts2rows(base)
    errorwb = mkworkbook(errorloggingfullname, [
        errorwbheader], allerrorrows, freeze_panes=(1, 1))
    errorwb.close()



parser = OptionParser()
parser.add_option("-f", "--file", dest="infilename",
                  help="Treebank File to be analysed")

parser.add_option("-m", "--method", dest="methodname",
                  help="Name of the method or (for backwards compatibility) "
                       "file containing definition of assessment method (SAM)")
parser.add_option("--no_spell", dest="dospellingcorrection", action="store_false",
                  help="Do no spelling correction")
parser.add_option("--no_auchann", dest="doauchann", action="store_false",
                  help="Do no Automatic CHAT annotation (AuCHAnn)")
parser.add_option("--no_history", dest="dohistory", action="store_false",
                  help="Do no History Creation")
parser.add_option("--no_history_extension", dest="extendhistory", action="store_false",
                  help="Use History but do not extend it")

(options, args) = parser.parse_args()

options.doauchann = True
options.dohistory = False
options.extendhistory = False
options.dospellingcorrection = False   # this is an experimental feature, put off for now

# we pretend that we read from a filename sample1.xml
options.infilename = 'sample1.xml'
base, ext = os.path.splitext(options.infilename)

options.method = tarsp    # some corrections are method-dependent; for young children, use the value tarsp

method = options.method

# here we create the input treebank
sample = ['die dicht', 'ik smeer op de andere been', 'die boek ook plaatje']
parses = [parse(utt) for utt in sample]
treebank = etree.Element('treebank')
treebank.extend(parses)




# here we set the relevant parameters, most are irrelevant for now except method

allsamplecorrections = {}   # for a history of earlier CHAT corrections, set to {} here
thissamplecorrections = {}  # for CHAT corrections in this sample, set to {} here
contextdict = {}  # to take the context into account, set to {} here

correctionparameters = CorrectionParameters(method, options, allsamplecorrections,
                                            thissamplecorrections, treebank, contextdict)
targets = target_all  # all utterances will be analysed
corr = corrn   # multiple corrections are considered and the 'best' one is selected

corrected_treebank, errordict, allorandalts = correcttreebank(treebank, targets, correctionparameters, corr=corr)


# write the errorlogging to an excel file
write2excel(allorandalts, base)

errorreportfilename = f'{base}_errorreport.xlsx'
mkerrorreport(errordict, errorreportfilename)


