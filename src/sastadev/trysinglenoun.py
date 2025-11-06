from sastadev.conf import settings
from sastadev.treebankfunctions import writetb
import copy

word = 'zuiger'

tree = settings.PARSE_FUNC(word)
treecopy = copy.deepcopy(tree)
tbdict = {word: treecopy}

outfullname = './single_noun_tb.xml'
writetb(tbdict, outfullname)

