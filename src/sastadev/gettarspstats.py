import os
from sastadev.readcsv import readheadedcsv

inputpath1 = './tarspcodes'
inputpath2 = './referencestatistics'


tarsp_predictions1filename = 'tarsppredictions1.txt'
tarsp_predictions1fullname = os.path.join(inputpath1, tarsp_predictions1filename)

header, data = readheadedcsv(tarsp_predictions1fullname)
predictiondict = {}
for i, row in data:
    rawkey = eval(row[0])
    key = tuple((int(x) for x in rawkey))
    listpredictions = eval(row[1])
    dctpredictions = {code: frq for (code, frq) in listpredictions}
    predictiondict[key] = dctpredictions

junk = 0

tarspcodefrqsfilename = 'tarspfrequencies.txt'
tarspcodefrqsfullname = os.path.join(inputpath2, tarspcodefrqsfilename)
header, data = readheadedcsv(tarspcodefrqsfullname)
tarspfrequenciesdict = {}
for i, row in data:
    code = row[0]
    frq = int(row[1])
    tarspfrequenciesdict[code] = frq

junk = 0


