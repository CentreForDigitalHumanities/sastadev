import re
from typing import List

from lxml import etree
from sastadev.correctionlabels import repeatedword
from sastadev.sastatypes import Penalty

bpl_none, bpl_word, bpl_node, bpl_delete, bpl_indeze, bpl_extra_grammatical, bpl_wordlemma, \
bpl_cond, bpl_replacement, bpl_word_delprec, bpl_node_nolemma = tuple(range(11))
defaultpenalty = 100
defaultbackplacement = bpl_none

SASTA = 'SASTA'
ADULTSPELLINGCORRECTION = 'AdultSpellingCorrection'
ALLSAMPLECORRECTIONS = 'AllSampleCorrections'
BASICREPLACEMENTS = 'BasicReplacements'
CHILDRENSPELLINGCORRECTION = 'ChildrenSpellingCorrection'
CONTEXT = 'Context'
HISTORY = 'History'
THISSAMPLECORRECTIONS = 'ThisSampleCorrections'


EXTRAGRAMMATICAL = 'ExtraGrammatical'

replacementsubsources = [ ADULTSPELLINGCORRECTION, ALLSAMPLECORRECTIONS, BASICREPLACEMENTS,
                             CHILDRENSPELLINGCORRECTION , CONTEXT, HISTORY, THISSAMPLECORRECTIONS
                           ]

space = ' '
metakw = '##META'

xmlformat = '''
<xmeta name="{name}" type="{atype}" value= "{value}" annotationwordlist="{annotationwordlist}"
       annotationposlist="{annotationposlist}" annotatedwordlist="{annotatedwordlist}"
       annotatedposlist="{annotatedposlist}"  cat="{cat}" subcat="{subcat}" source="{source}"
       backplacement="{backplacement}" penalty="{penalty}"
/>'''

# MetaValue class for simple PaQu style metadata copied from chamd


class MetaValue:
    def __init__(self, el, value_type, text):
        self.value_type = value_type
        self.text = text
        self.uel = despace(el)

    def __str__(self):
        return space.join([metakw, self.value_type, self.uel, "=", self.text])

    def toElement(self):
        meta = etree.Element('meta')
        meta.set('name', self.uel)
        meta.set('type', self.value_type)
        meta.set('value', self.text)
        return meta


def fromElement(xmlel):
    value_type = xmlel.attrib['type']
    text = xmlel.attrib['value']
    uel = xmlel.attrib['name']
    result = MetaValue(uel, value_type, text)
    return result


# copied from chamd
def despace(str):
    # remove leading and trailing spaces
    # replace other sequences of spaces by underscore
    result = str.strip()
    result = re.sub(r' +', r'_', result)
    return result


class Meta:
    """
    The class *Meta* defines a class for storing metadata. It has more attributes than the Alpino metadata,
    for which a class named MetaValue gas been created. The class *Meta* can accommodate all objects of class
    "MetaValue", though this is currently not exploited.

    The attributes of this class are:

    * atype: this is present for compatibility with the Alpino metadata, which have a type attribute
    * name: a name of the metadata element, usually a name for the phenomenon it describes
    * annotationwordlist: the list of words that form the annotation
    * annotationposlist: the list of positions of the words that form the annotation
    * annotatedwordlist: the list of words that are annotated
    * annotatedposlist: the list of positions of the words that are annotated
    * annotationcharlist: the list of characters that form the annotation (for annotations within  a word)
    * annotationcharposlist: the list of positions of the characters that form the annotation (for annotations within  a word)
    * annotatedcharlist =  the list of characters that are annotated (for annotations within  a word)
    * annotatedcharposlist: the list of positions of the characters that are annotated (for annotations within  a word)
    * value: present for compatibility with the Alpino metadata. It usually gets the same value as the
    annotationwordlist
    * cat: a label to specify a category that the metadata belongs to
    * subcat: a label to specify a subcategory that the metadata belongs to
    * source: a label to specify the source of the metadata, e.g. CHAT, SASTA/BasicReplacements, etc.
    * penalty: an integer value to specify the costs of the change that created the metadata
    * backplacement: integer value. if the metadata describes a replacement, this is used to specify if and how the
    original item should be put back
    * fmstr: string to format a representation of the metadata, unclear if it is still used
    * xmlformat: formatstring to format the metadata as XML; probably not in use anymore, replace by the toElement
    method

    """
    def __init__(self, name, value, annotationwordlist=[], annotationposlist=[], annotatedposlist=[],
                 annotatedwordlist=[], annotationcharlist=[
    ], annotationcharposlist=[], annotatedcharlist=[],
            annotatedcharposlist=[], atype='text', cat=None, subcat=None, source=None, penalty=defaultpenalty,
            backplacement=defaultbackplacement):
        self.atype = atype
        self.name = name
        self.annotationwordlist = annotationwordlist if annotationwordlist != [] else value
        self.annotationposlist = annotationposlist
        self.annotatedwordlist = annotatedwordlist
        self.annotatedposlist = annotatedposlist
        self.annotationcharlist = annotationcharlist
        self.annotationcharposlist = annotationcharposlist
        self.annotatedcharlist = annotatedcharlist
        self.annotatedcharposlist = annotatedcharposlist
        self.value = value
        self.cat = cat
        self.subcat = subcat
        self.source = source
        self.penalty = penalty
        self.backplacement = backplacement
        self.fmstr = '<{}:type={}:annotationwordlist={}:annotationposlist={}:annotatedwordlist={}:annotatedposlist={}:value={}:cat={}:source={}>'
        self.xmlformat = xmlformat

    def __repr__(self):
        reprfmstr = 'Meta({},{},annotationwordlist={},annotationposlist={},annotatedposlist{},annotatedwordlist={},' \
                    ' atype={}, cat={}, subcat={}, source={}, penalty={}, backplacement={})'
        result = reprfmstr.format(repr(self.name), repr(self.value), repr(self.annotationwordlist),
                                  repr(self.annotationposlist),
                                  repr(self.annotatedposlist), repr(
            self.annotatedwordlist), repr(self.atype),
            repr(self.cat), repr(self.subcat), repr(
                self.source), repr(self.penalty),
            repr(self.backplacement))
        return result

    def __str__(self):
        frm = self.fmstr.format(self.name, self.atype, str(self.annotationwordlist),
                                str(self.annotationposlist), str(
            self.annotatedwordlist), str(self.annotatedposlist),
            str(self.value), str(self.cat), str(self.source))
        return frm

    def toElement(self):
        # result = self.xmlformat.format(name=self.name, atype=self.atype, annotationwordlist=str(self.annotationwordlist),
        #                    annotationposlist=str(self.annotationposlist), annotatedwordlist=str(self.annotatedwordlist),
        #                    annotatedposlist=str(self.annotatedposlist), value=str(self.value), cat=str(self.cat),
        #                         subcat=self.subcat,  source=str(self.source), backplacement=self.backplacement,
        #                         penalty=self.penalty)

        result = etree.Element('xmeta', name=self.name, atype=self.atype,
                               annotationwordlist=str(self.annotationwordlist),
                               annotationposlist=str(self.annotationposlist),
                               annotatedwordlist=str(self.annotatedwordlist),
                               annotatedposlist=str(self.annotatedposlist), value=str(self.value), cat=str(self.cat),
                               subcat=str(self.subcat), source=str(self.source), backplacement=str(self.backplacement),
                               penalty=str(self.penalty))
        return result

    def __eq__(self, other):
        if self is other:
            return True
        result = (self.atype == other.atype and
                  self.name == other.name and
                  self.annotationwordlist == other.annotationwordlist  and
                  self.annotationposlist == other.annotationposlist and
                  self.annotatedwordlist == other.annotatedwordlist and
                  self.annotatedposlist == other.annotatedposlist and
                  self.annotationcharlist == other.annotationcharlist and
                  self.annotationcharposlist == other.annotationcharposlist and
                  self.annotatedcharlist == other.annotatedcharlist and
                  self.annotatedcharposlist == other.annotatedcharposlist and
                  self.value == other.value and
                  self.cat == other.cat and
                  self.subcat == other.subcat and
                  self.source == other.source and
                  self.penalty == other.penalty and
                  self.backplacement == other.backplacement and
                  self.fmstr == other.fmstr and
                  self.xmlformat == other.xmlformat)
        return result


def remove_md_duplicates(metadata: List[Meta]) -> List[Meta]:
    newlist = []
    for meta in metadata:
        if not foundin(meta, newlist):
            newlist.append(meta)
    return newlist

def foundin(meta: Meta, metadata:List[Meta]) -> bool:
    for el in metadata:
        if el == meta:
            return True
    return False

def selectmeta(name, metadatalist):
    for meta in metadatalist:
        if meta.name == name:
            return meta
    return None


def mkSASTAMeta(token, nwt, name, value, cat, subcat=None, source=SASTA, penalty=defaultpenalty, backplacement=defaultbackplacement):
    result = Meta(name, value, annotatedposlist=[token.pos],
                  annotatedwordlist=[token.word], annotationposlist=[nwt.pos],
                  annotationwordlist=[
                      nwt.word], cat=cat, subcat=subcat, source=source, penalty=penalty,
                  backplacement=backplacement)
    return result


Metadata = List[Meta]

# errormessages
filled_pause = "Filled Pause"
repeated = "Repeated word token"
repeatedseqtoken = repeatedword
repeatedjaneenou = "Repeated ja, nee, nou"
janeenou = "ja, nee or nou filled pause"
shortrep = 'Short Repetition'
longrep = 'Long Repetition'
intj = 'Interjection'
unknownword = 'Unknown Word'
unknownsymbol = 'Unknown Symbol'
substringrep = 'Substring repetition'
repetition = 'Repetition'
fstoken = 'Retraced token'
falsestart = 'Retracing with Correction'
insertion = 'Insertion'
smallclause = 'Small Clause Treatment'
tokenmapping = 'Token Mapping'
insertiontokenmapping = 'Insertion Token Mapping'

def modifypenalty(pct:int) -> Penalty:
    newpen = int(pct /100 * defaultpenalty)
    return newpen
