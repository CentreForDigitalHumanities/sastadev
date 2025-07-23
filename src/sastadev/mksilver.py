from collections import Counter, defaultdict
from math import isnan

from sastadev import readcsv
from sastadev.conf import settings
from sastadev.counterfunctions import counter2liststr
from sastadev.xlsx import getxlsxdata, mkworkbook


def getsilverannotations(perm_silverfullname, platinumcheckeditedfullname,
                         platinumcheckfullname, silvercheckfullname,
                         platinumfullname, platinumeditedfullname, goldscores):

    # -lees perm_silverfulldata in, voeg toe aan perm_silverfulldatadict
    perm_silverfulldatadict = dict()
    perm_silverfulldatadict, perm_header = updatepermdict(perm_silverfullname, perm_silverfulldatadict)

    # lees platinumcheckeditedfilename in, voeg toe aan perm_silverfulldatadict
    perm_silverfulldatadict, silverheader = updatepermdict(platinumcheckeditedfullname, perm_silverfulldatadict)

    #-lees platinmumcheck in, voeg toe aan perm_silverfulldatadict
    perm_silverfulldatadict, silverheader = updatepermdict(platinumcheckfullname, perm_silverfulldatadict)

    #-schrijf de prem_silverfulldatadict weg naar een nieuwe perm_silverfilename
    write2excel(perm_silverfulldatadict, silverheader, perm_silverfullname)

    #maak de silver file (platinum)--zie functie mksilver maar herschreven want je hebt de files al gelezen
    #@@
    mksilver(perm_silverfulldatadict, silvercheckfullname, platinumfullname, platinumeditedfullname, goldscores)

    #loop alle entries af in  platinumcheck, indien in perm_silverfulldatadict, [User 1-3] + entry{3:]
    # print dit naar de platinumcheckfile@@
    # of return de perm_silverfulldatadict hier en doe bovenstaande in de main loop waar je de file nu al uitschrijft
    return perm_silverfulldatadict






def mksilver(permsilverdict, silvercheckfullname, platinumfullname, platinumeditedfullname, goldscores):

    # read the silvercheckfile
    silverheader, silvercheckdata = getxlsxdata(silvercheckfullname)

    # determine which uttids have to be removed
    undecidedcounter = 0
    toremove = defaultdict(list)
    maxrow = len(silvercheckdata)
    for row in range(maxrow):
        currow = silvercheckdata[row]
        moreorless = currow[moreorlesscol]
        if moreorless not in legalmoreorlesses:
            settings.LOGGER.error('Unexpected value in row {}: {}. File {}'.format(row, moreorless, silvercheckfullname))
        if moreorless == 'Missed examples':
            continue
        qid = currow[qidcol]
        uttid = str(currow[uttidcol])
        pos = currow[poscol]
        if (qid, uttid, pos) in permsilverdict:
            curpermrow = permsilverdict[(qid, uttid, pos)]
            (user1, user2, user3) = curpermrow[user1col], curpermrow[user2col], curpermrow[user3col]
            cleanuser1 = clean(user1)
            if cleanuser1 not in allowedoknots:
                settings.LOGGER.error('Unexpected value in row {}: {}. File {}'.format(row, user1, silvercheckfullname))
            if cleanuser1 not in oks:
                toremove[qid].append(uttid)
            if cleanuser1 in undecideds:
                undecidedcounter += 1
        else:
            pass
            #settings.LOGGER.warning('No Silver remark for row {}: {}. File {}; qid={}, uttid={}, pos={}'.format(row, moreorless, silvercheckfullname, qid, uttid, pos))

    if undecidedcounter > 0:
        settings.LOGGER.info('{} undecided in file {}'.format(undecidedcounter, silvercheckfullname))
    # read the platinumfile
    (header, platinumdata) = readcsv.readheadedcsv(platinumfullname)
    newrows = []
    for (rowctr, row) in platinumdata:
        theqid = row[0]
        if theqid in toremove:
            toremoveids = [str(x) for x in toremove[theqid]]
            olduttids_string = row[uttidscol]
            rawolduttids = olduttids_string.split(comma)
            olduttids = [clean(x) for x in rawolduttids]
            toremoveCounter = Counter(toremoveids)
            olduttsCounter = Counter(olduttids)
            goldcounter = goldscores[theqid][2] if theqid in goldscores else Counter()
            newCounter = (olduttsCounter - toremoveCounter) | goldcounter  # all gold results must stay in
            newuttids_string = counter2liststr(newCounter)
            #newuttids_string = listminus(olduttids, toremoveids)
            newrow = row[:4] + [newuttids_string] + row[uttidscol + 1:]
        else:
            newrow = row
        newrows.append(newrow)

    # write the results to a new edited platinumfile

    readcsv.writecsv(newrows, platinumeditedfullname, header=header)
