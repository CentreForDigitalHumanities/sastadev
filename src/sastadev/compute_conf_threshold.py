import os
from collections import defaultdict
from sastadev.conf import settings
from sastadev.constants import datafolder, confbyuttfolder
from sastadev.methods import validmethods
from sastadev.sastatypes import Table
from sastadev.xlsx import getxlsxdata, mkworkbook
from typing import Callable

avgcol = 5
f1col = 7

proportioncol = 3
precisioncol = 0
nothcol = 2

hundred = '100'
nothundred = '<100'

noth_h_proportion = 70


def mymax(rows: list, key:Callable) -> list:
    maxval = None
    maxrows = []
    for row in rows:
        keyrow = key(row)
        if maxval is None:
            maxrows = [row]
            maxval = keyrow
        elif keyrow > maxval:
            maxrows = [row]
            maxval = keyrow
        elif keyrow == maxval:
            maxrows.append(row)
    return maxrows

def makecounts(fullname):
    resultdict = defaultdict(lambda: defaultdict(int))
    header, data = getxlsxdata(fullname)
    for row in data:
        f1 = row[f1col]
        for i in range(40, 95, 1):
            if row[avgcol] < i:
                if f1 == 100:
                    resultdict[i][hundred] += 1
                else:
                    resultdict[i][nothundred] += 1
    return resultdict


def make_conf_rows(resultdict) -> Table:
    newrows = []
    for i in resultdict:
        h = resultdict[i][hundred]
        noth = resultdict[i][nothundred]
        proportion = noth / (h + noth) * 100
        newrow = [i, h, noth, proportion]
        newrows.append(newrow)
    return newrows


def get_cutoff_pct(rows: Table) -> float:
    '''
    Each row has 4 cells:
    * precision boundary (incremens by 1 %)
    * h count ( # times the score is 100%
    * noth count (# times the score is not 100%
    * proportion of noth of all rows: noth / (noth+h) * 100

    This function selects the precision boundary of the row that has a proportioncol > noth_h_proportion and
    that has the highest noth count,  so that utterances with an average precision < this value are selected
    for revision by a human
    '''
    relevant_rows = [row for row in rows if row[proportioncol] > noth_h_proportion]
    if relevant_rows == []:
        relevant_rows = mymax(rows, key = lambda row: row[proportioncol])  # take the ones with the highest proportion
    thenothmax = 0
    therow = [0,0,0,0]
    for row in relevant_rows:
        if row[nothcol] > thenothmax:
            therow = row
            thenothmax = row[nothcol]
    result = therow[precisioncol]
    return result



if __name__ == '__main__':
    cutoff_data = []
    path = os.path.join(settings.SD_DIR, datafolder, confbyuttfolder)
    for methodname in validmethods:
        filename = f'confidence_by_utt_{methodname}.xlsx'
        fullname = os.path.join(path, filename)
        resultdict = makecounts(fullname)
        newrows = make_conf_rows(resultdict)
        cutoff_pct = get_cutoff_pct(newrows)
        cutoff_row = [methodname, cutoff_pct]
        cutoff_data.append(cutoff_row)
        # print(f'cutoff pct = {cutoff_pct}')
        header = ['prec', 'h', 'noth', 'proportion']
        outfilename = f'conf_threshold_data_{methodname}.xlsx'
        outfullname = os.path.join(path, outfilename)
        wb = mkworkbook(outfullname, [header], newrows, freeze_panes=(1, 0))
        wb.close()
    cutoff_filename = 'cutoff_data.xlsx'
    cutoff_fullname = os.path.join(path, cutoff_filename)
    cutoff_header = ['method', 'cutoff']
    wb = mkworkbook(cutoff_fullname, [cutoff_header], cutoff_data, freeze_panes=(1,0))
    wb.close()
