""" 
This module provides functions to deal an interrupted utterance with nonadjacent parts

It is presupposed that sasta_core keeps a copy of the tree of the last utterance ending with an interruption in a variable.
When the utterance with the continuation is encountered, the function getcombinationtree is invoked,
and the queries are applied to the tree that results from that function.

After the application of the pre and core queries, the results obtained are modified so that the annotations
belonging to the interrupted utterance are associated with the id of that utterances,
and the annotations belonging to the continuation utterances are associated with the id of that utterance.
"""
from collections import defaultdict
from sastadev.allresults import AllResults
from sastadev.conf import settings
from sastadev.sastatypes import ExactResults, ExactResultsDict, SynTree
from sastadev.treebankfunctions import getnodeyield, getorigutt, getsentence, getxsid
from sastadev.cleanCHILDEStokens import cleantext

def getcombinationtree(interrupted_tree, continuation_tree) -> SynTree:
    origutt1 = getorigutt(interrupted_tree)
    if origutt1 is None:
        origutt1 = getsentence(interrupted_tree)
    origutt2 = getorigutt(continuation_tree)
    cleanutt1, meta1 = cleantext(origutt1, repkeep=False)
    cleanutt2, meta2 = cleantext(origutt2, repkeep=False)
    newcleanutt = f'{cleanutt1} {cleanutt2}'
    newtree = settings.PARSE(newcleanutt)
    return newtree

def adaptresults(allresults: AllResults,  newtree: SynTree, interrupted_tree: SynTree) -> AllResults:
    # remove all results for the interrupted_tree
    # replace the interrupted_tree with the newtree
    # determine the length of the interrupted utterance and find the associated end
    # add all results for positions < interrupted_end to the interrupted xsid
    # add allresults for positions >= interrupted_end to the continuation xsid
    # replace the interrupted_tree with the newtree

    # after this function: also adapt nodeendmap[uttid] for the interrupted xsid
    # think about what to do with allutts


    exactresultsdict = allresults.exactresults
    interrupted_tree_length = len(getnodeyield(interrupted_tree))
    interrupted_tree_xsid = getxsid(interrupted_tree)
    newtree_xsid = getxsid(newtree)
    newexactresultsdict = defaultdict(list)
    newreskeyresults = []
    for reskey in exactresultsdict:
        reskeyresults = exactresultsdict[reskey]

        for xsid, pos in reskeyresults:
            if xsid == newtree_xsid:
                if pos >= interrupted_tree_length:
                    newreskeyresults[xsid].append((xsid, pos))
                else:
                    newreskeyresults[interrupted_tree_xsid].append((xsid, pos))
            else:
                newreskeyresults.append((xsid, pos))
        newexactresultsdict[reskey] = newreskeyresults

    # also adapt allcoreresults
    # adapt allmatches  # no this is still empty in this stage
    # maybe adapt allutts
    # adapt analysedtrees  # nee niet nodig want ze he
    new_analysedtrees = []
    for xsid, tree in allresults.analysedtrees:
        if xsid == interrupted_tree_xsid:
            newtuple = (xsid, newtree)
        else:
            newtuple = (xsid, tree)
        new_analysedtrees.append(newtuple)


    # or build a new allresults
    allresults.exactresults =  newexactresultsdict
    allresults.analysedtrees = new_analysedtrees
    return allresults


    pass
