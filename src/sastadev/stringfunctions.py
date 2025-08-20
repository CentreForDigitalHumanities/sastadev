import re
import unicodedata
from collections import Counter
from typing import Any, Callable, List, Match, Optional, Sequence, Set

vertbar = '|'
space = ' '
hyphen = '-'
slash = '/'
tab = '\t'
comma = ','
underscore = '_'

punctuationchars = """`!()-{}[]:;"'<>,.“?"""  # should actually use unicode categories

# for selecting nonempty tokens from a csvstring ; comma between single quotes is allowed
csvre = "'[^']+'|[^,' ]+"
csvpat = re.compile(csvre)

wpat = r'^.*\w.*$'
wre = re.compile(wpat)
allhyphenspat = r'^-+$'
allhyphensre = re.compile(allhyphenspat)

barevowels = 'aeiouy'
aiguvowels = 'áéíóúý'
gravevowels = 'àèìòù\u00FD'
tremavowels = 'äëïöüÿ'
circumflexvowels = 'âêîôû\u0177'


digits = '0123456789'
consonants = 'bcdfghjklmnpqrstvwxz\u00E7'  # \u00E7 is c cedilla
dutch_base_vowels = barevowels + aiguvowels + \
                    gravevowels + tremavowels + circumflexvowels
vowels = dutch_base_vowels
dutch_base_diphthongs = ['aa', 'ee', 'ie', 'oo',
                         'uu', 'ij', 'ei', 'au', 'ou', 'ui', 'eu', 'oe']
dutch_y_diphthongs = ['y' + d for d in dutch_base_vowels] + [d + 'y' for d in
                                                             dutch_base_vowels]  # ryen gaat nog fout ye alleen samen nemen aan begin van woord
dutch_y_triphthongs = ['y' + d for d in dutch_base_diphthongs] + \
                      [d + 'y' for d in dutch_base_diphthongs]
dutch_trema_diphthongs = ['äa', "ëe", 'ïe', 'öo', 'üu', 'ëi']
dutch_diphthongs = dutch_base_diphthongs + \
                   dutch_y_diphthongs + dutch_trema_diphthongs
dutch_base_triphthongs = ['aai', 'eeu', 'ooi', 'oei']
dutch_y_tetraphthongs = ['y' + d for d in dutch_base_triphthongs]
dutch_triphthongs = dutch_base_triphthongs + dutch_y_triphthongs
dutch_tetraphthongs = dutch_y_tetraphthongs
foreign_triphthongs = ['eau', 'oeu']

hyphenprefixes = ['anti', 'contra', 'ex']

singlehyphenpat = r'(^[^-]+)-([^-]+)$'
singlehyphenre = re.compile(singlehyphenpat)

duppattern = r'(.)\1+'
dupre = re.compile(duppattern)

purechatxxxcodes = {'xxx', 'yyy', 'www'}
chatxxxcodes = purechatxxxcodes | {'xx'}


sentencefinalpuncs = '.?!'

def simple_tokenise(sent: str) -> List[str]:
    """
    simple tokenisation. Interpunction symbols are surrounded by space, then split by space
    :param sent: input string
    :return: list of strings that make up the tokens of the input sentence
    """

    cleansent = ''
    for c in sent:
        if c in punctuationchars:
            cleansent += f' {c} '
        else:
            cleansent += c
    tokens = cleansent.split()
    return tokens

def str2list(instr: str, sep=comma) -> List[str]:
    if instr == '':
        return []
    rawlist = instr.split(sep)
    cleanlist = [el.strip() for el in rawlist]
    return cleanlist

def pad(wrd: str, i: int, c: str = space) -> str:
    '''
    returns a right-justified string lengthened to length i and padded  with c
    '''
    if len(wrd) > i:
        result = wrd
    else:
        result = wrd.rjust(i, c)
    return result


def star(str: str) -> str:
    '''
    The function *star* takes a string str and returns it preceded by ( and followed by )*. Used to create
    regular expressions.
    '''
    return '({})*'.format(str)

def ispunctuation(wrd: str) -> bool:
    result = wrd in punctuationchars
    return result

def alt(strlist: Sequence[str], grouped: bool = True) -> str:
    '''
    The function alt takes as input a string or a list of strings and joins them into  a string separated by |.
    If grouped is True the resulting string is surrounded by round brackets, else not. Used to create regular expressions
    '''
    alts = '|'.join(strlist)
    if grouped:
        result = '({})'.format(alts)
    else:
        result = '{}'.format(alts)
    return result


def charrange(string: str) -> str:
    '''
    The function charrange take string str and surrounds it with square bracketys []. used to create regular expressions.
    '''
    return '[{}]'.format(string)


consonants_star = star(charrange(consonants))

syllableheadspat = alt(dutch_tetraphthongs + dutch_triphthongs + dutch_diphthongs + [v for v in vowels])
syllableheadsre = re.compile(syllableheadspat)

monosyllabicpat = r'^' + consonants_star + \
                  syllableheadspat + consonants_star + r'$'
monosyllabicre = re.compile(monosyllabicpat)

wordinitialrepeatedconsonants = fr'^({charrange(consonants)})\1+'
wordfinalalrepeatedconsonants = fr'({charrange(consonants)})\1+$'
wordinitialrepeatedconsonantsre = re.compile(wordinitialrepeatedconsonants)
wordfinalalrepeatedconsonantsre = re.compile(wordfinalalrepeatedconsonants)
intervowelrepeatedconsonants = fr'{syllableheadspat}({charrange(consonants)})\2+{syllableheadspat}'
intervowelrepeatedconsonantsre = re.compile(intervowelrepeatedconsonants)

repeatedvowelsinopensyllable = rf'([{vowels}])\1+($|{charrange(consonants)}[{vowels}])'
repeatedvowelsinopensyllablere = re.compile(repeatedvowelsinopensyllable)

repeatedvowelsinclosedsyllable = rf'([{vowels}])\1+({charrange(consonants)})($|{charrange(consonants)})'
repeatedvowelsinclosedsyllablere = re.compile(repeatedvowelsinclosedsyllable)

def dutchdeduplicate(word: str, inlexicon: Callable[[str], bool], exceptions: Set[str]) -> List[str]:
    results = []
    if word in exceptions:
        return results
    newword = word

    # repeated consonants at the beginning reduce to a single consonant
    newword2 = wordinitialrepeatedconsonantsre.sub(r'\1', newword)
    if newword2 != newword and inlexicon(newword2):
        results.append(newword2)

    # repeated consonants at the end reduce to a single consonant
    newword3 = wordfinalalrepeatedconsonantsre.sub(r'\1', newword2)
    if newword3 != newword2 and inlexicon(newword3):
        results.append(newword3)

    # repeated consonants between vowels reduce to two consonants
    newword4 = intervowelrepeatedconsonantsre.sub(r'\1\2\2\3', newword3)
    if newword4 != newword3 and inlexicon(newword4):
        results.append(newword4)

    # repeated vowels reduce to one if in an open syllable
    newword5 = repeatedvowelsinopensyllablere.sub(r'\1\2', newword4)
    if newword5 != newword4 and inlexicon(newword5):
        results.append(newword5)

    # repeated vowels reduce to two vowels if in a closed syllable
    newword6 = repeatedvowelsinclosedsyllablere.sub(r'\1\1\2\3', newword5)
    if newword6 != newword5 and inlexicon(newword6):
        results.append(newword6)

    return results

def barededup(word: str) -> str:
    '''
    The function barededup takes as input a string and
    returns a string in which  sequences of the same character are reduced to a single instance of this character
    and other characters are left unchanged. Example: 'vver' -> 'ver'
    '''
    result = dupre.sub(r'\1', word)
    return result


def deduplicate(word: str, inlexicon: Callable[[str], bool], exceptions: Set[str] = set(), reduce21: bool=True ) -> List[str]:
    '''
    The function deduplicate takes as input a string word:

    * if it contains a sequence of duplicate characters, and
    * if it is not just a sequence of interpunction symbols, and
    * if it is not contained in the set of exceptions

    then

    * it checks whether the string with  the character sequence reduced to two characters is a word
    according to the function *inlexicon*,
        * if so,  it adds this string to the result variable *newwords*
        * else it checks whether the string with  the character sequence reduced to one character is a word
    according to the function *inlexicon*, and if so,  it adds this string to the result variable *newwords*

    and then it returns the value of the result variable *newwords*
    '''
    newwords: List[str] = []
    if word in exceptions:
        newwords = []
    # we want to exclude tokens consisting of interpunction symbols only e.g  ---, --
    elif wre.match(word):
        newword = dupre.sub(r'\1\1', word)
        if inlexicon(newword):
            newwords.append(newword)
        elif reduce21:
            newword = dupre.sub(r'\1', word)
            if inlexicon(newword):
                newwords.append(newword)
    return newwords


def fullworddehyphenate(word: str, inlexicon: Callable[[str], bool]) -> List[str]:
    '''
    The function fullworddehyphenate takes as input a string *word*:

    Its purpose is to remove unnecessary hyphens from this word.

    * the hyphen can be a part of the word (*sergeant-majoor*), in which case it should not be removed.
    * it can also have been added to an existing word without hyphens (zie-ken-huis), in which case, it should be removed

    * it can also separate a possibly mispronounced prefix repetition of the prefix of word (e.g., ver-verkoopt or vver-verkoopt), in which case the hyphen and the prefix should be removed.


    To that end,

    * it applies the function *dehyphenate* to *word*. If this yields a result that is an existing word according to the function *inlexicon*, then this result is added to the result variable *newtokens*

    * if newtokens is still the empty list after this, it applies the function *delhyphenprefix* to word.  If this yields a result that is an existing word according to the function *inlexicon*, then this result is added to the result variable *newtokens*.

    and then it returns the result variable newtokens.

    The functions *dehyphenate* and *delhyphenprefix* are described here:

    * .. autofunction:: sastadev.stringfunctions::dehyphenate
    * .. autofunction:: sastadev.stringfunctions::delhyphenprefix


    '''
    newtokens = []
    newwords = dehyphenate(word)
    newwordset = set(newwords)
    for newword in newwordset:
        if inlexicon(newword):
            newtokens.append(newword)
    if newtokens == []:
        newwords = delhyphenprefix(word, inlexicon)
        newwordset = set(newwords)
        for newword in newwordset:
            newtokens.append(newword)
    return newtokens


def delhyphenprefix(word: str, inlexicon: Callable[[str], bool]) -> List[str]:
    '''
    The function *delphyphenprefix* takes as input a string *word*, splits it into a prefix and a mainword
    based on the first occurring hyphen, and  then:

    * if the prefix is a prefix that normally occurs with a hyphen and the mainword is an existing word according to the function *inlexicon* (e.g. *ex-vrouw*), the result variable is set to the empty list;
    * if the mainwords starts with the prefix and the main word is an existing word according to the function *inlexicon* (e.g. *ver-verkoop*),  then the result variable is set to [mainword];
    * if the prefix and the mainword are both existing words, the result variable is set to [];
    * if the mainwords starts with barededeup(prefix) and the main word is an existing word according to the function *inlexicon* (e.g. *vver-verkoop*),  then the result variable is set to [mainword]

     and then it returns the value of the result variable *result*.

    '''
    m = singlehyphenre.match(word)
    if m is not None:
        prefix = m.group(1)
        mainword = m.group(2)
        mwinlex = inlexicon(mainword)
        pfinlex = inlexicon(prefix)
        deduppf = barededup(prefix)
        # the word starts wit ha known prefix that uses hyphen such as ex (ex-vrouw)
        if prefix in hyphenprefixes and mwinlex:
            result = []
        # this is the core case  e.g. ver-verkoop
        elif mainword.startswith(prefix) and mwinlex:
            result = [mainword]
        # for compounds with a hyphen: kat-oorbellen, generaal-majoor and for tennis-baan(?)
        elif pfinlex and mwinlex:
            result = []
        elif mainword.startswith(deduppf) and mwinlex:  # vver-verkoop
            result = [mainword]
        else:
            result = []
    else:
        result = []
    return result


def allhyphens(word: str) -> Optional[Match]:
    '''
    The function allhyphens checks whether the string word consist completely of hyphens
    '''
    result = allhyphensre.match(word)
    return result


def dehyphenate(word: str) -> List[str]:
    '''
    The function dehyphenate takes as input a string and returns  a list of strings with all possible ways
    of removing hyphens in this string
    Examples:

    * dehyphenate('zie-ken-huis') = ['zie-ken-huis', 'zieken-huis', 'zie-kenhuis', 'ziekenhuis']
    * dehyphenate('ziekenhuis') = ['ziekenhuis']
    * dehyphenate('---') = ['---']  (a string consisting only of hyphens remains unchanged

    '''
    results = []
    if len(word) == 0:
        results = ['']
    elif allhyphens(word):
        results = [word]
    else:
        head = word[0:1]
        tail = word[1:]
        if head == hyphen:
            # newresult = head + tail
            # results.append(newresult)
            rightresults = dehyphenate(tail)
            for rightresult in rightresults:
                newresult = head + rightresult
                results.append(newresult)
                newresult = rightresult
                results.append(newresult)
        else:
            tailresults = dehyphenate(tail)
            for tailresult in tailresults:
                newresult = head + tailresult
                results.append(newresult)
    return results


def isconsonant(char: str) -> bool:
    '''
    The function isconsonant checks whether the input string char is a consonant.
    '''
    if len(char) != 1:
        result = False
    elif char.lower() in consonants:
        result = True
    else:
        result = False
    return result


def isvowel(char: str) -> bool:
    '''
    The function isvowel checks whether the input string char is a vowel.
    '''
    if len(char) != 1:
        result = False
    elif char.lower() in vowels:
        result = True
    else:
        result = False
    return result


def endsinschwa(word: str) -> bool:
    '''
    The function endinschwa checks whether the string word ends in schwa.
    '''
    # Ce of Vie of ije or ë
    if word[-3:] == 'ije':
        result = True
    elif word[-2:] == 'ie' and isvowel(word[-3:-2]):
        result = True
    elif word[-1:] == "ë":
        result = True
    elif word[-1:] == 'e' and isconsonant(word[-2:-1]):
        result = True
    else:
        result = False
    return result


def isdiphthong(d: str) -> bool:
    '''
    The function isdiphthong checks whether the string d is a diphtong in Dutch.
    '''
    result = d in dutch_diphthongs
    return result


def istriphthong(d: str) -> bool:
    '''
    The function istriphthong checks whether the string d is a triphtong in Dutch.
    '''
    result = d in dutch_triphthongs
    return result


def monosyllabic(word: str) -> bool:
    '''
    The function monosyllabic checks whether the string word cosnist of one syllable.
    '''
    result = monosyllabicre.match(word) is not None
    return result


def accentaigu(word: str) -> List[str]:
    '''
    The function accentaigu turns all vowels of a word into their varinats with an accent aigu, in all possible combinations.
    Example: accentaigu('aap') == ['aap', 'aáp', 'áap', 'ááp']
    '''
    if len(word) == 0:
        results = ['']
    elif isvowel(word[0]):
        restresults = accentaigu(word[1:])
        results1 = [word[0] + wrest for wrest in restresults]
        results2 = [aigu(word[0]) + wrest for wrest in restresults]
        results = results1 + results2
    else:
        restresults = accentaigu(word[1:])
        results = [word[0] + wrest for wrest in restresults]
    return results


def aigu(c: str) -> str:
    '''
    The function aigu turns the string c into a variant with an accent aigu.
    Only useful for single character strings taht are contained in barevowels
    :param c:
    :return:
    '''
    theindex = barevowels.find(c)
    result = aiguvowels[theindex]
    return result


def testcondition(condition, word):
    if condition(word):
        print('OK:{}'.format(word))
    else:
        print('NO:{}'.format(word))


def test():
    monosyllabicwords = ['baai', 'eeuw', 'mooi', 'aap', 'deed', 'Piet', 'noot', 'duut', 'rijd', 'meid', 'rauw', 'koud',
                         'buit', 'reuk', 'boer', 'la', 'de', 'hik', 'dop', 'dut',
                         'yell', 'ry', 'Händl', 'Pëtr', 'bït', 'Köln', 'Kür', 'Tÿd']
    disyllabicwords = ['baaien', 'eeuwen', 'mooie', 'aapje', 'deden', 'Pietje', 'noten', 'dut', 'rijden', 'meiden',
                       'rauwe', 'koude', 'buitje', 'reuken', 'boeren', 'laden', 'dender',
                       'hikken', 'doppen', 'dutten', 'yellen', 'ryen', 'Händler', 'Pëtri', 'bïty', 'Kölner', 'Kürer',
                       'Tÿding', 'naäap', 'meeëten', 'ciën', 'coöp']

    for word in monosyllabicwords:
        testcondition(monosyllabic, word.lower())
    for word in disyllabicwords:
        testcondition(monosyllabic, word.lower())

    for word in monosyllabicwords + disyllabicwords:
        ms = syllableheadsre.finditer(word)
        print(word, end=' -- ')
        for m in ms:
            print(m.group(0), end=', ')
        print('')


def nono(inval: Any) -> bool:
    result = (inval is None) or (inval == 0) or (inval == []) or (inval == '')
    return result


def nonnull(inval: Any) -> bool:
    result = not (nono(inval))
    return result


def allconsonants(inval: str) -> bool:
    '''
    The function allconsonants checks whether all characters in the string inval are consonants
    '''
    result = all([isconsonant(c) for c in inval])
    return result


def string2list(liststr: str, quoteignore=False) -> List[str]:
    '''
    The function string2list turns a string surrounded by [ ] into a list by splitting it on a comma
    Examples:
    * "[1,2,3]" becomes ['1', '2', '3']
    * "[]" becomes []
    * "[ ]" becomes [" "]
    * "['Jan', 'Piet']" becomes ["'Jan'", "'Piet'"] if quoteignore = False
    * "['Jan', 'Piet']" becomes ['Jan', 'Piet'] if quoteignore = True
    * comma's between single quotes are allowed

    '''
    if liststr is None or len(liststr) == 2:
        return []
    elif liststr[0] == '[' and liststr[-1] == ']':
        core = liststr[1:-1]
        parts = csvpat.findall(core)
        strippedparts = [part.strip() for part in parts]
        if quoteignore:
            cleanparts1 = [part.strip("'") for part in strippedparts]
            cleanparts = [part.strip('"') for part in cleanparts1]
        else:
            cleanparts = strippedparts
        return cleanparts
    else:
        return []


def realwordstring(w: str) -> bool:
    '''
    The function *realwordstring* checks whether the string w @@ to be extended@@

    '''
    if len(w) != 1:
        result = True
    else:
        result = not unicodedata.category(w).startswith('P')
    return result

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
def getallrealwords(allresults):
    result = {}
    for uttid in allresults.allutts:
        words = [w for w in allresults.allutts[uttid] if realwordstring(w)]
        result[uttid] = Counter(words)
    return result

def remove_underscore(lemma: str) -> str:
    lemmaparts = lemma.split(underscore)
    newlemma = ''.join(lemmaparts)
    return newlemma

def normalise_word(wrd: str) -> str:
    cleanwrd = wrd.lower()
    cleanwrd = strip_accents(cleanwrd)
    return cleanwrd

def lpad(id: str, size:int = 3, sym: str= '0') -> str:
    lid = len(id)
    if lid > size:
        properid = id
        # issue a warning
    else:
        properid = (size - lid) * sym + id
    return properid


if __name__ == '__main__':
    test()
