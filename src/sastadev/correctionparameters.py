from dataclasses import dataclass

from sastadev.methods import Method
from sastadev.sastatypes import TreeBank


@dataclass
class CorrectionParameters:
    method: Method
    options: dict
    allsamplecorrections : dict
    thissamplecorrections: dict
    treebank: TreeBank
    contextdict : dict
