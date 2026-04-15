import itertools
import os
import re
from collections import Counter, defaultdict
from io import BytesIO

import xlsxwriter

from sastadev import xlsx
from sastadev.conf import settings
from sastadev.counterfunctions import counter2liststr
from sastadev.forms import getformfilename
from sastadev.allresults import mkresultskey

ordA = ord('A')
comma = ','
xlsxext = '.xlsx'

idpat = r'^[TSA][0-9]{3}$'
idcpat = r'^[TSA][0-9]{3}c$'
idre = re.compile(idpat)
idcre = re.compile(idcpat)

tarspformsuffix = '_TARSP-Form'

#tarspformsuffixext = tarspformsuffix + xlsxext
#intreebanksfolder = 'intreebanks'

bb = 'bold_bottom'
bt = 'bold_top'
lb = 'line_bottom'
lt = 'line_top'
ll = 'line_left'
lr = 'line_right'
tw = 'text_wrap'

row_len = 56
col_len = 26


tarsp_2005_size = (row_len, col_len)
all_cells = itertools.product(range(tarsp_2005_size[0]), range(tarsp_2005_size[1]),)
textwrapcolumns = [2, 5, 8, 11, 14, 17, 20, 23]  # CFILORUX

# VOORN
# VERB
all_cols = list(range(col_len))
format_table = defaultdict(list)
for col in all_cols:
    if col in textwrapcolumns:
        for row in range(row_len):
            format_table[(row, col)].append(tw)
    format_table[(0, col)].append(lt)
    format_table[(1, col)].append(lt)
    format_table[(4, col)].append(bb)
    format_table[(11, col)].append(bb)
    for row in  [19, 27, 38, 43, 52, 55]:
        format_table[(row, col)].append(bb)
for col in  list(range(1, 19)) + list(range(20, col_len)):
    format_table[(7, col)].append(lb)
format_table[(8,19)].extend([bt, bb])                  # VOORN
format_table[(8,20)].extend([bt, bb])                  # VOORN
format_table[(8,21)].extend([bt, bb])                  # VOORN
for col in list(range(19)) + list(range(22, col_len)):
    format_table[(10, col)].append(bb)
format_table[(23,16)].extend([bt, bb])             # VERB
#for col in range(1, col_len):
#    format_table[(8, col)].append(lb)

# vertical lines
for row in range(row_len):
    format_table[(row, 0)].append(ll)
    format_table[(row, col_len-1)].append(lr)
for row in range(5, row_len):
    format_table[(row, 1)].append(ll)
for col in [7,  10, 13]:
    for row in range(11, row_len):
        format_table[(row,col)].append(ll)
for row in range(6, 12):
    format_table[(row,1)].extend([ll,lr])
for row in range(8, row_len):
    format_table[(row, 19)].append(ll)  # column T
    format_table[(row, 21)].append(lr)  # column V
for row in range(23, row_len):
    format_table[(row, 16)].extend([ll, lr])  # column Q


def mk_format(format_labels, workbook):
    theformat = workbook.add_format()
    if bb in format_labels:
        theformat.set_bottom(5)
    if bt in format_labels:
        theformat.set_top(5)
    if lb in format_labels and not bb in format_labels:
        theformat.set_bottom(1)
    if lt in format_labels and not bt in format_labels:
        theformat.set_top(1)
    if ll in format_labels:
        theformat.set_left(1)
    if lr in format_labels:
        theformat.set_right(1)
    if tw in format_labels:
        theformat.set_text_wrap()
    return theformat

def getshortloc(colctr, rowctr):
    #colctr must be smaller than 26
    colstr = chr((colctr % 26) + ordA)
    rowstr = str(rowctr + 1)
    result = colstr + rowstr
    return result


# def oldreadbaseform(infilename):
#     basesheet = {}
#     wb = xlrd.open_workbook(infilename)
#     sheet = wb.sheet_by_index(0)
#     startrow = 0
#     startcol = 0
#     lastrow = sheet.nrows
#     lastcol = sheet.ncols
#     for rowctr in range(startrow, lastrow):
#         for colctr in range(startcol, lastcol):
#             curval = sheet.cell_value(rowctr, colctr)
#             if curval is not None and curval != '':
#                 basesheet[(rowctr, colctr)] = curval
#     return basesheet

def readbaseform(infilename):
    basesheet = {}
    header, data = xlsx.getxlsxdata(infilename)
    for rowctr, row in enumerate(data):
        for colctr, curval in enumerate(row):
            if curval is not None and curval != '':
                basesheet[(rowctr, colctr)] = curval
    return basesheet


def is_id(word):
    result = idre.match(word)
    return result


def is_idc(word):
    result = idcre.match(word)
    return result


def idc2id(word):
    if word[-1] == 'c':
        result = word[:-1]
    else:
        result = word
    return result


def getval(allresults, idx):
    if idx in allresults.coreresults:
        result = allresults.coreresults[idx]
    elif idx[0] in allresults.postresults:
        result = allresults.postresults[idx[0]]
    else:
        result = ''
    return result


def val2str(aval):
    if isinstance(aval, Counter):
        result = counter2liststr(aval)
    elif isinstance(aval, list):
        result = comma.join(aval)
    else:
        result = str(aval)
    return result


def mktarspform(allresults, _, in_memory=False):
    global basesheet

    if not in_memory:
        target = getformfilename(allresults.filename, tarspformsuffix)
        #(base, ext) = os.path.splitext(allresults.filename)
        #core, filename = os.path.split(base)
        #root, lastfolder = os.path.split(core)
        #if lastfolder == intreebanksfolder:
        #    target = os.path.join(root, 'forms', filename + tarspformsuffixext)
        #else:
        #   target = base + tarspformsuffixext
    else:
        target = BytesIO()

    workbook = xlsxwriter.Workbook(target, {"strings_to_numbers": True})
    worksheet = workbook.add_worksheet()

    # textwrap = workbook.add_format()
    # textwrap.set_text_wrap()
    boldbottom = workbook.add_format()
    boldbottom.set_bottom(5)

    for (rowctr, colctr) in all_cells:
        if (rowctr, colctr) in basesheet:
            curval = str(basesheet[(rowctr, colctr)])
        else:
            curval = ''
        if (rowctr, colctr) in format_table:
            theformat = mk_format(format_table[(rowctr, colctr)], workbook)
        else:
            theformat = workbook.add_format()
        if is_id(curval):
            curvalreskey = mkresultskey(curval)
            newval = getval(allresults, curvalreskey)
            # write newval to the new sheet
            newvalstr = val2str(newval)
            worksheet.write(rowctr, colctr, newvalstr, theformat)
        elif is_idc(curval):
            urval = idc2id(curval)
            urvalreskey = mkresultskey(urval)
            newval = getval(allresults, urvalreskey)
            cval = len(newval)
            newvalstr = val2str(cval)
            worksheet.write(rowctr, colctr, newvalstr, theformat)
        else:
            worksheet.write(rowctr, colctr, curval, theformat)

    #formatting
    # worksheet.set_row(3, cell_format=boldbottom)
    # textwrapcolumns = [2, 5, 8, 11, 14, 17, 20, 23]  # CFILORUX
    # for col in textwrapcolumns:
    #     worksheet.set_column(col, col, None, textwrap)

    # rawboldbottomrows = [12, 20, 28, 39, 44, 53, 56]
    # boldbottomrows = [i-1 for i in rawboldbottomrows]
    # for row in boldbottomrows:
    #     worksheet.set_row(row, row, boldbottom)

    columnwidths = {'B': 12, 'C': 14, 'D': 3, 'G': 3, 'H': 12, 'J': 3, 'K': 9, 'M': 3, 'N': 12, 'P': 3, 'S': 3, 'V': 3, 'W': 12, 'Y': 3, 'Z': 3}
    for row in columnwidths:
        range = row + ':' + row
        worksheet.set_column(range, columnwidths[row])

    # worksheet.set_landscape()
    worksheet.fit_to_pages(1, 1)
    worksheet.hide_gridlines(0)  # do not hide gridlines

    workbook.close()
    return target


# initialisation
basefilename = os.path.join(settings.SD_DIR, 'data', 'form_templates', 'TARSP Form Current.xlsx')
basesheet = readbaseform(basefilename)
junk = 0
