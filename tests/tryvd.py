from sastadev.lexicon import getwordinfo, isa_inf, isa_vd

words = ['trouwen', 'getrouwd', 'getrouwen', 'geheb']
for word in words:
    if isa_vd(word):
        result = 'vd'
    elif isa_inf(word):
        result = 'inf'
    else:
        result = 'NO'
    print(f'{word}: {result}')
