from lxml import etree
from sastadev import CHAT_Annotation
from sastadev.conf import settings
from sastadev.constants import outtreebanksfolder
from sastadev.datasets import trainingdatasets
from sastadev.treebankfunctions import find1, getxsid, getuttid
import os
from typing import List

space = ' '
scope_open = '<'
scope_close = '>'

inclusion_annotation_names = [CHAT_Annotation.CHAT_omittedword, CHAT_Annotation.CHAT_satellite_at_end,
                              CHAT_Annotation.CHAT_satellite_in_beginning, CHAT_Annotation.CHAT_falling_tone,
                              CHAT_Annotation.CHAT_rising_tone,]
inclusion_annotations = [ann for ann in CHAT_Annotation.annotations if ann.name in inclusion_annotation_names]

ignore_annotation_names = [CHAT_Annotation.CHAT_overlap_follows, CHAT_Annotation.CHAT_overlap_precedes,
                           CHAT_Annotation.CHAT_pause]
ignore_annotations =  [ann for ann in CHAT_Annotation.annotations if ann.name in ignore_annotation_names]

normal_annotation_names = [CHAT_Annotation.CHAT_specialform, CHAT_Annotation.CHAT_unintelligible_speech,
                           CHAT_Annotation.CHAT_phonological_coding, CHAT_Annotation.CHAT_wordnoncompletion]
normal_annotations =  [ann for ann in CHAT_Annotation.annotations if ann.name in normal_annotation_names]

scoped_ignore_annotations = ['[/]', '[//]', '[///]']

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
    neutral, in_scope, inclusion_state, ignore_state = 0, 1, 2, 3
    state = neutral
    for tokenctr, token in enumerate(tokens):
        next_token = tokens[tokenctr + 1] if tokenctr < len(tokens) - 1  else None
        if state == neutral and next_token in scoped_ignore_annotations:
            pass
        elif state == ignore_state and token == ']':
            state = neutral
        elif token == '[+ ':
            state = ignore_state
        elif state == ignore_state:
            pass
        elif state == neutral and next_token in ['[:', '[=', '[: ', '[= ']:
            next_3_token = tokens[tokenctr + 3] if tokenctr < len(tokens) - 3 else None
            if next_3_token == ']':
                state = inclusion_state
                newtokenlist.append(token)
        elif state == inclusion_state and token == ']':
            newtokenlist.append(token)
            newtokenstr = space.join(newtokenlist)
            newtokens.append(newtokenstr)
            newtokenlist = []
            state = neutral
        elif state == inclusion_state:
            newtokenlist.append(token)
        elif token in scoped_ignore_annotations:
            pass
        elif token == scope_open:
            state = in_scope
        elif token == scope_close:  # so no <> inside <>
            state = neutral
        elif state == in_scope:
            pass
        elif is_inclusion_token(token):
            newtokenlist.append(token)
        elif is_ignore_token(token):
            pass
        else:
            newtokenlist.append(token)
            newtokenstr = space.join(newtokenlist)
            newtokens.append(newtokenstr)
            newtokenlist = []
    return newtokens


example_pairs = [(['[>]', 'Jan'], ['Jan']),
            (['dit', 'is', '[/]', 'is', 'mooi'], ['dit', 'is', 'mooi']),
            (['<', 'dit', 'is', '>', '[/]', 'dit', 'is', 'mooi'], ['dit', 'is', 'mooi']),
            (['een', 'heul', '[:', 'heel', ']', 'mooi', 'boek'], ['een', 'heul [: heel ]', 'mooi', 'boek'] )
            ]
def test():
    selected_pairs = example_pairs
    for ex, corr in selected_pairs:
        alt_tok = retokenize(ex)
        if alt_tok == corr:
            print(f'OK: {alt_tok} == {corr} for {ex}')
        else:
            print(f'NO: {alt_tok} != {corr} for {ex}')


tokenisation_xpath = './/xmeta[@name="tokenisation"]/@annotationwordlist'
cleaned_tokenisation_xpath = './/xmeta[@name="cleanedtokenisation"]/@annotationwordlist'
def main():
    datasets = trainingdatasets
    for ds in datasets:
        infolder = os.path.join(settings.DATAROOT, ds.name, outtreebanksfolder)
        raw_filenames = os.listdir(infolder)
        filenames = [fn for fn in raw_filenames if fn.endswith('.xml')]
        for fn in filenames:
            fullname = os.path.join(infolder, fn)
            full_tb = etree.parse(fullname)
            tb = full_tb.getroot()
            for tree in tb:
                tok_meta_str = find1(tree, tokenisation_xpath )
                cleaned_tok_meta_str = find1(tree, cleaned_tokenisation_xpath)
                xsid = getxsid(tree)
                if tok_meta_str is None:
                    print(f'No tokenisation found for xsid={xsid}')
                    continue
                if cleaned_tok_meta_str is None:
                    print(f'No cleaned tokenisation found for xsid={xsid}')
                    continue
                tok_meta = eval(tok_meta_str)
                cleaned_tok_meta = eval(cleaned_tok_meta_str)
                new_tok = retokenize(tok_meta)
                if len(new_tok) != len(cleaned_tok_meta):
                    print(f'{xsid}: {new_tok} / {tok_meta} ')
                    junk = 0


if __name__ == '__main__':
    # test()
    main()