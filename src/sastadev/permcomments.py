from math import isnan
import os
from collections import Counter
from sastadev.conf import settings
from sastadev.constants import (checksuffix, errorsummaryfolder, errorsummarysuffix, intreebanksfolder,
                                silverpermfolder as permfolder, resultsfolder)
from sastadev.counterfunctions import counter2liststr
from sastadev.xlsx import  getxlsxdata, mkworkbook
from sastadev.filefunctions import savecopy
from typing import List

commentdelsym = '!'
commentsep = ';'

qid = 'qid'
uttid = 'uttid'
pos = 'pos'

pcheaders = [
    ['Sample', 'User1', 'User2', 'User3', 'MoreorLess', qid,  'inform', 'cat', 'subcat', 'item', uttid, pos, 'utt',
     'origutt', 'parsed_as', 'marking']]

platinumcheck_column_widths = {'F:F': 9, 'G:G': 8.11, 'K:K': 6.44, 'L:L': 5.44, 'M:M': 26, 'N:N': 26, 'O:O': 26 }
sampleheaders = ['sample']

permprefix = 'perm_'

permsilvercolcount = 8   # number of columns in the silverperm files
checkfilecolcount = 16

samplecol = 0
user1col = 1
user2col = 2
user3col = 3
moreorlesscol = 4
qidcol = 5
uttidcol = 10
poscol = 11

permsamplecol = 0
permuser1col = 1
permuser2col = 2
permuser3col = 3
permqidcol = 4
permuttidcol = 5
permposcol = 6
permmoreorlesscol = 7




uttidscol = 5  # in platinum-edited tsv files

nots = ['not']
oks = ['ok', 'oke']
undecideds = ['?', 'ok/not', 'not/ok']
allowedoknots = oks + nots + undecideds
legalmoreorlesses = ['More examples', 'Missed examples']
comma = ','
commaspace = ', '



def getallcomments(dataset, sample):
    datasetpath = os.path.join(settings.DATAROOT, dataset)
    intreebankspath = os.path.join(datasetpath, intreebanksfolder)
    filename = os.path.join(intreebankspath, f'{sample}.xml')
    permdatadict = dict()

    # read the permsample file, add to permdatadict
    permfilename = f'perm_{sample}.xlsx'
    permpath = os.path.join(settings.SD_DIR, settings.DATAROOT, dataset, permfolder)
    if not os.path.exists(permpath):
        os.makedirs(permpath)
    permfullname = os.path.join(permpath, permfilename)
    permdatadict, perm_header = updatepermdict(permfullname, permdatadict, permfile=True)

    # read the check file, add to permdatadict
    checkfilename = f'{sample}{checksuffix}.xlsx'
    resultspath = os.path.join(settings.SD_DIR, settings.DATAROOT, dataset, resultsfolder)
    if not os.path.exists(resultspath):
        os.makedirs(resultspath)
    checkfullname = os.path.join(resultspath, checkfilename)
    permdatadict, checkheader = updatepermdict(checkfullname, permdatadict)

    # read the errorsummary files, add to permdatadict
    errorsummarypath = os.path.join(settings.SD_DIR, settings.DATAROOT, dataset, errorsummaryfolder)
    if not os.path.exists(errorsummarypath):
        os.makedirs(errorsummarypath)
    errorsummaryfilenames = [fn for fn in os.listdir(errorsummarypath) if fn.endswith(errorsummarysuffix+'.xlsx')]
    for errorsummaryfilename in errorsummaryfilenames:
        errorsummaryfullname = os.path.join(errorsummarypath, errorsummaryfilename)
        permdatadict, errorsummaryheader = updatepermdict(errorsummaryfullname, permdatadict, sample=sample)


    # make a copy of the original permfullname if it exists
    if os.path.exists(permfullname):
        savecopy(permfullname, prevsuffix='', prevprefix='previous_')
    # write the permdatadict to perfullname
    writeperm2excel(permdatadict, perm_header, permfullname)

    return permdatadict

def removeduplicates(rawel: str) -> str:
    rawels = rawel.split(commentsep)
    els = [rawel.strip() for rawel in rawels]
    newels = []
    for el in els:
        if el not in newels:
            newels.append(el)
    result = commentsep.join(newels)
    return result


def removedelsym(coms: List[str]) -> List[str]:
    newcoms = []
    for com in coms:
        if com.startswith(commentdelsym):
            newcoms.append(com[1:])
        else:
            newcoms.append(com)
    return newcoms
def smartmerge(com1:str, com2:str) -> str:
    rawcom1s = com1.split(commentsep)
    com1s = [rawcom1.strip() for rawcom1 in rawcom1s]
    rawcom2s = com2.split(commentsep)
    com2s = [rawcom2.strip() for rawcom2 in rawcom2s]
    toremove = [com1[1:] for com1 in com1s if com1.startswith(commentdelsym)] + \
               [com2[1:] for com2 in com2s if com2.startswith(commentdelsym)]
    com1s = removedelsym(com1s)
    com2s = removedelsym(com2s)
    newcoms = [com1 for com1 in com1s if com1 not in toremove]
    for com in com2s:
        if com not in newcoms and com not in toremove:
            newcoms.append(com)
    result = commentsep.join(newcoms)
    return result



def mergerows(row1, row2):
    newrow = []
    for i, eltuple in enumerate(zip(row1, row2)):
        rawel1, rawel2 = eltuple
        el1, el2 = removeduplicates(rawel1), removeduplicates(rawel2)
        if el1.lower() == el2.lower():
            newel = el2
        elif el2 == '':
            newel = el1
        elif el1 == '':
            newel = el2
        else:
            newel = smartmerge(el1, el2)
        newrow.append(newel)
    return newrow

def updatepermdict(fullname, permdict, sample=None, permfile=False):
    header, data = getxlsxdata(fullname)
     # if data == []:
     #    settings.LOGGER.warning(f'No data found in {fullname}')
    colcount = permsilvercolcount if permfile else checkfilecolcount
    colsok = checkpermformat(header, data, colcount, strict=False)
    silverfulldatadict = silverdata2dict(data, sample=sample, permfile=permfile)

    #Voeg silverfulldatadict toe aan permdict
    for key in silverfulldatadict:
        if key not in permdict:
            permdict[key] = silverfulldatadict[key]
        elif key in permdict:
            newval = mergerows(permdict[key], silverfulldatadict[key])
            # for i in overwritten:
            #     settings.LOGGER.warning(f'Key: {key}; usercol{i+1} value:\n ({silverfulldatadict[key][i]}) \noverwritten by value:\n {permdict[key][i]};\n File: {fullname}' )
            permdict[key] = newval
    return permdict, header

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

def silverdata2dict(silverdata, sample=None, permfile=False):
    #make a dictionary out of data: a list of rows
    #silverdict = dict()
    silverfulldatadict = dict()
    if silverdata is not None:
        for rowctr, therow in enumerate(silverdata):
            if permfile:
                if len(therow) >= permposcol:
                    thesample = therow[permsamplecol].lower()
                    user1 = therow[permuser1col]
                    user2 = therow[permuser2col]
                    user3 = therow[permuser3col]
                    qid = therow[permqidcol]
                    uttid = str(therow[permuttidcol])
                    pos = therow[permposcol]
                    moreorless = therow[permmoreorlesscol]
                    thekey = (thesample, qid, uttid, pos, moreorless)
            else:
                if len(therow) >= poscol:
                    thesample = therow[samplecol].lower()
                    user1 = therow[user1col]
                    user2 = therow[user2col]
                    user3 = therow[user3col]
                    qid = therow[qidcol]
                    uttid = str(therow[uttidcol])
                    pos = therow[poscol]
                    moreorless = therow[moreorlesscol]
                    thekey = (thesample, qid, uttid, pos, moreorless)
                    # only add it when any of user1, user2, user3 has a nonempty value
            if not (nono(user1) and nono(user2) and nono(user3)):
                #silverdict[thekey] = (user1, user2, user3)
                if sample is None or thesample == sample.lower():
                    silverfulldatadict[thekey] = [user1, user2, user3]
    return silverfulldatadict  # , silverdict


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

