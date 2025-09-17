from editdistance import distance

topcat = 'top'

# overvl overlug overvloedige vloe vloeistof weggesp wegge wegspult

repeatedwords = [(['overvl', 'overlug'], 'overvloedige'),
                 (['weggesp', 'wegge'], 'wegspult')
                ]

fuzzyrepetitionthreshold = 5 / 8

def fuzzyrepetition(nonword: str, word:str) -> bool:
   lnonword = len(nonword)
   lword = len(word)
   if lnonword < lword:
       cpword = word[:lnonword]
   thedistance = distance(nonword, cpword)
   reldistance = thedistance / lnonword
   result = reldistance <= fuzzyrepetitionthreshold
   return result



def tryme():
    for lst, wrd in repeatedwords:
        for nonwrd in lst:
            result = fuzzyrepetition(nonwrd, wrd)
            print(f'{nonwrd} - {wrd}: {result}')



if __name__ == '__main__':
    tryme()
