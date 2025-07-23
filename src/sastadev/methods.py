import os
from typing import Callable, Dict, List, Optional, Tuple

from sastadev.allresults import mkresultskey
from sastadev.conf import settings
from sastadev.query import pre_process
from sastadev.sastatypes import (AltCodeDict, ExactResult, ExactResultsDict,
                                 ExactResultsFilter, FileName,
                                 Item_Level2QIdDict, Level, MethodName,
                                 Pattern, QId, Query, QueryDict)
from sastadev.stringfunctions import str2list

lemmaqid = 'A051'
lexreskey = mkresultskey('A018')
nreskey = mkresultskey('A021')

asta = 'asta'
stap = 'stap'
tarsp = 'tarsp'

tarspmethods = [tarsp]
astamethods = [asta]
stapmethods = [stap]

validmethods = astamethods + stapmethods + tarspmethods

astalexicalmeasures = [mkresultskey('A018'), mkresultskey('A021')]  # LEX and N

basicpattern: Pattern = '[,;]'
extendedpattern: Pattern = '[,;/\|]'

methodseparators = {}
methodseparators[tarsp] = basicpattern
methodseparators[stap] = extendedpattern
methodseparators[asta] = extendedpattern

tarsp2005 = 'tarsp2005'
tarsp2017 = 'tarsp2017'
tarspauris = 'tarspauris'
astae = 'astae'
astafuture = 'astafuture'


class SampleSize:
    def __init__(self, maxuttcount=None, maxwordcount=None):
        self.maxuttcount: Optional[int] = maxuttcount
        self.maxwordcount: Optional[int] = maxwordcount


def validmethod(rawmethod: str) -> bool:
    method = rawmethod.lower()
    result = method in validmethods
    return result


def allok(query: Query, xs: ExactResultsDict, x: ExactResult) -> bool:
    return True




class Method:
    '''

    The *Method* class has the following properties and methods:

* name : MethodName: name of the method
* queries : QueryDict = queries: a dictionary containing the queries (key is query id)
* item2idmap : Item_Level2QIdDict. Dictionary that maps an (item, level) tuple to the QueryId
* altcodes: AltCodeDict: dictionary with alternative codes and their mapping to the standard code
* postquerylist : List[QId]: list of query id’s for queries that are post or form queries
* methodfilename: FileName: filename of the file that contains the language measures
* defaultfilter: ExactResultsFilter: name of the function that acts as the default filter to regulate interaction between prequeries and core queries. By default it has the value allok


    '''

    def __init__(self, name: MethodName, queries: QueryDict, item2idmap: Item_Level2QIdDict,
                 altcodes: AltCodeDict, postquerylist: List[QId], methodfilename: FileName,
                 defaultfilter: ExactResultsFilter = allok):
        self.name: MethodName = name
        self.queries: QueryDict = queries
        self.defaultfilter: ExactResultsFilter = defaultfilter
        self.item2idmap: Item_Level2QIdDict = item2idmap
        self.simpleitem2idmap = {item: id for (
            (item, level), id) in item2idmap.items()}
        self.altcodes: AltCodeDict = altcodes
        self.simplealtcodedict = {alt[0]: code[0] for (alt, code) in self.altcodes.items()}
        self.postquerylist: List[QId] = postquerylist
        self.methodfilename: FileName = methodfilename
        self.separators: Pattern = methodseparators[name]


def implies(a: bool, b: bool) -> bool:
    return (not a) or b


def astalemmafilter(query: Query, xrs: ExactResultsDict, xr: ExactResult) -> bool:
    for (qid, val) in xrs:
        if qid == lemmaqid:
            if xr in xrs[(qid, val)]:
                result1 = (lexreskey in xrs and xr in xrs[lexreskey]) or (nreskey in xrs and xr in xrs[nreskey])
                result = query.process == pre_process or result1
                return result

    return True



# filter specifies what passes the filter
def astadefaultfilter(query: Query, xrs: ExactResultsDict, xr: ExactResult) -> bool:
    a029 = mkresultskey('A029')
    a045 = mkresultskey('A045')
    result1 = query.process == pre_process
    result2 = xr not in xrs[a029] if a029 in xrs else True
    result3 = xr not in xrs[a045] if a045 in xrs else True
    result = result1 or (result2 and result3)
    return result


def getmethodfromfile(filename: str) -> str:
    result = ''
    path, base = os.path.split(filename.lower())
    for m in supported_methods:
        if m in base:
            result = m
    if result == '':
        settings.LOGGER.error('No supported method found in filename')
        exit(-1)
    else:
        return result


def treatmethod(methodname: Optional[MethodName], methodfilename: Optional[FileName]) -> Tuple[MethodName, FileName]:
    if methodname is None and methodfilename is None:
        settings.LOGGER.error('Specify a method using -m ')
        exit(-1)
    elif methodname is None and methodfilename is not None:
        resultmethodfilename = methodfilename
        resultmethodname = getmethodfromfile(methodfilename)
        settings.LOGGER.info(
            'Method derived from the method file name: {}'.format(resultmethodname))
    elif methodname is not None and methodfilename is None:
        if methodname.lower() in supported_methods:
            resultmethodname = methodname.lower()
            resultmethodfilename = supported_methods[methodname]
        else:
            resultmethodfilename = methodname
            resultmethodname = getmethodfromfile(methodname)
            settings.LOGGER.info(
                'Method derived from the method file name: {}'.format(resultmethodname))
    elif methodname is not None and methodfilename is not None:
        if methodname.lower() in supported_methods:
            resultmethodname = methodname.lower()
            resultmethodfilename = methodfilename
        else:
            settings.LOGGER.error(
                'Unsupported method specified {}'.format(methodname))
            exit(-1)
    return resultmethodname, resultmethodfilename



codepath = os.path.dirname(os.path.abspath(__file__))
datapath = os.path.join(codepath, 'data')
methodspath = os.path.join(datapath, 'methods')

supported_methods = {}
supported_methods[tarsp] = os.path.join(
    methodspath, 'TARSP_Index_Current.xlsx')
supported_methods[asta] = os.path.join(methodspath, 'ASTA_Index_Current.xlsx')
supported_methods[stap] = os.path.join(methodspath, 'STAP_Index_Current.xlsx')


codepath = os.path.dirname(os.path.abspath(__file__))
datapath = os.path.join(codepath, 'data')
methodspath = os.path.join(datapath, 'methods')

# supported_methods = {}
# supported_methods[tarsp] = os.path.join(
#     methodspath, 'TARSP_Index_Current.xlsx')
# supported_methods[asta] = os.path.join(methodspath, 'ASTA_Index_Current.xlsx')
# supported_methods[stap] = os.path.join(methodspath, 'STAP_Index_Current.xlsx')

defaultfilters: Dict[MethodName, ExactResultsFilter] = {}
defaultfilters[asta] = astadefaultfilter
defaultfilters[tarsp] = allok
defaultfilters[stap] = allok

maxsamplesize: Dict[MethodName, SampleSize] = {}
maxsamplesize[asta] = SampleSize(maxwordcount=300)
# reset when utterance selection is automated
maxsamplesize[tarsp] = SampleSize(maxuttcount=100)
# reset when utterance selection is automated
maxsamplesize[stap] = SampleSize(maxuttcount=100)

lastuttqidcondition: Dict[MethodName, Callable] = {}
lastuttqidcondition[asta] = lambda q: q in astalexicalmeasures
lastuttqidcondition[tarsp] = lambda q: True
lastuttqidcondition[stap] = lambda q: True




