"""
This module offers the function get_annotations() to obtain a dictionary with the annotations from a file
for the moment at the utteranceid level, to be extended to the wordposition per uttid level

and the function read_annotations() to obtain a score dictionary with queryid as keys and Counter() as values
"""

# todo
# -additional columns unaligned treatment and generalisation
# -code alternatives and replacemtne extensions
# =codes written without spaces?

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Match, Optional, Pattern, Tuple

from sastadev import xlsx
from sastadev.allresults import ResultsKey, mkresultskey
from sastadev.anonymization import getname
from sastadev.conf import settings
from sastadev.methods import Method
from sastadev.readmethod import itemseppattern
from sastadev.sastatypes import (ExactResults, FileName, Item, Level, Position,
                                 QId, QueryDict, UttId, UttWordDict)

varitem = ''

txtext = ".txt"
comma = ","
space = ' '
tsvext = '.tsv'
commaspace = ', '
tab = '\t'
all_levels = set()

# @@next must be made dependent on the method
literallevels = ['literal', 'lemma']
commentslevels = ['comments', 'commentaar', 'opmerkingen', 'qa']

semicolon = ';'
labelsep = semicolon

wordcolheaderpattern = r'^\s*word\d+\s*$'
wordcolheaderre = re.compile(wordcolheaderpattern)
firstwordcolheaderpattern = r'^\s*word0*1\s*$'
firstwordcolheaderre = re.compile(firstwordcolheaderpattern)

speakerheaders = ['speaker', 'spreker', 'spk']
uttidheaders = ['uiting', 'id', 'utt', 'uttid', ]
levelheaders = ['level']
stagesheaders = ['fases', 'stages']
commentsheaders = ['opmerkingen', 'comments', 'commentaar']
unalignedheaders = ['hele uiting', 'unaligned', 'hele zin']

uttlevels = ['utt', 'uiting']
def nested_dict(n: int,
                type: type):  # I do not know how to characterize the result type Dict n times deep endin gwith values of type type
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n - 1, type))


def clean(label: str) -> str:
    result = label
    result = result.lstrip()
    result = result.rstrip()
    result = result.lower()
    return result


def getlabels(labelstr: str, allvaliditems: List[str], themethod: Method) -> List[str]:
    separators = themethod.separators
    rawlabels = re.split(separators, labelstr)
    labels = [rawlabel.strip() for rawlabel in rawlabels]
    validlabels = []
    for label in labels:
        if label in allvaliditems:
            validlabels.append(label)
        elif label == '':
            pass
        else:
            settings.LOGGER.warning(
                f'Cannot interpret {label} in {labelstr}; ignored')
    return validlabels


def oldgetlabels(labelstr: str, patterns: Tuple[Pattern, Pattern]) -> List[str]:
    results = []
    (pattern, fullpattern) = patterns
    if fullpattern.match(labelstr):
        ms = pattern.finditer(labelstr)
        results = [m.group(0) for m in ms if m.group(0) not in ' ;,-/']
    else:
        results = []
        ms = pattern.finditer(labelstr)
        logstr = str([m.group(0) for m in ms if m.group(0) not in ' ;,-'])
        # print('Cannot interpret {};  found items: {}'.format(labelstr,logstr), file=sys.stderr)
        settings.LOGGER.warning(
            'Cannot interpret %s; found items: %s', labelstr, logstr)
        # exit(-1)
    return results


def isuttlevel(level: str) -> bool:
    return level.lower() in uttidheaders


def iswordcolumn(str: str) -> Optional[Match[str]]:
    result = wordcolheaderre.match(str.lower())
    return result


def isfirstwordcolumn(str: str) -> Optional[Match[str]]:
    result = firstwordcolheaderre.match(str.lower())
    return result


def enrich(labelstr: str, lcprefix: str) -> str:
    labels = labelstr.split(labelsep)
    newlabels = []
    for label in labels:
        cleanlabel = clean(label)
        if label != "" and lcprefix != "":
            newlabels.append(lcprefix + ":" + cleanlabel)
        else:
            newlabels.append(cleanlabel)
    result = labelsep.join(newlabels)
    return result

def getcleanlevelsandlabels(thelabelstr: str, thelevel: str, prefix: str, allvaliditems: List[str], themethod: Method) \
        -> List[Tuple[str, str]]:
    results: List[Tuple[str, str]] = []
    lcthelabelstr = thelabelstr.lower()
    lcprefix = prefix.lower().strip()
    lcthelabelstr = enrich(lcthelabelstr, lcprefix)
    thelabels = getlabels(lcthelabelstr, allvaliditems, themethod)
    for thelabel in thelabels:
        if thelabel != "":
            cleanlabel = thelabel
            cleanlevel = clean(thelevel)
            result = (cleanlevel, cleanlabel)
            results.append(result)

    return results


def get_annotations(infilename: FileName, allitems: List[str], themethod: Method) \
        -> Tuple[UttWordDict, Dict[Tuple[Level, Item], List[Tuple[UttId, Position]]]]:
    '''
    Reads the file with name filename in SASTA Annotation Format
    :param infilename:
    :param allitems: list of all valid items
    :param themethod: the method
    :return: a dictionary  with as  key a tuple (level, item) and as value a list of (uttid, tokenposition) pairs
    '''

    thedata = defaultdict(list)

    allutts = {}

    # To open Workbook
    header, data = xlsx.getxlsxdata(infilename)

    levelcol = 1
    uttidcol = 0
    stagescol = -1
    commentscol = -1
    unalignedcol = -1

    # uttlevel = 'utt'

    uttcount = 0

    for col, val in enumerate(header):
        if iswordcolumn(val):
            lastwordcol = col
            if isfirstwordcolumn(val):
                firstwordcol = col
        elif clean(val) in speakerheaders:
            spkcol = col
        elif clean(val) in uttidheaders:
            uttidcol = col
        elif clean(val) in levelheaders:
            levelcol = col
        elif clean(val) in stagesheaders:
            stagescol = col
        elif clean(val) in commentsheaders:
            commentscol = col
        elif clean(val) in unalignedheaders:
            unalignedcol = col
        else:
            pass  # maybe warn here that an unknow column header has been encountered?
    startcol = min([col for col in [firstwordcol, unalignedcol, commentscol, stagescol] if col >=0])
    for row in data:
        if row[uttidcol] != "":
            # this might go wrong if there is no integer there @@make it robust: removed int()
            uttid = str(row[uttidcol])
        thelevel = row[levelcol]
        thelevel = clean(thelevel)
        all_levels.add(thelevel)
        # if thelevel == uttlevel:
        #    uttcount += 1
        curuttwlist = []
        for colctr in range(startcol, len(row)):
            if thelevel in uttlevels:
                rawcurcellval = str(row[colctr])
                curcellval = getname(rawcurcellval)
                if curcellval != '':
                    curuttwlist.append(curcellval)
            elif thelevel in literallevels and colctr != stagescol and colctr != commentscol:
                rawthelabel = str(row[colctr])
                thelabel = getname(rawthelabel)
                if colctr > lastwordcol:
                    tokenposition = 0
                else:
                    tokenposition = colctr - firstwordcol + 1
                cleanlevel = thelevel
                cleanlabel = thelabel
                if cleanlabel != '':
                    thedata[(cleanlevel, cleanlabel)].append((uttid, tokenposition))
            elif thelevel in commentslevels:
                pass
            elif thelevel not in uttlevels and colctr != stagescol and colctr != commentscol:
                thelabelstr = row[colctr]
                thelevel = row[levelcol]
                if colctr == unalignedcol:
                    prefix = ''
                if lastwordcol + 1 <= colctr < len(row):
                    # prefix = headers[colctr] aangepast om het simpeler te houden
                    prefix = ""
                else:
                    prefix = ""
                cleanlevelsandlabels = getcleanlevelsandlabels(
                    thelabelstr, thelevel, prefix, allitems, themethod)
                if colctr > lastwordcol or colctr == unalignedcol:
                    tokenposition = 0
                else:
                    tokenposition = colctr - firstwordcol + 1
                for (cleanlevel, cleanlabel) in cleanlevelsandlabels:
                    thedata[(cleanlevel, cleanlabel)].append(
                        (uttid, tokenposition))
        if curuttwlist != []:
            allutts[uttid] = curuttwlist
    return allutts, thedata


def update(thedict: Dict[ResultsKey, Tuple[Level, Item, ExactResults]], reskey: ResultsKey,
           goldtuple: Tuple[Level, Item, ExactResults]):
    (level, item, thecounter) = goldtuple
    if reskey in thedict:
        (oldlevel, olditem, oldcounter) = thedict[reskey]
        thedict[reskey] = (oldlevel, olditem, oldcounter + thecounter)
    else:
        thedict[reskey] = goldtuple


def oldgetitem2levelmap(mapping: Dict[Tuple[Item, Level], Any]) -> Dict[Item, List[Level]]:
    resultmap: Dict[Item, List[Level]] = {}
    for (item, level) in mapping:
        if item in resultmap:
            resultmap[item].append(level)
        else:
            resultmap[item] = [level]
    return resultmap


def getitem2levelmap(mapping: Dict[Tuple[Item, Level], Any]) -> Dict[Item, Level]:
    resultmap: Dict[Item, Level] = {}
    for (item, level) in mapping:
        if item in resultmap:
            settings.LOGGER.error(
                'Duplicate level {} for item {} with level {} ignored'.format(level, item, resultmap[item]))
        else:
            resultmap[item] = level
    return resultmap


def codeadapt(c: str) -> str:
    result = c
    result = re.sub(r'\.', r'\\.', result)
    result = re.sub(r'\(', r'\\(', result)
    result = re.sub(r'\)', r'\\)', result)
    result = re.sub(r'\?', r'\\?', result)
    result = re.sub(r'\*', r'\\*', result)
    result = re.sub(r'\+', r'\\+', result)
    result = re.sub(r' ', r'\\s+', result)
    return result


def mkpatterns(allcodes: List[str]) -> Tuple[Pattern, Pattern]:
    basepattern = r''
    sortedallcodes = sorted(allcodes, key=len, reverse=True)
    adaptedcodes = [codeadapt(c) for c in sortedallcodes]
    basepattern = r'' + '|'.join(adaptedcodes) + '|' + itemseppattern
    fullpattern = r'^(' + basepattern + r')*$'
    return (re.compile(basepattern), re.compile(fullpattern))


# def get_golddata(filename: FileName, mapping: Dict[Tuple[Item, Level], QId],
#                  altcodes: Dict[Tuple[Item, Level], Tuple[Item, Level]],
#                  queries: QueryDict, includeimplies: bool = False) \
#         -> Tuple[UttWordDict, Dict[QId, Tuple[Level, Item, List[Tuple[UttId, Position]]]]]:
def get_golddata(filename: FileName, themethod: Method, includeimplies: bool = False) \
        -> Tuple[UttWordDict, Dict[QId, Tuple[Level, Item, List[Tuple[UttId, Position]]]]]:

    # item2levelmap = {}
    mapping: Dict[Tuple[Item, Level], QId] = themethod.item2idmap
    altcodes: Dict[Tuple[Item, Level], Tuple[Item, Level]] = themethod.altcodes
    queries: QueryDict = themethod.queries
    includeimplies = False  # temporarily put off to test different implementation
    mappingitem2levelmap = getitem2levelmap(mapping)
    altcodesitem2levelmap = getitem2levelmap(altcodes)
    allmappingitems = [item for (item, _) in mapping]
    allaltcodesitems = [item for (item, _) in altcodes]
    allitems = allmappingitems + allaltcodesitems
    patterns = mkpatterns(allitems)
    allutts, basicdata = get_annotations(filename, allitems, themethod)
    results: Dict[ResultsKey, Tuple[Level, Item, ExactResults]] = {}
    for thelevel, theitem in basicdata:
        thecounter = basicdata[(thelevel, theitem)]
        # unclear why this below here is needed
        #        if (theitem, thelevel) in mapping:
        #            mappingitem = theitem
        #        elif (varitem, thelevel) in mapping:
        #            mappingitem = varitem
        #        else:
        #            mappingitem = theitem
        if thelevel in literallevels and (thelevel, thelevel) in mapping:
            # we still have to determine how to deal with this this is an attempt
            qid = mapping[thelevel, thelevel]
            reskey = mkresultskey(qid, theitem)
            update(results, reskey, (thelevel, theitem, thecounter))
        elif (theitem, thelevel) in mapping:
            qid = mapping[(theitem, thelevel)]
            reskey = mkresultskey(qid)
            update(results, reskey, (thelevel, theitem, thecounter))
            if includeimplies:
                for implieditem in queries[qid].implies:
                    impliedlevel = mappingitem2levelmap[implieditem]
                    if (implieditem, impliedlevel) in mapping:
                        impliedqid = mapping[(implieditem, impliedlevel)]
                        update(results, mkresultskey(impliedqid),
                               (impliedlevel, implieditem, thecounter))
                    else:
                        settings.LOGGER.error(
                            'Implied Item ({},{}) not found in mapping'.format(implieditem, impliedlevel))
        elif (theitem, thelevel) in altcodes:
            (altitem, altlevel) = altcodes[(theitem, thelevel)]
            qid = mapping[(altitem, altlevel)]
            reskey = mkresultskey(qid)
            update(results, reskey, (altlevel, altitem, thecounter))
            settings.LOGGER.info(
                '{} of level {} invalid code replaced by {} of level {}'.format(theitem, thelevel, altitem, altlevel))
            if includeimplies:
                for implieditem in queries[qid].implies:
                    impliedlevel = mappingitem2levelmap[implieditem]
                    if (implieditem, impliedlevel) in mapping:
                        impliedqid = mapping[(implieditem, impliedlevel)]
                        update(results, mkresultskey(impliedqid),
                               (impliedlevel, implieditem, thecounter))
                    else:
                        settings.LOGGER.error(
                            'Implied Item ({},{}) not found in mapping'.format(implieditem, impliedlevel))
        elif theitem in mappingitem2levelmap:  # valid item but wrong level
            thecorrectlevel = mappingitem2levelmap[theitem]
            qid = mapping[(theitem, thecorrectlevel)]
            reskey = mkresultskey(qid)
            update(results, reskey, (thecorrectlevel, theitem, thecounter))
            settings.LOGGER.info(
                'level {} of item {} replaced by correct level {}'.format(thelevel, theitem, thecorrectlevel))
            if includeimplies:
                for implieditem in queries[qid].implies:
                    impliedlevel = mappingitem2levelmap[implieditem]
                    if (implieditem, impliedlevel) in mapping:
                        impliedqid = mapping[(implieditem, impliedlevel)]
                        update(results, mkresultskey(impliedqid),
                               (impliedlevel, implieditem, thecounter))
                    else:
                        settings.LOGGER.error(
                            'Implied Item ({},{}) not found in mapping'.format(implieditem, impliedlevel))
        elif theitem in altcodesitem2levelmap:  # valid alternative item but wrong level
            theitemlevel = altcodesitem2levelmap[theitem]
            (thecorrectitem, thecorrectlevel) = altcodes[(
                theitem, theitemlevel)]
            qid = mapping[(thecorrectitem, thecorrectlevel)]
            reskey = mkresultskey(qid)
            update(results, reskey, (thecorrectlevel, thecorrectitem, thecounter))
            settings.LOGGER.info(
                'level {} of item {} replaced by correct level {} and item {}'.format(thelevel, theitem,
                                                                                      thecorrectlevel,
                                                                                      thecorrectitem))
            if includeimplies:
                for implieditem in queries[qid].implies:
                    impliedlevel = mappingitem2levelmap[implieditem]
                    if (implieditem, impliedlevel) in mapping:
                        impliedqid = mapping[(implieditem, impliedlevel)]
                        update(results, mkresultskey(impliedqid),
                               (impliedlevel, implieditem, thecounter))
                    else:
                        settings.LOGGER.error(
                            'Implied Item ({},{}) not found in mapping'.format(implieditem, thecorrectlevel))

        else:
            settings.LOGGER.error(
                '{} of level {} not a valid coding'.format(theitem, thelevel))
    return allutts, results


def exact2global(thedata: Dict[Tuple[Level, Item], ExactResults]) -> Dict[Tuple[Level, Item], Counter]:
    '''
    turns a dictionary with  as values a list of (uttid, pos) tuples into a dictionary with the same keys and as values a counter of uttid
    :param thedata:
    :return:
    '''

    cdata = {}
    for atuple in thedata:
        newvalue = [uttid for (uttid, _) in thedata[atuple]]
        cdata[atuple] = Counter(newvalue)
    return cdata


def richexact2global(thedata):
    '''
    turns a dictionary with  as values a tuple (level, item,list of (uttid, pos) tuples) into a dictionary with the
    same keys and as values a tuple (level, item, counter of uttid)
    :param thedata:
    :return:
    '''

    cdata = {}
    for thekey in thedata:
        (thelevel, theitem, exactlist) = thedata[thekey]
        newvalue = [uttid for (uttid, _) in exactlist]
        cdata[thekey] = (thelevel, theitem, Counter(newvalue))
    return cdata


def richscores2scores(richscores: Dict[ResultsKey, Tuple[Level, Item, Any]]) -> Dict[QId, Any]:
    scores = {}
    for reskey in richscores:
        scores[reskey] = richscores[reskey][2]
    return scores
