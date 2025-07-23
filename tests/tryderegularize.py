from deregularise import correctinflection

trylist = ['ebakt', 'sebakt', 'sebakte']

def tryme():
    for el in trylist:
        corrections = correctinflection(el)
        print(f'{el}:')
        for correction in corrections:
            print(correction)


if __name__ == '__main__':
    tryme()