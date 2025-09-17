import re

from sastadev.stringfunctions import (intervowelrepeatedconsonantsre)

pattern = r'([aeiou])([mnfghkl])\2+([aeiou])'

testwords = ['ammmmmmmal', ' ammal', 'amaal']

for word in testwords:
    newword = re.sub(pattern, r'\1\2\2\3', word)
    print(word, newword)

for word in testwords:
    matches = intervowelrepeatedconsonantsre.finditer(word)
    for match in matches:
        junk = 0
    newword = intervowelrepeatedconsonantsre.sub(r'\1\2\2\3', word)
    print(word, newword)
