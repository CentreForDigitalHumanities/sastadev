from auchannsettings import settings as auchannsettings
from auchann.align_words import AlignmentSettings, align_words


utt = 'dat pijn heeft .'
expl = 'omdat hij pijn heeft'

resultalignment = align_words(utt, expl, auchannsettings)
result = str(resultalignment)
print(result)
