import os
from sastadev.readcsv import readcsv

infilename = 'code_frequencies.tsv.txt'
inpath = './data/code_frequencies'
infullname = os .path.join(inpath, infilename)

code_frequencies = {}
idata = readcsv(infullname)
for _, row in idata:
    qid = row[0]
    frq = row[1]
    code_frequencies[qid] = frq

junk = 0   # for debugging purposes
