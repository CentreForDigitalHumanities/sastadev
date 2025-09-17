from lxml import etree
import os
from sastadev.sastatypes import FileName, TreeBank
from sastadev.conf import settings
from sastadev.constants import outtreebanksfolder, treesfolder
from sastadev.datasets import DataSet
from sastadev.readcsv import writecsv
from sastadev.treebankfunctions import getmeta, getxsid

tree_extension = '.xml'
propersize = 3
reportevery = 10

def treebank2trees(treebank: TreeBank, datasetname: str, infilename: FileName, verbose: bool = False):
    (path, fn) = os.path.split(infilename)
    (base, ext) = os.path.splitext(fn)
    outfolder = base
    outpath = os.path.join(settings.DATAROOT, datasetname, outtreebanksfolder, treesfolder, outfolder)
    filelistname = f'{outfolder}.fl'
    filelistfullname = os.path.join(outpath, filelistname)
    filelistheader = outfolder
    filelist = [[filelistheader]]
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    for syntree in treebank:
        xsid = getxsid(syntree)
        lxsid = len(xsid)
        if lxsid > propersize:
            properxsid = lxsid
            # issue a warning
        else:
            properxsid = (propersize - lxsid) * '0' + xsid
        outfilename = f'{outfolder}_{properxsid}{tree_extension}'
        outfullname = os.path.join(outpath, outfilename)
        newtree = etree.ElementTree(syntree)
        newtree.write(outfullname, encoding="UTF8", xml_declaration=False, pretty_print=True) # no XML declarations
        filelist.append([outfullname])
    writecsv(filelist, filelistfullname)
