from collections import Counter
from copy import copy
from typing import Tuple

from lxml import etree
from sastadev.conf import settings
from sastadev.allresults import ResultsKey, showreskey
from sastadev.sastatypes import Position, UttId
from sastadev.treebankfunctions import (find1, getattval, getmarkedyield,
                                        getyield, getparsedas)

tab = '\t'
space = ' '
eps = ''
slash = '/'

usercommentbegin = 1
usercommentuntil = 4
usercommentdefaultvalue = eps

more = 'More examples'
less = 'Missed examples'

samplecol = 0
informcol = 6
uttidcol = 10
markingcol = 15


def getmarkedutt(m, syntree):
    thewordlist = getyield(syntree)
    thepositions = getwordpositions(m, syntree)
    themarkedyield = getmarkedyield(thewordlist, thepositions)
    yieldstr = space.join(themarkedyield)
    return yieldstr


def mark(str):
    result = '*' + str + '*'
    return result


def getwordpositionsold(matchtree, syntree):
    positions1 = []
    for node in matchtree.iter():
        if 'pt' in node.attrib:
            if 'end' in node.attrib:
                positions1.append(node.attrib['end'])

    indexednodes = {}
    for node in syntree.iter():
        if 'index' in node.attrib and ('pt' in node.attrib or 'cat' in node.attrib or 'pos' in node.attrib):
            theindex = node.attrib['index']
            indexednodes[theindex] = node

    thequery2 = ".//node[@index and not(@pt) and not(@cat)]"
    try:
        matches2 = matchtree.xpath(thequery2)
    except etree.XPathEvalError:
        matches2 = []
    positions2 = []
    for m in matches2:
        positions2 += getwordpositions(m, syntree)
    positions = positions1 + positions2
    result = [int(p) for p in positions]
    return result


def getwordpositions(matchtree, syntree):
    # nothing special needs to be done for index nodes since they also have begin and end
    positions = []
    for node in matchtree.iter():
        if 'end' in node.attrib:
            positions.append(node.attrib['end'])
    result = [int(p) for p in positions]
    return result


def getfirstwordposition(matchtree):
    if 'begin' in matchtree.attrib:
        positionstr = getattval(matchtree, 'begin')
        position = int(positionstr) + 1
    else:
        position = 0
    return position


def mismatches(reskey, queries, theresultsminusgold, goldminustheresults, allmatches, allutts, platinumcheckfile):
    reskeystr = showreskey(reskey)
    queryid = reskey[0]
    if theresultsminusgold != {}:
        print('More examples', file=platinumcheckfile)
    for uttid in theresultsminusgold:
        if (reskey, uttid) in allmatches:
            for (m, syntree) in allmatches[(reskey, uttid)]:
                markedutt = getmarkedutt(m, syntree)
                platinumcheckrow1 = [reskeystr, queries[queryid].cat, queries[queryid].subcat, queries[queryid].item,
                                     uttid, markedutt]
                print(tab.join(platinumcheckrow1), file=platinumcheckfile)

    if goldminustheresults != {}:
        print('Missed examples', file=platinumcheckfile)
    for uttid in goldminustheresults:
        if uttid in allutts:
            uttstr = space.join(allutts[uttid])
        else:
            uttstr = ''
            settings.LOGGER.warning('uttid {} not in alluts'.format(uttid))
        platinumcheckrow2 = [reskeystr, queries[queryid].inform, queries[queryid].cat, queries[queryid].subcat, queries[queryid].item, uttid,
                             uttstr]
        print(tab.join(platinumcheckrow2), file=platinumcheckfile)


def getmarkposition(position, nodeendmap, uttid):
    if position == 0:
        result = 0
    elif uttid in nodeendmap:
        if str(position) in nodeendmap[uttid]:
            result = nodeendmap[uttid][str(position)]
        else:
            settings.LOGGER.error(
                'getmarkposition: No mapping found for position {} in utterance {}'.format(position, uttid))
            result = 0
    else:
        settings.LOGGER.error(
            'getmarkposition: No mappings found for uttid {}'.format(uttid))
        result = 0
    return result


def isliteralreskey(reskey: ResultsKey):
    (key, val) = reskey
    result = key != val
    return result


def literalmissedmatches(queries, exactresults, exactgoldscores, allmatches, allutts, analysedtreesdict, sample,
                         permsilverdatadict={}, annotationinput=False):
    newrows = []
    for reskey in exactgoldscores:
        if isliteralreskey(reskey) and reskey not in exactresults:
            reskeystr = showreskey(reskey)
            queryid = reskey[0]
            inform = queries[queryid].inform
            for hit in exactgoldscores[reskey]:
                (uttid, position) = hit
                if uttid in allutts:
                    # markposition = 1 if position == 0 else position
                    markposition = position
                    markedwordlist = getmarkedyield(
                        allutts[uttid], [markposition])
                    uttstr = space.join(markedwordlist)
                    # tree = allmatches[(reskey, uttid)][0][1] if (reskey, uttid) in allmatches else None
                    tree = analysedtreesdict[uttid] if uttid in analysedtreesdict else None
                    origutt = find1(tree, './/meta[@name="origutt"]/@value') if tree is not None else '**'
                    parsedas = getparsedas(tree, uttstr)

                else:
                    settings.LOGGER.warning(
                        'uttid {} not in allutts'.format(uttid))
                    uttstr = ""
                    markposition = 0
                    tree = allmatches[(reskey, uttid)][0][1] if (reskey, uttid) in allmatches else None
                    origutt = find1(tree, './/meta[@name="origutt"]/@value') if tree is not None else '**'
                    parsedas = getparsedas(tree, uttstr)

                platinumcheckrow2 = [reskeystr, inform, queries[queryid].cat, queries[queryid].subcat, queries[queryid].item,
                                     str(uttid),
                                     str(markposition),
                                     uttstr, origutt, parsedas]
                reskeystr = slash.join(reskey)
                moreorless = less
                key = (sample.lower(), reskeystr, uttid, position, moreorless)
                usercomments = getusercomments(permsilverdatadict, key, report=False)
                xlplatinumcheckrow2 = [sample] + usercomments + [moreorless] + platinumcheckrow2
                newrows.append(xlplatinumcheckrow2)
    return newrows


def exactmismatches(reskey, queries, exactresults, exactgoldscores, allmatches, allutts,
                    analysedtreesdict, sample,
                    permsilverdatadict={}, annotationinput=False):
    reskeystr = showreskey(reskey)
    queryid = reskey[0]
    inform = queries[queryid].inform
    theexactresults = exactresults[reskey] if reskey in exactresults else Counter()
    theexactgoldscores = exactgoldscores[reskey] if reskey in exactgoldscores else Counter()
    (theresultsminusgold, goldminustheresults, intersection) = exactcompare(theexactresults, theexactgoldscores)
    newrows = []
    for hit in theresultsminusgold:
        uttid, position = hit
        if (reskey, uttid) in allmatches or annotationinput:
            # markposition = 1 if position == 0 else position
            tree = allmatches[(reskey, uttid)][0][1] if (reskey, uttid) in allmatches else None
            origutt = find1(tree, './/meta[@name="origutt"]/@value') if tree is not None else '**'
            markposition = position
            if uttid in allutts:
                markedwordlist = getmarkedyield(allutts[uttid], [markposition])
                uttstr = space.join(markedwordlist)
                queryitem = reskey[1] if isliteralreskey(reskey) else queries[queryid].item
                parsedas = getparsedas(tree, uttstr)
                platinumcheckrow1 = [reskeystr, inform, queries[queryid].cat, queries[queryid].subcat, queryitem,
                                     str(uttid), str(markposition), uttstr, origutt, parsedas]
                moreorless = more
                key = (sample.lower(), reskey, uttid, position, moreorless)
                # breakpoint()
                usercomments = getusercomments(permsilverdatadict, key, report=True)
                xlplatinumcheckrow1 = [sample] + usercomments + [moreorless] + platinumcheckrow1
                newrows.append(xlplatinumcheckrow1)
            else:
                settings.LOGGER.error(
                    f'Uttid {uttid} not in allutts; reporting ignored')

    for hit in goldminustheresults:
        (uttid, position) = hit
        if uttid in allutts:
            # markposition = 1 if position == 0 else position
            markposition = position
            markedwordlist = getmarkedyield(allutts[uttid], [markposition])
            uttstr = space.join(markedwordlist)
            tree = allmatches[(reskey, uttid)][0][1] if (reskey, uttid) in allmatches else None
            tree = analysedtreesdict[uttid] if uttid in analysedtreesdict else None
            origutt = find1(tree, './/meta[@name="origutt"]/@value') if tree is not None else '**'
            parsedas = getparsedas(tree, uttstr)
        else:
            settings.LOGGER.warning('uttid {} not in allutts'.format(uttid))
            uttstr = ""
            markposition = 0
            tree = allmatches[(reskey, uttid)][0][1] if (queryid, uttid) in allmatches else None
            origutt = find1(tree, './/meta[@name="origutt"]/@value') if tree is not None else '**'
            parsedas = getparsedas(tree, uttstr)
        moreorless = less
        platinumcheckrow2 = [reskeystr, inform, queries[queryid].cat, queries[queryid].subcat, queries[queryid].item,
                             str(uttid),
                             str(markposition),
                             uttstr, origutt, parsedas]
        key = (sample.lower(), reskey, uttid, position, moreorless)
        usercomments = getusercomments(permsilverdatadict, key, report=False)
        xlplatinumcheckrow2 = [sample] + usercomments + [moreorless] + platinumcheckrow2
        newrows.append(xlplatinumcheckrow2)
    return newrows


def compareunaligned(resultctr, goldctr):
    """
    :param resultctr:
    :param goldctr:
    :return:
    """
    resultlist = counter2list(resultctr)
    goldlist = counter2list(goldctr)
    curgoldlist = copy(goldlist)
    newintersection = []
    takefromresultlist = []
    takefromgoldlist = []
    for (utt1, pos1) in resultlist:
        if (utt1, 0) in curgoldlist:
            takefromresultlist.append((utt1, pos1))
            takefromgoldlist.append((utt1, 0))
            newintersection.append((utt1, pos1))
            curgoldlist.remove((utt1, 0))
        elif pos1 == 0:
            for (utt2, pos2) in curgoldlist:
                if utt1 == utt2:
                    takefromresultlist.append((utt1, pos1))
                    takefromgoldlist.append((utt1, pos2))
                    newintersection.append((utt1, pos2))
                    curgoldlist.remove((utt2, pos2))
                    break
    takefromresultctr = Counter(takefromresultlist)
    takefromgoldctr = Counter(takefromgoldlist)
    newintersectionctr = Counter(newintersection)
    return takefromresultctr, takefromgoldctr, newintersectionctr


def exactcompare(exactresults, exactgoldscores):
    '''
    compares two lists of exact results, i.e. dlists of pairs (uttid, position)
    :param exactresults:
    :param exactgoldscores:
    :return: triple (resultsminusgold, goldminusresults, intereection)
    '''
    resultscounter = Counter(exactresults)
    goldcounter = Counter(exactgoldscores)
    intersection1 = resultscounter & goldcounter
    resultsminusgold1 = resultscounter - goldcounter
    goldminusresults1 = goldcounter - resultscounter

    (resultsminusgold2, goldminusresults2, intersection2) = compareunaligned(
        resultsminusgold1, goldminusresults1)

    intersectionctr = intersection1 + intersection2
    resultsminusgoldctr = resultsminusgold1 - resultsminusgold2
    goldminusresultsctr = goldminusresults1 - goldminusresults2

    intersection = counter2list(intersectionctr)
    resultsminusgold = counter2list(resultsminusgoldctr)
    goldminusresults = counter2list(goldminusresultsctr)

    return (resultsminusgold, goldminusresults, intersection)


def counter2list(ctr):
    result1 = [el for el in ctr for k in range(ctr[el])]
    result = sorted(result1)
    return result


def getusercomments(permdict, rawkey: Tuple[str, ResultsKey, UttId, Position, str], report=False):
    sample, reskey, uttid, pos, moreorless = rawkey
    reskeystr = slash.join(reskey)
    key = sample, reskeystr, uttid, pos, moreorless
    olderkey = (reskey[0], uttid, pos)
    if key in permdict:
        therow = permdict[key]
        usercomments = therow
        result = usercomments
    elif olderkey in permdict:
        therow = permdict[olderkey]
        usercomments = therow
        result = usercomments
    else:
        count = usercommentuntil - usercommentbegin
        resultlist = [usercommentdefaultvalue for _ in range(count)]
        result = resultlist
    return result


def testcompare():
    testresults = [(1, 2), (1, 2), (1, 2), (1, 5), (1, 6), (2, 0), (2, 4)]
    goldresults = [(1, 2), (2, 4), (2, 6), (1, 0), (3, 5)]
    reftestminusgold = [(1, 2), (1, 5), (1, 6)]
    refgoldminustest = [(3, 5)]
    refintersection = [(1, 2), (1, 2), (2, 4), (2, 6)]
    (testminusgold, goldminustest, intersection) = exactcompare(
        testresults, goldresults)
    for (l, r, g) in zip(['R-G', 'G-R', 'R*G'], [testminusgold, goldminustest, intersection],
                         [reftestminusgold, refgoldminustest, refintersection]):
        if r == g:
            print('{}: OK {} == {}'.format(l, r, g))
        else:
            print('{}: NO: {} != {}'.format(l, r, g))


if __name__ == '__main__':
    testcompare()
