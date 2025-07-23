from sastadev.cleanCHILDEStokens import cleantext, robustness
from sastadev import sastatok


utts = [(1, 'ja. [+EA]', 'ja.'),
        (2,
         'dat <is>[//] ligt meer verder ofzo, naast STAD. [+ VU] [%zwaait met haar handen om de richting aan te geven]',
         'dat ligt meer verder ofzo, naast STAD.'),
        (3, 'ze [: het is een] spel waar je een kat bent', 'het is een spel waar je een kat bent'),
        (4, 'gaatie [: gaat ie]', 'gaat ie')]

for i, utt, correctcleanutt in utts:
    robutt = robustness(utt)
    cleanutt, meta = cleantext(robutt, repkeep=False)
    if cleanutt != correctcleanutt:
        print(f'NO:{utt}: {cleanutt}!={correctcleanutt}')