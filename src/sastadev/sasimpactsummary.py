from sastadev.sastatypes import HeadedTable
from typing import Tuple
from sastadev.conf import settings
from sastadev.constants import resultsfolder, byuttscoressuffix, sasimpact_sheetname, sas_summarysuffix, sasfolder
from sastadev.filefunctions import getsamplename
from sastadev.xlsx import getxlsxdata, mkworkbook, add_worksheet
import os


def getsasimpactsummary(rawdsname: str) -> Tuple[bool, HeadedTable, HeadedTable]:

    errorfound = False
    dsname = rawdsname.strip().lower()
    thepath = os.path.join(settings.DATAROOT, dsname, resultsfolder)
    rawfilenames = os.listdir(thepath)
    filenames = [fn for fn in rawfilenames if fn.endswith(f'{byuttscoressuffix}.xlsx')]
    newfulldata = []
    scoredata = []
    summaryheader = []
    for filename in filenames:
        fullname = os.path.join(thepath, filename)
        h, data = getxlsxdata(fullname, sheetname=sasimpact_sheetname)
        if len(h) > len(summaryheader):
            summaryheader = h
        samplename = getsamplename(filename)
        for row in data:
            newrow = [dsname, samplename] + row
            newfulldata.append(newrow)
        if len(data) != 2:
            print(f'Error: {dsname}/{samplename} has {len(data)} instead of 2 rows.')
            errorfound = True
        else:
            newrow = [dsname, samplename] + data[1]
            scoredata.append(newrow)
    fullsummaryheader = ['Dataset', 'Sample'] + summaryheader
    result = errorfound, (fullsummaryheader, newfulldata), (fullsummaryheader, scoredata)
    return result

def writesasimpactsummary(dsname: str) -> None:
    errorfound, fullhtable, scoretable = getsasimpactsummary(dsname)
    if errorfound:
        print('Aborting')
        exit(-1)
    else:
        outfilename = f'{dsname.strip().lower()}{sas_summarysuffix}.xlsx'
        outpath = os.path.join(settings.DATAROOT, dsname, sasfolder)
        outfullname = os.path.join(outpath, outfilename)
        fullheader, fulltable = fullhtable
        wb = mkworkbook(outfullname, [fullheader], fulltable, sheetname='Full_Summary', freeze_panes=(1,0))
        scoreheader, scoretable  = scoretable
        add_worksheet(wb, [scoreheader], scoretable, sheetname='Score_Summary', freeze_panes=(1,0))
        wb.close()


def main():
    writesasimpactsummary('VKLASTA')


if __name__ == '__main__':
    main()