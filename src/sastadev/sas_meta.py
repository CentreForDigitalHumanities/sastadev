from dataclasses import dataclass
from sastadev.sastatypes import FileName, SynTree, UttId
from typing import List, Tuple


@dataclass
class SAS_Meta:
    """
    Objects of the class *SAS_Meta* contain information on an utterance selected by SAS for review by  human expert:

    * datasetname: the name of the dataset that the utterance comes from

    * treebanksfolder: the treebanksfolder that the utterance comes from

    * xmlfilename: the name of the xml file of the treebank

    * xsid: the utterance identifier

    * sentnodelist: list of nodes for words in the parsetree

    * origutt: the original utterance

    * parsedas: the string that was the input to the Alpino parser

    * message: a message to the human user to clarify why this utterance is selected for review

    * suggestedcodes: in some cases SAS can give a list of plausible missing codes

    * realwordcount: the number of 'real' words in the utterance (i.e., not interpunction signs)

    * codecount: the number of codes assigned to this utterance (most probably, the proportion between realwordcount
      and codecount must be within certain boundaries)

    """
    datasetname: str
    treebanksfolder: str
    xmlfilename: FileName
    xsid: UttId
    sentnodelist: List[SynTree]
    origutt: str
    parsedas: str
    message: str
    suggestedcodes: List[str]
    realwordcount: int
    codecount: int

@dataclass
class SAS_Result:
    """
    """
    xsid: str
    node: SynTree
    message: str
    suggestedcodes: List[str]

SAS_Match_and_Meta = Tuple[SynTree, SAS_Meta]

def sas_matchmeta2result(matchmeta: SAS_Match_and_Meta) -> SAS_Result:
    match, meta = matchmeta
    result = SAS_Result(meta.xsid, match, meta.message, meta.suggestedcodes)
    return result
