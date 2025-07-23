from sastadev.stringfunctions import dutchdeduplicate, chatxxxcodes
from sastadev.lexicon import known_word
from typing import List


testtriples = [(1, 'nnnog', ['nog']), (2, 'noggg', ['nog']), (3, 'zzzzzijn', ['zijn']), (4, 'nnnnogggg', ['nog']),
             (5, 'staaa', ['sta']), (7, 'haaaalen', ['halen']), (8, 'haaal', ['haal']), (9, 'haaalden', ['haalden'])
             ]


def select(triples, ids: List[int]=None):
    if ids is None:
        selectedtriples = triples
    else:
        selectedtriples = [triple for triple in triples if triple[0] in ids]
    return selectedtriples



def tryme():
    selectedtriples = select(testtriples, ids=None)
    errorfound = False
    for i, selectedword, golds in selectedtriples:
        results = dutchdeduplicate(selectedword, known_word, exceptions=chatxxxcodes)
        sortedresults = sorted(results)
        sortedgolds = sorted(golds)
        if sortedresults != sortedgolds:
            print(f'NO:{str(i)}: {str(sortedresults)} != {str(sortedgolds)}')
            errorfound = True



if __name__ == '__main__':
    tryme()

