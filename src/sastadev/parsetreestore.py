import os
import lxml.etree
import sastadev.treebankfunctions
import sastadev.conf

# moved to alpinoparsing

# storedparsespath = os.path.join(sastadev.conf.settings.SD_DIR, 'data', 'storedparses')
# storedparsesfilename = 'storedparses.xml'
# storedparsesfullname = os.path.join(storedparsespath, storedparsesfilename)
# storedparsesdict = {}
#
# if os.path.exists(storedparsesfullname):
#     fulltreebank = lxml.etree.parse(storedparsesfullname)
#     treebank = fulltreebank.getroot()
#     for tree in treebank:
#         mwustr = sastadev.treebankfunctions.getyieldstr(tree)
#         storedparsesdict[mwustr] = tree
#
# junk = 0