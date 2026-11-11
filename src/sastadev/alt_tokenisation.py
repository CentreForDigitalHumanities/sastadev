from lxml import etree
import re
from sastadev import CHAT_Annotation as CHAT
from sastadev.CHAT_Annotation import CHAT_trailing_off_of_a_question, CHAT_Regex, compiledre_types
from sastadev.conf import settings
from sastadev.constants import outtreebanksfolder
from sastadev.datasets import trainingdatasets
from sastadev.sastatypes import SynTree
from sastadev.treebankfunctions import find1, getxsid, getuttid
import os
from typing import List

space = ' '
scope_open = '<'
scope_close = '>'

inclusion_annotation_names = [CHAT.CHAT_omittedword, CHAT.CHAT_satellite_at_end,
                              CHAT.CHAT_satellite_in_beginning, CHAT.CHAT_falling_tone,
                              CHAT.CHAT_rising_tone,]
inclusion_annotations = [ann for ann in CHAT.annotations if ann.name in inclusion_annotation_names]

filler_annotation_names = [CHAT.CHAT_filler, CHAT.CHAT_nonword,
                           CHAT.CHAT_phonological_fragment]
ignore_annotation_names = [  # CHAT.CHAT_alternative_transcription
                              CHAT.CHAT_best_guess,
                              CHAT.CHAT_clause_delimiter,
                              CHAT.CHAT_contrastive_stressing,
                              CHAT.CHAT_een,
                              CHAT.CHAT_errormarking,
                              CHAT.CHAT_excluded_utterance,
                              CHAT.CHAT_falling_tone,
                              CHAT.CHAT_included_utterance,
                              CHAT.CHAT_interposed_word,
                              CHAT.CHAT_interruption,
                              CHAT.CHAT_interruption,
                              CHAT.CHAT_interruption_of_a_question,
                              CHAT.CHAT_lazy_overlap,
                              CHAT.CHAT_omittedword,
                              CHAT.CHAT_other_completion,
                              CHAT.CHAT_overlap_follows,
                              CHAT.CHAT_overlap_precedes,
                              CHAT.CHAT_pause,
                              CHAT.CHAT_question_with_exclamation,
                              CHAT.CHAT_quick_uptake,
                              CHAT.CHAT_quotation_follows,
                              CHAT.CHAT_quotation_precedes,
                              CHAT.CHAT_quoted_utterance,
                              CHAT.CHAT_rising_tone,
                              CHAT.CHAT_self_completion,
                              CHAT.CHAT_self_interrupted_question,
                              CHAT.CHAT_self_interruption,
                              CHAT.CHAT_simple_event,
                              CHAT.CHAT_stressing,
                              CHAT.CHAT_timed_pause,
                              CHAT.CHAT_trailing_off,
                              CHAT.CHAT_trailing_off_of_a_question,
                              CHAT.CHAT_transcription_break,
                              CHAT.CHAT_twee,
                              CHAT.CHAT_untranscribed_material,
                              CHAT.CHAT_zero_utterance,

                          ] + filler_annotation_names



ignore_annotations =  [ann for ann in CHAT.annotations if ann.name in ignore_annotation_names]

normal_annotation_names = [CHAT.CHAT_specialform, CHAT.CHAT_unintelligible_speech,
                           CHAT.CHAT_phonological_coding, CHAT.CHAT_wordnoncompletion,
                           CHAT.CHAT_satellite_at_end, CHAT.CHAT_satellite_in_beginning, CHAT.CHAT_primary_stress,
                           CHAT.CHAT_secondary_stress, CHAT.CHAT_lengthened_syllable, CHAT.CHAT_blocking,
                           CHAT.CHAT_pause_between_syllables, CHAT.CHAT_quotation_begin, CHAT.CHAT_quotation_end,
                           CHAT.CHAT_segment_repetition, CHAT.CHAT_joined_words, CHAT.CHAT_clitic_boundary,
                           CHAT.CHAT_blocked_segments]
normal_annotations =  [ann for ann in CHAT.annotations if ann.name in normal_annotation_names]

scoped_ignore_annotations = ['[/]', '[//]', '[///]', '[/-]', '[/?]', '[e]']

scope_keep_tokens = ['[<]', '[>]', '[*]', '[?]', '[=!', '[!]', '[=?', '[%', '[% ']
scope_keep_annotation_names = [CHAT.CHAT_overlap_follows, CHAT.CHAT_overlap_precedes, CHAT.CHAT_stressing,
                               CHAT.CHAT_contrastive_stressing]
scope_keep_annotations = [ann for ann in CHAT.annotations if ann.name in scope_keep_annotation_names]

start_ignore_tokens = ['[+ ', '[*', '[* ', '[=?', '[=!', '[x', '[% ', '[%', '[^', '[^ ', '[=!',  '[*', '[* ',
                       '[-', '[- ']
start_event_ignore_tokens = ['&{l=', '&{n=']
end_event_ignore_tokens = ['&}l=', '&}l=']

bullet_ignore_tokens= [u'\u00b7%pic:', u'\u00b7%txt:', u'\u0015', u'\u00b7']


def has_compiledre(regex: CHAT_Regex) -> bool:
    for retype in compiledre_types:
        if isinstance(regex, retype):
            return True
    return False

def is_scope_keep_token(token:str) -> bool:
    if token in scope_keep_tokens:
        return True
    for ann in scope_keep_annotations:
        if ann.regex.compiledre.search(token):
            return True
    return False

def is_inclusion_token(token:str) -> bool:
    for ann in inclusion_annotations:
        if ann.regex.compiledre.search(token):
            return True
    return False

def is_ignore_token(token: str) -> bool:
    for ann in ignore_annotations:
        if has_compiledre(ann.regex) and ann.regex.compiledre.search(token):
            return True
    return False

def is_normal_token(token:str) -> bool:
    for ann in normal_annotations:
        if ann.regex.compiledre.search(token):
            return True
    return False

to_remove_tokens = []
to_remove_tokens_start = ['[*', '[*' ]
to_remove_tokens_end = [']']
def remove_simple_items(tokens: List[str]) -> List[str]:
    neutral_state, remove_state = 0, 1
    state = neutral_state
    newtokens = []
    for token in tokens:
        if token in to_remove_tokens:  # no it is not that simple
            pass
        elif token in to_remove_tokens_start:
            state = remove_state
        elif state == remove_state and token not in to_remove_tokens_end:
            pass
        elif state == remove_state and token in to_remove_tokens_end:
            state = neutral_state
        else:
            newtokens.append(token)
    return newtokens

inside, outside = 0, 1
def retokenize_inner_tokens(tokens: List[str]) -> List[str]:
    start, end = -1, -1
    result = tokens
    for i, token in enumerate(tokens):
        if token == '<':
            start = i + 1
        elif token == '>':
            end = i
        if end >= start and start >= 0  and end >= 0:
            new_inner = ['<'] + core_retokenize(tokens[start:end]) + ['>']
            rest_result = retokenize_inner_tokens(tokens[end+1:])
            result = tokens[:start - 1] + new_inner + rest_result
            return result
    return result

# @first remove everything unscoped that has to be removed
# @retokenize inside <>
# @retokenzize

def retokenize(tokens: List[str]) -> List[str]:
    tokens1 = remove_simple_items(tokens)
    tokens2 = retokenize_inner_tokens(tokens1)
    new_tokens = core_retokenize(tokens2)
    return new_tokens


def core_retokenize(tokens: List[str]) -> List[str]:
    newtokens = []
    newtokenlist = []
    scope_tokens = []
    (neutral, in_scope, inclusion_state, ignore_state,
     multi_replacement_state_1, multi_replacement_state_2,
     bullet_ignore_state, event_ignore_state) = 0, 1, 2, 3, 4, 5, 6, 7
    state = neutral
    for tokenctr, token in enumerate(tokens):
        next_token = tokens[tokenctr + 1] if tokenctr < len(tokens) - 1  else None
        if state == neutral and next_token in scoped_ignore_annotations:
            pass
        elif state == ignore_state and token == ']':
            state = neutral
        elif state == multi_replacement_state_1:
            newtokenlist.append(token)
            if token not in ['[:', '[: ', '[::']:
                newtokenstr = space.join(newtokenlist)
                newtokens.append(newtokenstr)
                newtokenlist = []
                state = multi_replacement_state_2
        elif state == multi_replacement_state_2 and token != ']':
            newtokenlist.append(token)
            if next_token != ']':
                newtokenstr = space.join(newtokenlist)
                newtokens.append(newtokenstr)
                newtokenlist = []
        elif state == multi_replacement_state_2 and token == ']':
            newtokenlist.append(token)
            newtokenstr = space.join(newtokenlist)
            newtokens.append(newtokenstr)
            newtokenlist = []
            state = neutral
        elif token in start_ignore_tokens or re.search(r'^\[%\w\w\w:\]$', token):
            state = ignore_state
        elif token[:4] in start_event_ignore_tokens:
            state = event_ignore_state
        elif state == event_ignore_state and token[:4] in end_event_ignore_tokens:
            state = neutral
        elif state in [bullet_ignore_state] and token in bullet_ignore_tokens:
            state = neutral
        elif token  in bullet_ignore_tokens:
            state = bullet_ignore_state
        elif state in [ignore_state, bullet_ignore_state, event_ignore_state]:
            pass
        elif state == neutral and next_token in ['[:', '[=', '[: ', '[= ', '[::']:
            next_3_token = tokens[tokenctr + 3] if tokenctr < len(tokens) - 3 else None
            if next_3_token == ']':
                state = inclusion_state
                newtokenlist.append(token)
            elif next_token  in ['[=', '[= ']:
                state = inclusion_state
                newtokenlist.append(token)
            elif next_token in ['[:', '[: ', '[::']:
                newtokenlist.append(token)
                state = multi_replacement_state_1
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
            if not any([tk == '>' for tk in tokens[tokenctr+1:] ]):
                pass
                settings.LOGGER.error(f'Unclosed "<" in {tokens} ')
            else:
                state = in_scope
        elif token == scope_close:  # so no <> inside <>
            if next_token in scoped_ignore_annotations:
                scope_tokens = []
            elif is_scope_keep_token(next_token):
                newtokens.extend(scope_tokens)
                scope_tokens = []
            state = neutral
        elif state == in_scope:
            if not is_ignore_token(token):
                scope_tokens.append(token)
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


example_pairs = [
            (['nog', 'n', 'naar', 'binnen', 'toe', '.', '[+ ', 'G', ']'], ['nog', 'n', 'naar', 'binnen', 'toe', '.']),
            (['e', '[=', 'even', ']', 'kijken', '.', '[+ ', 'G', ']'], ['e [= even ]', 'kijken', '.']),
            (['[>]', 'Jan'], ['Jan']),
            (['dit', 'is', '[/]', 'is', 'mooi'], ['dit', 'is', 'mooi']),
            (['<', 'dit', 'is', '>', '[/]', 'dit', 'is', 'mooi'], ['dit', 'is', 'mooi']),
            (['een', 'heul', '[:', 'heel', ']', 'mooi', 'boek'], ['een', 'heul [: heel ]', 'mooi', 'boek']),
             (['goed', '[:',  'went', ']', '[*]'], ['goed [: went ]']),


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

def get_alt_tokenisation(tree: SynTree) -> List[str]:
    tok_meta_str = find1(tree, tokenisation_xpath)
    cleaned_tok_meta_str = find1(tree, cleaned_tokenisation_xpath)
    xsid = getxsid(tree)
    if tok_meta_str is None:
        print(f'No tokenisation found for xsid={xsid}')
        return []
    if cleaned_tok_meta_str is None:
        print(f'No cleaned tokenisation found for xsid={xsid}')
        return []
    tok_meta = eval(tok_meta_str)
    cleaned_tok_meta = eval(cleaned_tok_meta_str)
    new_tok = retokenize(tok_meta)
    if len(new_tok) != len(cleaned_tok_meta):
        settings.LOGGER.error(f'{xsid}: {new_tok} / {tok_meta} / {cleaned_tok_meta}')
    return new_tok


def main():
    verbose = True
    datasets = trainingdatasets
    for ds in datasets:
        infolder = os.path.join(settings.DATAROOT, ds.name, outtreebanksfolder)
        raw_filenames = os.listdir(infolder)
        filenames = [fn for fn in raw_filenames if fn.endswith('.xml')]
        for fn in filenames:
            if verbose:
                print(f'Processing {ds.name}/{fn}...')
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
                    print(f'{xsid}: {new_tok} / {tok_meta} in {fn}')
                    junk = 0


if __name__ == '__main__':
    # test()
    main()