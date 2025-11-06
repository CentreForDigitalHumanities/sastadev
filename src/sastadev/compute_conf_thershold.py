import os
from collections import defaultdict
from sastadev.conf import settings
from sastadev.xlsx import getxlsxdata, mkworkbook

avgcol = 5
f1col = 7

hundred = '100'
nothundred = '<100'

confbyuttfolder = '_conf_by_utt'

def makecounts(fullname):
    resultdict = defaultdict(lambda: defaultdict(int))
    header, data = getxlsxdata(fullname)
    for row in data:
        f1 = row[f1col]
        for i in range(40, 86, 1):
            if row[avgcol] < i:
                if f1 == 100:
                    resultdict[i][hundred] += 1
                else:
                    resultdict[i][nothundred] += 1
    return resultdict


if __name__ == '__main__':
    filename = 'confidence_by_utt.xlsx'
    path = os.path.join(settings.DATAROOT, confbyuttfolder)
    fullname = os.path.join(path, filename)
    resultdict = makecounts(fullname)
    newrows = []
    for i in resultdict:
        h = resultdict[i][hundred]
        noth = resultdict[i][nothundred]
        proportion = noth / (h + noth) * 100
        newrow = [i, h, noth, proportion]
        newrows.append(newrow)
    header = ['prec', 'h', 'noth', 'proportion']
    outfilename = 'conf_threshold_data.xlsx'
    outfullname = os.path.join(path, outfilename)
    wb = mkworkbook(outfullname, [header], newrows, freeze_panes=(1, 0))
    wb.close()
