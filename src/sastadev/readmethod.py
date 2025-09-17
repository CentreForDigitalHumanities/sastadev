'''
This module defines the function read_method to read in a method:

* read_method(methodfilename: FileName) -> Method:
'''

from typing import List

from sastadev import xlsx
from sastadev.conf import settings
from sastadev.methods import Method, defaultfilters, tarsp, asta
from sastadev.query import Query, form_process, post_process
from sastadev.sastatypes import (AltCodeDict, FileName, Item_Level2QIdDict,
                                 QId, QueryDict)
from sastadev.stringfunctions import str2list

comma = ','

altitemsep = comma
implies_sep = comma
itemseppattern = r'[,-;\s]'


def getboolean(str: str) -> bool:
    if str is None:
        result = False
    elif str == '':
        result = False
    else:
        cleanstr = str.strip().lower()
        if cleanstr in ['no', 'false'] or cleanstr[0] in ['n', 'f']:
            result = False
        else:
            result = True
    return result


def getint(fase: str) -> int:
    try:
        result = int(fase)
    except Exception:
        result = 0
    return result


def get_pages(val: str) -> str:
    # pages = val.split(pagesep)
    # result = pages
    result = val
    return result


def getaltitems(str: str) -> List[str]:
    result = getlistofitems(str, altitemsep)
    return result


def getimplies(str: str) -> List[str]:
    result = getlistofitems(str, implies_sep)
    return result


def getlistofitems(str: str, sep: str) -> List[str]:
    rawresult = str.split(sep)
    cleanresult = [w.strip().lower() for w in rawresult]
    if cleanresult == ['']:
        cleanresult = []
    return cleanresult


# def oldread_method(methodfilename: FileName) -> Tuple[QueryDict, Item_Level2QIdDict, AltCodeDict, List[QId]]:
#     # To open Workbook
#     wb = xlrd.open_workbook(methodfilename)
#     sheet = wb.sheet_by_index(0)
#
#     idcol, catcol, subcatcol, levelcol, itemcol, altcol, impliescol, \
#         originalcol, pagescol, fasecol, querycol, informcol, screeningcol, processcol, special1col, special2col, commentscol = \
#         0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
#
#     headerrow = 0
#
#     queries: QueryDict = {}
#     item2idmap: Item_Level2QIdDict = {}
#     altcodes: AltCodeDict = {}
#
#     postquerylist: List[QId] = []
#     for rowctr in range(sheet.nrows):
#         if rowctr != headerrow:
#             id : QId = sheet.cell_value(rowctr, idcol).strip()
#             cat: str = sheet.cell_value(rowctr, catcol).strip()
#             subcat: str = sheet.cell_value(rowctr, subcatcol).strip()
#             level: str = sheet.cell_value(rowctr, levelcol).strip()
#             item: str = sheet.cell_value(rowctr, itemcol).strip()
#             altitems: List[str] = getaltitems(sheet.cell_value(rowctr, altcol))
#             implies: List[str] = getimplies(sheet.cell_value(rowctr, impliescol))
#             original: bool = getboolean(sheet.cell_value(rowctr, originalcol))
#             pages: str = get_pages(sheet.cell_value(rowctr, pagescol))
#             fase: int = getint(sheet.cell_value(rowctr, fasecol))
#             query: str = sheet.cell_value(rowctr, querycol)
#             inform: str = sheet.cell_value(rowctr, informcol)
#             screening: str  = sheet.cell_value(rowctr, screeningcol)
#             process: str = sheet.cell_value(rowctr, processcol).strip()
#             special1: str = sheet.cell_value(rowctr, special1col).strip()
#             special2: str = sheet.cell_value(rowctr, special2col).strip()
#             comments: str = sheet.cell_value(rowctr, commentscol)
#
#             queries[id] = Query(id, cat, subcat, level, item, altitems, implies, original, pages, fase, query, inform, screening, process,
#                                 special1, special2, comments)
#             if queries[id].process in [post_process, form_process]:
#                 postquerylist.append(id)
#             lcitem = item.lower()
#             lclevel = level.lower()
#             if (lcitem, lclevel) in item2idmap:
#                 settings.LOGGER.error('Duplicate (item, level) pair for {} and {}'.format(item2idmap[(lcitem, lclevel)], id))
#             item2idmap[(lcitem, lclevel)] = id
#             for altitem in altitems:
#                 lcaltitem = altitem.lower()
#                 if (lcaltitem, lclevel) in altcodes:
#                     settings.LOGGER.error('Duplicate (alternative item, level) pair for {} and {}'.format(altcodes[(lcaltitem, lclevel)], id))
#                 altcodes[(lcaltitem, lclevel)] = (lcitem, lclevel)
#
#         rowctr += 1
#     return (queries, item2idmap, altcodes, postquerylist)

def empty(row: list) -> bool:
    for el in row:
        if el != '':
            return False
    return True


def read_method(methodname: str, methodfilename: FileName, variant=None) -> Method:
    header, data = xlsx.getxlsxdata(methodfilename)

    idcol, catcol, subcatcol, levelcol, itemcol, altcol, impliescol, \
    originalcol, pagescol, fasecol, querycol, informcol, screeningcol, processcol, literalcol, starscol, filtercol, \
    variantscol, unused1col, unused2col, commentscol = \
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20

    headerrow = 0

    queries: QueryDict = {}
    item2idmap: Item_Level2QIdDict = {}
    altcodes: AltCodeDict = {}

    postquerylist: List[QId] = []
    for row in data:
        if not empty(row):
            id: QId = row[idcol].strip()
            cat: str = row[catcol].strip()
            subcat: str = row[subcatcol].strip()
            level: str = row[levelcol].strip()
            item: str = row[itemcol].strip()
            altitems: List[str] = getaltitems(row[altcol])
            implies: List[str] = getimplies(row[impliescol])
            original: bool = getboolean(row[originalcol])
            pages: str = str(get_pages(row[pagescol]))
            fase: int = getint(row[fasecol])
            query: str = row[querycol]
            inform: str = row[informcol]
            screening: str = row[screeningcol]
            process: str = row[processcol].strip()
            literal: str = row[literalcol].strip()
            stars: str = row[starscol].strip()
            filter: str = row[filtercol].strip()
            variants: str = str2list(row[variantscol])
            unused1: str = row[unused1col]
            unused2: str = row[unused2col]
            comments: str = row[commentscol]

            if variant is None and methodname == tarsp:
                variant = 'tarsp2017'
            if variant is None or variants == [] or variant in variants:

                queries[id] = Query(id, cat, subcat, level, item, altitems, implies, original, pages, fase, query,
                                    inform, screening, process, literal,
                                    stars, filter, variants, unused1, unused2, comments)
                if queries[id].process in [post_process, form_process]:
                    postquerylist.append(id)
                lcitem = item.lower()
                lclevel = level.lower()
                if (lcitem, lclevel) in item2idmap:
                    settings.LOGGER.error('Duplicate (item, level) pair for {} and {}'.format(
                        item2idmap[(lcitem, lclevel)], id))
                item2idmap[(lcitem, lclevel)] = id
                for altitem in altitems:
                    lcaltitem = altitem.lower()
                    if (lcaltitem, lclevel) in altcodes:
                        settings.LOGGER.error('Duplicate (alternative item, level) pair for {} and {}'.format(
                            altcodes[(lcaltitem, lclevel)], id))
                    altcodes[(lcaltitem, lclevel)] = (lcitem, lclevel)

    defaultfilter = defaultfilters[methodname]
    themethod = Method(methodname, queries, item2idmap, altcodes, postquerylist,
                       methodfilename, defaultfilter)

    return themethod
