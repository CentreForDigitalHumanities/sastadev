"""
The module *update_inflectioncorrection* generates a new version of the file inflectioncorrection.
It reads the file *irregverbfilename* and generates paradigms by using the function *makeparadigm*
"""

from sastadev.deregularise import (correctionfullname, makeparadigm, tab)


# read the irregular verbs

irregverbfilename = r"./data/DutchIrregularVerbs.tsv"
irregverbfile = open(irregverbfilename, 'r', encoding='utf8')

forms = {}
for line in irregverbfile:
    if line[-1] == '\n':
        line = line[:-1]
    row = line.split(tab)
    forms[row[0]] = row

irregverbfile.close()

correction = {}
# initialisatie
for el in forms:
    triples = makeparadigm(el, forms)
    for wrong, meta, good in triples:
        if good != wrong:
            correction[wrong] = good, meta


with open(correctionfullname, 'w', encoding='utf8') as correctionfile:
    for w in correction:
        print(w, correction[w][0], correction[w]
              [1], sep=tab, file=correctionfile)
