# import os
# from lxml import etree
# from sastadev.treebankfunctions import getyieldstr
# from sastadev import conf
#
# storedparsespath = os.path.join(conf.settings.SD_DIR, 'data', 'storedparses')
# storedparsesfilename = 'storedparses.xml'
# storedparsesfullname = os.path.join(storedparsespath, storedparsesfilename)
# storedparsesdict = {}
#
# if os.path.exists(storedparsesfullname):
#     fulltreebank = etree.parse(storedparsesfullname)
#     treebank = fulltreebank.getroot()
#     for tree in treebank:
#         mwustr = getyieldstr(tree)
#         storedparsesdict[mwustr] = tree
#
# junk = 0