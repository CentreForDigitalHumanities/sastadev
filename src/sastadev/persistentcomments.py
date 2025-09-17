from math import isnan
import os
from collections import Counter
from sastadev.conf import settings
from sastadev.counterfunctions import counter2liststr
from sastadev.xlsx import  getxlsxdata, mkworkbook
from sastadev.filefunctions import savecopy
from typing import Callable, List

defaultcommentdelsym = '!'
defaultcommentsep = ';'


platinumcheck_column_widths = {'F:F': 9, 'G:G': 8.11, 'K:K': 6.44, 'L:L': 5.44, 'M:M': 26, 'N:N': 26, 'O:O': 26 }
sampleheaders = ['sample']

permprefix = 'perm_'

permsilvercolcount = 8   # number of columns in the silverperm files
checkfilecolcount = 16

class FileDescription():
    def __init__(self, folders, filenamecondition):
        self.folders: List[str] = folders
        self.filenamecondition: Callable[[str], bool] = filenamecondition

class PersistentComments():
    def __init__(self, filedescriptions, persistentcommentsfolder, mkpersistentfilename, keycolumns,
                 commentcolumns, prevprefix = 'previous_', commentsep=defaultcommentsep,
                 commentdelsym=defaultcommentdelsym):
        self.filedescriptions: List[FileDescription] = filedescriptions
        self.persistentcommentsfolder : str = persistentcommentsfolder
        self.mkpersistentfilename: Callable[[str], str] = mkpersistentfilename
        self.keycolumns: List[int] = keycolumns
        self.commentcolumns: List[int] = commentcolumns
        self.prevprefix: str = prevprefix
        self.commentsep : str = commentsep
        self.commentdelsym : str = commentdelsym

    def getallcomments(self, dataset):
        permdatadict = dict()

        # read the permsample file, add to permdatadict
        permfilename = self.mkpersistentfilename(dataset)
        if not os.path.exists(self.persistentcommentsfolder):
            os.makedirs(self.persistentcommentsfolder)
        permfullname = os.path.join(self.persistentcommentsfolder, permfilename)
        permdatadict, perm_header = self.updatepermdict(permfullname, permdatadict, permfile=True)

        # read the comments from the files characterized by the filedescriptions
        for filedescription in self.filedescriptions:
            for folder in filedescription.folders:
                rawfilenames = os.listdir(folder)
                filenames = [ fn for fn in rawfilenames if filedescription.filenamecondition(fn)]
                for filename in filenames:
                    fullname = os.path.join(folder, filename)
                    permdatadict, checkheader = self.updatepermdict(fullname, permdatadict, self.keycolumns, self.commentcolumns)

        # make a copy of the original permfullname if it exists
        if os.path.exists(permfullname):
            savecopy(permfullname, prevsuffix='', prevprefix=self.prevprefix)

        # write the permdatadict to perfullname
        writeperm2excel(permdatadict, perm_header, permfullname)

        return permdatadict

    def removeduplicates(self, rawel: str) -> str:
        rawels = rawel.split(self.commentsep)
        els = [rawel.strip() for rawel in rawels]
        newels = []
        for el in els:
            if el not in newels:
                newels.append(el)
        result = self.commentsep.join(newels)
        return result

    def removedelsym(self, coms: List[str]) -> List[str]:
        newcoms = []
        for com in coms:
            if com.startswith(self.commentdelsym):
                newcoms.append(com[1:])
            else:
                newcoms.append(com)
        return newcoms

    def smartmerge(self, com1: str, com2: str) -> str:
        rawcom1s = com1.split(self.commentsep)
        com1s = [rawcom1.strip() for rawcom1 in rawcom1s]
        rawcom2s = com2.split(self.commentsep)
        com2s = [rawcom2.strip() for rawcom2 in rawcom2s]
        toremove = [com1[1:] for com1 in com1s if com1.startswith(self.commentdelsym)] + \
                   [com2[1:] for com2 in com2s if com2.startswith(self.commentdelsym)]
        com1s =self.removedelsym(com1s)
        com2s = self.removedelsym(com2s)
        newcoms = [com1 for com1 in com1s if com1 not in toremove]
        for com in com2s:
            if com not in newcoms and com not in toremove:
                newcoms.append(com)
        result = self.commentsep.join(newcoms)
        return result

    def mergerows(self, row1, row2):
        newrow = []
        for i, eltuple in enumerate(zip(row1, row2)):
            rawel1, rawel2 = eltuple
            el1, el2 = self.removeduplicates(rawel1), self.removeduplicates(rawel2)
            if el1.lower() == el2.lower():
                newel = el2
            elif el2 == '':
                newel = el1
            elif el1 == '':
                newel = el2
            else:
                newel = self.smartmerge(el1, el2)
            newrow.append(newel)
        return newrow

    def updatepermdict(self, fullname, permdict, keycolumns, commentcolumns, sample=None, permfile=False):
        header, data = getxlsxdata(fullname)
        # if data == []:
        #    settings.LOGGER.warning(f'No data found in {fullname}')
        colcount = permsilvercolcount if permfile else checkfilecolcount
        colsok = checkpermformat(header, data, colcount, strict=False)
        silverfulldatadict = silverdata2dict(data, keycolumns, commentcolumns, sample=sample, permfile=permfile)

        # Voeg silverfulldatadict toe aan permdict
        for key in silverfulldatadict:
            if key not in permdict:
                permdict[key] = silverfulldatadict[key]
            elif key in permdict:
                newval = self.mergerows(permdict[key], silverfulldatadict[key])
                # for i in overwritten:
                #     settings.LOGGER.warning(f'Key: {key}; usercol{i+1} value:\n ({silverfulldatadict[key][i]}) \noverwritten by value:\n {permdict[key][i]};\n File: {fullname}' )
                permdict[key] = newval
        return permdict, header


nots = ['not']
oks = ['ok', 'oke']
undecideds = ['?', 'ok/not', 'not/ok']
allowedoknots = oks + nots + undecideds
legalmoreorlesses = ['More examples', 'Missed examples']
comma = ','
commaspace = ', '






def rowsequal(row1, row2, casesensitive=False):
    if len(row1) != len(row2):
        return False
    pairs = zip(row1, row2)
    for el1, el2 in pairs:
        if isinstance(el1, str) and isinstance(el2, str):
            if el1.lower() != el2.lower():
                return False
        elif el1 != el2:
            return False
    return True



def writeperm2excel(datadict, header, filename):
    data = [[key[0]] + datadict[key] + list(key[1:]) for key in datadict]
    workbook = mkworkbook(filename, [header], data)
    workbook.close()


def getheader(data):
    if data is None:
        result = []
    else:
        result = data.head()
    return result

def checkpermformat(header, data, colcount, strict=True):
    result = True
    lheader = len(header)
    if (lheader == 0 or header == ['']) and data == []:
        return True
    result = lheader == colcount
    if result:
        rowctr = 0
        for row in data:
            rowctr += 1
            lrow = len(row)
            result = lrow == colcount
            if not result:
                settings.LOGGER.error('Wrong # columns ({} instead of {}), row {}'.format(lrow, colcount, rowctr))
                if strict:
                    exit(-1)
                else:
                    return False
    else:
        settings.LOGGER.error('Wrong # columns ({} instead of {}) in the header'.format(lheader, colcount,))
        if strict:
            exit(-1)
        else:
            return False
    return result

def silverdata2dict(silverdata, keycolumns, commentcolumns, permfile=False):
    #make a dictionary out of data: a list of rows
    #silverdict = dict()
    mincolcount = max(max(keycolumns), max(commentcolumns))
    silverfulldatadict = dict()
    if silverdata is not None:
        for rowctr, therow in enumerate(silverdata):
            if permfile:
                lkeycolumns = len(keycolumns)
                lcommentcolumns = len(commentcolumns)
                if len(therow) == lkeycolumns + lcommentcolumns:
                    thekey = [therow[i] for i in range(lkeycolumns)]
                    thecomments = [therow[i] for i in range(lkeycolumns, lkeycolumns + lcommentcolumns)]
            else:
                if len(therow) >= mincolcount:
                    thecomments = [therow[i].lower() for i in commentcolumns]
                    thekey = tuple([therow[i].lower() for i in keycolumns])
                    # only add it when any of user1, user2, user3 has a nonempty value
            if not all([nono(el) for el in thecomments]) :
                #silverdict[thekey] = (user1, user2, user3)
                silverfulldatadict[thekey] = thecomments
    return silverfulldatadict


def nono(inval):
    result = (inval is None) or (inval == 0) or (inval == []) or (inval == '')
    return result


def myisnan(inval):
    try:
        result = isnan(inval)
    except Exception:
        result = False
    return result

def clean(inval):
    #if type(inval) != str:
    #    print('nonstring value: {}'.format(inval))
    instr = str(inval)
    result = instr.strip()
    result = result.lower()
    return result


def listminus(list1, list2):
    clist1 = Counter(list1)
    clist2 = Counter(list2)
    cresult = clist1 - clist2
    result = counter2liststr(cresult)
    return result

