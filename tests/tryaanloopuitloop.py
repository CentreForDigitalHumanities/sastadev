import json
from lxml import etree
import os
from sastadev.filefunctions import get_corrected_tree_fullname
from sastadev.tblex import getaanloop_core_uitloop
from sastadev.treebankfunctions import getattval as gav
from sastadev.xlsx import getxlsxdata, mkworkbook

space = ' '
semicolon = ';'

testdatapath = r"D:\Dropbox\jodijk\myprograms\python\sastacode\mysastadev\src\sastadev\testdata"
testdatafilename = "search_treebanksresults_multiple_commas.xlsx"
testdatafullname = os.path.join(testdatapath, testdatafilename)
refoutfilename  = 'aanloop_core_uitloop_ref.json'
refoutfullname = os.path.join(testdatapath, refoutfilename)
refoutfilenamexlsx = 'aanloop_core_uitloop_ref.xlsx'
refoutfullnamexlsx = os.path.join(testdatapath, refoutfilenamexlsx)

datasetcol = 4
xmlfilenamecol = 6
xsidcol = 7

outheader = ['datasetname', ' samplename', 'xsid', 'aanloop', 'core', 'uitloop' ]

def totest(row: list) -> bool:
    result =  row[datasetcol].lower() == 'elsdejong' and \
              row[xmlfilenamecol][0:-len('_corrected.xml')].lower() == 'stap_01' and \
              str(row[xsidcol])  == '26'
    return result

def dotest():
    header, data = getxlsxdata(testdatafullname)
    refinput = []
    xlsxrefinput = []
    testing = False
    if testing:
        data = [row for row in data if totest(row)]
    for row in data:
        datasetname = row[datasetcol]
        samplename = row[xmlfilenamecol][0:-len('_corrected.xml')]
        xsid = str(row[xsidcol])
        treefullname = get_corrected_tree_fullname(datasetname, samplename, xsid)
        fulltree = etree.parse(treefullname)
        tree = fulltree.getroot()
        aanloops, core, uitloops = getaanloop_core_uitloop(tree)
        core_out = space.join([gav(n, 'word') for n in core])
        aanloop_out = [space.join([gav(n, 'word') for n in aanloop]) for aanloop in aanloops ]
        uitloop_out = [space.join([gav(n, 'word') for n in uitloop]) for uitloop in uitloops ]
        refinput.append([datasetname, samplename, xsid, aanloop_out, core_out, uitloop_out])
        xlsxrefinput.append([datasetname, samplename, xsid,
                             semicolon.join(aanloop_out), core_out, semicolon.join(uitloop_out)])
    with open(refoutfullname, 'w', encoding='utf8') as outfile:
        json.dump(refinput, outfile)

    wb = mkworkbook(refoutfullnamexlsx, [outheader], xlsxrefinput, freeze_panes=(1, 0))
    wb.close()




if __name__ == '__main__':
    dotest()