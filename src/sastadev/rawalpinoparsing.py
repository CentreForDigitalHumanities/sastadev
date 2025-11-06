import logging
import re
import urllib.parse
import urllib.request

from lxml import etree  # type: ignore

from sastadev.treebankfunctions import showtree

# from memoize import memoize

# from sastatypes import SynTree, URL

# from config import SDLOGGER
# from sastatypes import SynTree, URL

urllibrequestversion = urllib.request.__version__

alpino_special_symbols_pattern = r'[\[\]]'
alpino_special_symbols_re = re.compile(alpino_special_symbols_pattern)

gretelurl = 'https://gretel.hum.uu.nl/api/src/router.php/parse_sentence/'
# gretelurl = 'http://gretel.hum.uu.nl/api/src/router.php/parse_sentence/'
previewurltemplate = 'https://gretel.hum.uu.nl/ng/tree?sent={sent}&xml={xml}'
# previewurltemplate = 'http://gretel.hum.uu.nl/ng/tree?sent={sent}&xml={xml}'

emptypattern = r'^\s*$'
emptyre = re.compile(emptypattern)


def isempty(sent: str) -> bool:
    '''
    The function *isempty* checks whether the input string *sent* is the null string or
    consists of white space only.

    '''
    result = emptyre.match(sent) is not None
    return result


def parse(origsent: str, escape: bool = True):
    '''
    The function *parse* invokes the alpino parser (over the internet, so an internet connection is required) to parse
    the string *origsent*.
    The parameter *escape* can be used to escape symbols that have a special meaning
    for Alpino. Its default value is *True*.

    This function is memoised. In order to avoid unexpected results since the output type is mutable, a deepcopy
    of the result is returned. This is essential, because if the same input string is parsed twice,
    the resulting parse tree objects should really be two different instances.!

    '''
    if isempty(origsent):
        return None
    if escape:
        sent = escape_alpino_input(origsent)
    else:
        sent = origsent
    encodedsent = urllib.parse.quote(sent)
    fullurl = gretelurl + encodedsent
    try:
        r1 = urllib.request.urlopen(fullurl)
    except urllib.request.HTTPError as e:
        logging.error('{}: parsing <{}> failed'.format(e, sent))
        return None
    except urllib.error.URLError as e:
        logging.error('{}: parsing <{}> failed'.format(e, sent))
        return None
    else:
        if 300 > r1.status >= 200:
            streebytes = r1.read()
            # print(streebytes.decode('utf8'))
            stree = etree.fromstring(streebytes)
            return stree
        else:
            logging.error('parsing failed:', r1.status, r1.reason, sent)
            return None

def escape_alpino_input(instr: str) -> str:
    '''
    The function escape_alpino_input takes as input a string *str* and returns this string with symbols with a
    special meaning for Alpino escaped, in particular the square bracket symbols [ and ] used for bracketed input.
    :param instr:
    :return:
    '''
    result = ''
    for c in instr:
        if c == '[':
            newc = '\['
        elif c == ']':
            newc = '\]'
        else:
            newc = c
        result += newc
    return result


def mytest():
    utts = ['[@posflt   verb kom]', 'kom']
    for utt in utts:
        tree = parse(utt, escape=False)
        showtree(tree, 'tree')


if __name__ == '__main__':
    mytest()
