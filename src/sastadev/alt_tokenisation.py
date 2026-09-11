from sastadev import CHAT_Annotation
from typing import List

space = ' '
inclusion_annotation_names = [CHAT_Annotation.CHAT_omittedword, CHAT_Annotation.CHAT_satellite_at_end,
                              CHAT_Annotation.CHAT_satellite_in_beginning, CHAT_Annotation.CHAT_falling_tone,
                              CHAT_Annotation.CHAT_rising_tone,]
inclusion_annotations = [ann for ann in CHAT_Annotation.annotations if ann.name in inclusion_annotation_names]

ignore_annotation_names = [CHAT_Annotation.CHAT_overlap_follows, CHAT_Annotation.CHAT_overlap_precedes]
ignore_annotations =  [ann for ann in CHAT_Annotation.annotations if ann.name in ignore_annotation_names]

normal_annotation_names = [CHAT_Annotation.CHAT_specialform, CHAT_Annotation.CHAT_unintelligible_speech,
                           CHAT_Annotation.CHAT_phonological_coding, CHAT_Annotation.CHAT_wordnoncompletion]
normal_annotations =  [ann for ann in CHAT_Annotation.annotations if ann.name in normal_annotation_names]


def is_inclusion_token(token:str) -> bool:
    for ann in inclusion_annotations:
        if ann.regex.compiledre.search(token):
            return True
    return False

def is_ignore_token(token: str) -> bool:
    for ann in ignore_annotations:
        if ann.regex.compiledre.search(token):
            return True
    return False

def is_normal_token(token:str) -> bool:
    for ann in normal_annotations:
        if ann.regex.compiledre.search(token):
            return True
    return False

def retokenize(tokens: List[str]) -> List[str]:
    newtokens = []
    newtokenlist = []
    for token in tokens:
        if is_inclusion_token(token):
            newtokenlist.append(token)
        elif is_ignore_token(token):
            pass
        else:
            newtokenlist.append(token)
            newtokenstr = space.join(newtokenlist)
            newtokens.append(newtokenstr)
            newtokenlist = []
    return newtokens


examples = [['[>]', 'Jan']]
def main():
    for ex in examples:
        alt_tok = retokenize(ex)
        print(alt_tok)


if __name__ == '__main__':
    main()