"""
This module contains definitions of types used in multiple modules
"""

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from lxml import etree
from typing_extensions import TypeAlias

from sastadev.query import Query
from sastadev.sastatoken import Token

Level = str  # in the future perhaps NewType('Level', str)
Position = int  # in the future perhaps NewType('Position', int)
QId = str  # in the future perhaps NewType('QId', str)
ResultsKey = Tuple[QId, str]
SynTree = etree.Element  # type: ignore
TreeBank = etree.Element
UttId = str  # in the future perhaps NewType('UttId', str)


Item = str  # in the future perhaps NewType('Item', str)
Item2LevelsDict = Dict[Item, List[Level]]
Item_Level = Tuple[Item, Level]

AltCodeDict = Dict[Item_Level, Item_Level]
AltId = int
AnalysedTrees = List[Tuple[UttId, SynTree]]
BackPlacement = int
CapitalName = str
CountryName = str
ContinentName = str
CELEXPosCode = str
FirstName = str
LocationName = str
DCOIPt = str
DeHet = str
CELEX_INFL = str
DCOITuple = Tuple
Lemma = str
CorrectionMode = str  # Literal['0','1','n']
ErrorDict = Dict[str, List[List[str]]]
Level = str  # in the future perhaps NewType('Level', str)
Item = str  # in the future perhaps NewType('Item', str)
Item_Level = Tuple[Item, Level]
IntSpan = Tuple[int, int]
AltCodeDict = Dict[Item_Level, Item_Level]
QId = str  # in the future perhaps NewType('QId', str)
UttId = str  # in the future perhaps NewType('UttId', str)
Position = int  # in the future perhaps NewType('Position', int)
PositionStr = str
Relation = str
Stage = int
SynTree = etree._Element  # type: ignore
GoldTuple = Tuple[str, str, Counter]
GoldResults = Dict[QId, GoldTuple]
Item2LevelsDict = Dict[Item, List[Level]]
Match = Tuple[SynTree, SynTree]
Matches = List[Match]
MatchesDict = Dict[Tuple[QId, UttId], Matches]
MetaElement = etree.Element
ExactResult = Tuple[UttId, Position]
ExactResults = List[ExactResult]
ExactResultsDict = Dict[ResultsKey, ExactResults]  # qid
SampleName = str
AllExactResultsDict = Dict[SampleName, ExactResultsDict]
Gender = str
Table = List[List[Any]]
Header = List[str]
Pattern = str
Penalty: TypeAlias = int
PhiTriple: TypeAlias = Tuple[str, str, str]
OptPhiTriple: TypeAlias = Optional[PhiTriple]
PositionMap: TypeAlias = Dict[Position, Position]
QueryDict: TypeAlias = Dict[QId, Query]
QIdCount: TypeAlias = Dict[QId, int]
MethodName: TypeAlias = str  # perhaps in the future NewType('MethodName', str)
FileName: TypeAlias = str  # perhaps in the future NewType('FileName', str)
ReplacementMode: TypeAlias = int
ResultsCounter: TypeAlias = Counter  # Counter[UttId]  # Dict[UttId, int]
ResultsDict: TypeAlias = Dict[QId, ResultsCounter]
SampleSizeTuple: TypeAlias = Tuple[List[UttId], int, Optional[PositionStr]]
Span: TypeAlias = Tuple[PositionStr, PositionStr]
Item_Level2QIdDict: TypeAlias = Dict[Item_Level, QId]
Nort: TypeAlias = Union[SynTree, Token]
ExactResultsFilter: TypeAlias = Callable[[
    Query, ExactResultsDict, ExactResult], bool]
Targets: TypeAlias = int
Treebank: TypeAlias = etree._Element
TreePredicate: TypeAlias = Callable[[SynTree], bool]
TokenTreePredicate: TypeAlias = Callable[[Token, SynTree], bool]
URL: TypeAlias = str
UttTokenDict: TypeAlias = Dict[UttId, List[Token]]
UttWordDict: TypeAlias = Dict[UttId, List[str]]
WordInfo: TypeAlias = Tuple[Optional[CELEXPosCode],
                            Optional[DeHet], Optional[CELEX_INFL], Optional[Lemma]]
XpathExpression = str

MethodVariant = str
DataSetName = str
HeadedTable = Tuple[Header, Table]
# moved the following to allresults.py
# CoreQueryFunction = Callable[[SynTree], List[SynTree]]
# PostQueryFunction = Callable[[SynTree, allresults.AllResults], List[SynTree]]
# QueryFunction = Union[CoreQueryFunction, PostQueryFunction]
