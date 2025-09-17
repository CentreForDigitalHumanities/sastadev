import os
import sys
import shutil
from sastadev.conf import settings
from sastadev.constants import correctedsuffix, outtreebanksfolder, treesfolder
from sastadev.readcsv import writecsv
from sastadev.sastatypes import FileName, List, Tuple
from sastadev.stringfunctions import lpad

reportwidth = 0

# the following 2 are useful if you just have to read the files,
# they are less useful if you have to create new copies with the same folder structure


def getallfilenames(inpath, allowedexts):
    filenames = []
    for root, dirs, thefiles in os.walk(inpath):
        for filename in thefiles:
            fullname = os.path.join(root, filename)
            (base, ext) = os.path.splitext(filename)
            if ext in allowedexts:
                filenames.append(fullname)
    return filenames


def iterallfilenames(inpath, allowedexts):
    filenames = []
    for root, dirs, thefiles in os.walk(inpath):
        for filename in thefiles:
            fullname = os.path.join(root, filename)
            (base, ext) = os.path.splitext(filename)
            if ext in allowedexts:
                yield fullname


# @@add functions that arev useful if you have make new versions with the same folder structure

def reportevery(ctr, repevery, sep=' ', maxwidth=100, file=sys.stderr):
    global reportwidth
    # curreportwidth = reportwidth
    if ctr % repevery == 0:
        ctrstr = str(ctr)
        lcurreport = len(ctrstr) + len(sep)
        if reportwidth + lcurreport > maxwidth:
            print(file=sys.stderr)
            reportwidth = lcurreport
        else:
            print(ctr, end=sep, file=file)
            sys.stderr.flush()
            reportwidth += len(str(ctr)) + len(sep)


def getbasename(fullname):
    path, filename = os.path.split(fullname)
    base, ext = os.path.splitext(filename)
    return base

def savecopy(infullname, prevsuffix='_previous', prevprefix='', outpath=None):
    thepath, infilename = os.path.split(infullname)
    base, ext = os.path.splitext(infilename)
    previousinfilename = prevprefix + base + prevsuffix + ext
    if outpath is None:
        outpath = thepath
    previousinfullname = os.path.join(outpath, previousinfilename)
    shutil.copyfile(infullname, previousinfullname)


def getsamplename(fn: FileName) -> str:
    basename = getbasename(fn)
    samplename = basename[:basename.rfind('_')]
    return samplename

def get_dataset_samplename(fn: FileName) -> str:
    bgn, last = os.path.split(fn)    # ...auristrain/intreebanks/dld03.xml -> (...auristrain/intreebanks,
    # dld03.xml)
    bgn2, last2 = os.path.split(bgn) # ...auristrain/intreebanks -> (...auristrain, intreebanks)
    # if last2  != intreebanksfolder issue a warning
    bgn3, datasetname = os.path.split(bgn2)  # ...auristrain -> (..., auristrain)
    samplename, ext = os.path.splitext(last)
    return datasetname, samplename


def make_filelist(cat: str, datasetname: str, sample_uttids_tuples: Tuple[str, List[str]], outpath: str ) -> None:
    filelist_title = f'{datasetname}_{cat}'
    filelist_name = f'{filelist_title}.fl'
    filelist = [[filelist_title]]
    file_list_fullname = os.path.join(outpath, filelist_name)
    treespath = os.path.join(settings.DATAROOT, datasetname, outtreebanksfolder, treesfolder)
    for samplename, uttids in sample_uttids_tuples:
        foldername = f'{samplename}{correctedsuffix}'
        for uttid in uttids:
            fulluttid = lpad(uttid, size=3)
            filename = f'{samplename}{correctedsuffix}_{fulluttid}.xml'
            fullname = os.path.join(treespath, foldername, filename)
            filelist.append([fullname])
    writecsv(filelist, file_list_fullname)


def get_corrected_tree_fullname(datasetname, samplename, uttid) -> str:
    correctedname = f'{samplename}{correctedsuffix}'
    fullpath = os.path.join(settings.DATAROOT, datasetname,
                            outtreebanksfolder, treesfolder, correctedname)
    filename = f'{correctedname}_{lpad(uttid)}.xml'
    fullname = os.path.join(fullpath, filename)
    return fullname

