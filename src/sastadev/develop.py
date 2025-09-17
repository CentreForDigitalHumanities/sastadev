"""
Module to develoop new functions in . This modulke is NOT used by sastadev. Functions and data in this file are only temporarily here.
"""

from sastadev.metadata import Meta
from sastadev.parse_criteria import Criterion, negative
from sastadev.sastatypes import SynTree
from typing import List


predmxpath = './/node[@rel="predm"]'

def getpredmcount(tree: SynTree, mds: List[Meta] = [], methodname: str='') -> int:
    predms = getpredm(tree)
    return len(predms)

def getpredm(tree):
    predms = tree.xpath(predmxpath)
    return predms

predmcriterion =  Criterion('predmcount', getpredmcount, negative,
                            "Count of number of occurrences of nodes with relation 'predm'")
