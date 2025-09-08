

space = ' '


class Token:
    def __init__(self, word, pos, skip=False, subpos=0):
        self.word = word
        self.pos = pos
        self.subpos = subpos
        self.skip = skip

    def __repr__(self):
        fmtstr = 'Token(word={},pos={}, skip={}, subpos={})'
        result = fmtstr.format(repr(self.word), repr(
            self.pos), repr(self.skip), repr(self.subpos))
        return result

    def __str__(self):
        skipstr = ' (skip=True)' if self.skip else ''
        subposstr = '/{}'.format(self.subpos) if self.subpos != 0 else ''
        result = '{}{}:{}{}'.format(self.pos, subposstr, self.word, skipstr)
        return result


def oldstringlist2tokenlist(list):
    result = []
    llist = len(list)
    for el in range(llist):
        thetoken = Token(list[el], el)
        result.append(thetoken)
    return result


def stringlist2tokenlist(list, start=0, inc=1):
    result = []
    llist = len(list)
    pos = start
    for el in range(llist):
        thetoken = Token(list[el], pos)
        result.append(thetoken)
        pos += inc
    return result


def tokenlist2stringlist(tlist, skip=False):
    if skip:
        result = [t.word for t in tlist if not t.skip]
    else:
        result = [t.word for t in tlist]
    return result


def tokenlist2string(tlist):
    wordlist = [t.word for t in tlist]
    result = space.join(wordlist)
    return result


def show(tokenlist):
    resultlist = []
    for token in tokenlist:
        resultlist.append(str(token))
    result = ', '.join(resultlist)
    return result


def tokeninflate(token):
    result = inflate(token.pos) + token.subpos
    return result


def deflate(n: int):
    result = (n // 10) - 1
    return result


def inflate(n: int):
    result = (n + 1) * 10
    return result


def insertinflate(n: int):
    dm = n % 10
    result = ((n - dm) + 1) * 10 + dm
    return result

def mktokenlist(tokens, fpos, inserttokens):
    resultlist = [token for token in tokens if token.pos <= fpos] + \
        inserttokens + \
                 [token for token in tokens if token.pos > fpos]
    return resultlist