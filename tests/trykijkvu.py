from sastadev.conf import settings
from sastadev.tblex import tarsp_kijkvu
from sastadev.treebankfunctions import find1

sentences = ['kijk , een boek']


def tryme():
    for sentence in sentences:
        tree = settings.PARSE_FUNC(sentence)
        kijknode = find1(tree, """.//node[@word="kijk"]""")
        if kijknode is not None:
            result = tarsp_kijkvu(kijknode)
        else:
            result = False
            print(f'No kijk found in {sentence}')
        print(sentence, result)



if __name__ == '__main__':
    tryme()