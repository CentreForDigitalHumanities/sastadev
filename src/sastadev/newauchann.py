"""
This module is intended for an adaptation of auchann output in which words of false starts are marked wit the prefix 1
"""
import re
included_prefix = '1'
space = ' '


simple_false_start_pattern = r'\b(\w+)(\s*)(\[//\])'

scoped_false_start_pattern = r'(<[^>]+>)\s*\[//\]'

def false_start_to_prefix(auchannstr: str) -> str:
    result = auchannstr
    result = re.sub(simple_false_start_pattern, rf'{included_prefix}\1\2' , result)

    result = scoped_false_start_to_prefix(result)


    return result

def clean_spaces(instr:str) -> str:
    words = instr.split()
    result = space.join(words)
    return result

def scoped_false_start_to_prefix(auchannstr: str) -> str:
    firstmatch = re.search(scoped_false_start_pattern, auchannstr)
    if firstmatch is None:
        return auchannstr
    else:
        replacement = get_replacement(firstmatch.group(1))
        raw_resultstr = auchannstr[:firstmatch.start()] + replacement + scoped_false_start_to_prefix(auchannstr[firstmatch.end():])
        resultstr = clean_spaces(raw_resultstr)
        return resultstr

def get_replacement(instr: str) -> str:
    purestr = instr[1:-1]
    word_list = purestr.split(space)
    out_word_list = [f'{included_prefix}{word}' for word in word_list]
    result = f'{space}{space.join(out_word_list)}{space}'
    return result


inputstrings = ['0ik 0heb ook ik [//] ADD hebt [//]',
                'ik <heb echt> [//] iets 0hebt 0echte nodig']

def test():
    for instr in inputstrings:
        result = false_start_to_prefix(instr)
        print(instr)
        print(result)
        print('---------')



if __name__ == "__main__":
    test()