from sastadev.metadata import Meta, MetaValue
from typing import List
from sastadev.CHAT_Annotation import CHAT_omittedword, CHAT_replacement
from sastadev import sastatok
from sastadev.cleanCHILDEStokens import robustness

verbose = False

tokenisation = 'tokenisation'
space = ' '
CHAT_repetition_code = '[/]'
CHAT_retracing_code = '[//]'


annotation_correction = 'CHAT annotation correction'

dis_dit_wrong_replacements = {"di's": "dit", "da's": "dat", "hij's": "hij", "zij's": "zij", "die's": "die"}
def correct_dis_dit(origutt: str, chat_metadata:List[Meta])  -> str:
    # dis_dit_metas = [meta for meta in chat_metadata if meta.name == CHAT_replacement and
    #                  meta.annotatedwordlist != [] and meta.annotatedwordlist[0] in dis_dit_wrong_replacements and
    #                  meta.annotationwordlist != [] and
    #                  meta.annotationwordlist[0] == dis_dit_wrong_replacements[meta.annotatedwordlist[0]]
    #                  ]
    # omitted_is_metas = [meta for meta in chat_metadata if meta.name == CHAT_omittedword and
    #                                                   meta.annotationwordlist == ["is"]]

    tokenisation_metadata = [meta for meta in chat_metadata if meta.name == tokenisation]
    if tokenisation_metadata == []:
        return origutt, chat_metadata
    tokenisation_meta = tokenisation_metadata[0]
    tokens = tokenisation_meta.annotationwordlist
    annotationposlist = [10 * (i +1 ) for i in range(len(tokens))]
    for i, token in enumerate(tokens):
        if token in dis_dit_wrong_replacements:
            tokenplus1 = tokenisation_meta.annotationwordlist[i+1]
            tokenplus2 = tokenisation_meta.annotationwordlist[i+2]
            tokenplus3 = tokenisation_meta.annotationwordlist[i+3]
            tokenplus4 = tokenisation_meta.annotationwordlist[i+4]
            if tokenplus1.strip() == "[:" and \
               tokenplus2.strip() == dis_dit_wrong_replacements[token] and \
               tokenplus3.strip() == "]" and \
               tokenplus4.strip() == "0is":
                rest_metadata = []
                corrected_tokens = [dis_dit_wrong_replacements[token]] + ['is']
                tail_tokens, tail_metadata = correct_dis_dit(tokens[i+5:], rest_metadata)
                new_meta1 = Meta(annotation_correction, value=corrected_tokens, annotationwordlist=corrected_tokens,
                               annotationposlist = annotationposlist[i:i+5], annotatedwordlist= tokens[i: i+5], source='CHAT')
                new_meta2 = Meta('corrected_utt', value=origutt, source='CHAT')
                new_metadata = [new_meta1, new_meta2] + tail_metadata
                new_tokens = tokens[:i] + corrected_tokens + tail_tokens
                new_utt = space.join(new_tokens)
                return new_utt, new_metadata
    return origutt, chat_metadata





def correct_chat(utt:str) -> str:
    # tokenize the utt
    utt2 = robustness(utt, verbose=verbose)
    tokens = sastatok.sasta_tokenize(utt2)
    words = [t.word for t in tokens]
    new_words = correct_chat_repetition(words)
    raw_new_utt = space.join(new_words)
    new_utt = space.join(raw_new_utt.split())
    return new_utt

def correct_chat_repetition(words:List[str]) -> List[str]:
    # detect (w+) < \1 > [/] different
    # (w+) = repeating_words
    #  \1 = repeated_words
    # different = following_words
    # transform to < \1 > [/] w+
    new_words = []
    for i, word in enumerate(words):
        if word in [CHAT_repetition_code, CHAT_retracing_code]:
            CHAT_code = word
            repeated_words = find_repeated_words(words[:i])
            l_repeated_words = len(repeated_words)
            repeated_words_parts = partition(repeated_words)
            repeated_words_parts_1 = repeated_words_parts[0]
            l_repeated_words_parts_1 = len(repeated_words_parts_1)
            if repeated_words != []:
                end = i + 1 + l_repeated_words_parts_1
                if end < len(words):
                    following_words = [w for w in words[i + 1:end]]
                    following_differs = repeated_words_parts_1 != following_words
                else:
                    following_differs = True
                repeating_words_begin = i - l_repeated_words - 2 - l_repeated_words_parts_1
                repeating_words_end = repeating_words_begin + l_repeated_words_parts_1
                if following_differs and repeating_words_begin >= 0:
                        repeating_words = [w for w in words[repeating_words_begin:repeating_words_end]]
                        if repeating_words == repeated_words_parts_1:
                            new_repeated_words = convert_partition(repeated_words_parts)
                            rest = correct_chat_repetition(words[i+1:])
                            new_words = new_words[:repeating_words_begin] + new_repeated_words + [CHAT_code] + repeating_words + rest
                            break
                        else:
                            new_words.append(word)
                elif len(repeated_words_parts) > 1:  # < als als > [/] als -> als [/] als [/] als
                    rest = correct_chat_repetition(words[i+1:])
                    partition_part = convert_partition(repeated_words_parts)
                    new_words = new_words[:i-l_repeated_words - 2] + partition_part + [CHAT_code] + rest
                    break
                else:
                    new_words.append(word)
            else:
                new_words.append(word)
        else:
            new_words.append(word)
    return new_words

def find_repeated_words(words:List[str]) -> List[str]:
    repeated_words = []
    if words[-1] != '>':
        return []
    i = len(words) - 1
    start = i
    while i >= 0:
        if words[i] != '<':
            start = i
            i = i - 1
        else:
            break
    result = words[start:-1]
    return result

def clean_utt(utt:str) -> str:
    utt_tokens = sastatok.sasta_tokenize(utt)
    utt_words = [t.word for t in utt_tokens]
    raw_result = space.join(utt_words)
    result = space.join(raw_result.split())
    return result



def partition(wlist:List[str]) -> List[List[str]]:
    """
    split wlist into a number of identical sublists
    """
    no_sub_parts = [wlist]
    max =  len(wlist) // 2
    partition_found = False
    for i in range(max):
        diff_found = False
        if partition_found:
            return parts
        start = 0
        parts = []
        prev_part = None
        while start < len(wlist):
            new_part = wlist[start:start + i + 1]
            parts.append(new_part)
            if prev_part is not None and prev_part != new_part:
                diff_found = True
                break
            prev_part = new_part
            start += i + 1
        if not diff_found:
            partition_found = True
    if partition_found:
        return parts
    else:
        return no_sub_parts

def convert_partition(parts:List[List[str]]) -> List[str]:
    if parts == []:
        return []
#    elif len(parts) == 1:
#        return parts[0]
    l_part_1 = len(parts[0])
    if l_part_1 > 1:
        prefix = ['<']
        suffix = ['>']
    else:
        prefix = []
        suffix = []
    results = []
    for part in parts[:-1]:
        results += prefix + part + suffix + ['[/]']
    results += prefix + parts[-1] + suffix
    return results


def try_partition():
    the_lists = [['a', 'a', 'a', 'a', 'a'],
             ['a', 'b', 'a', 'b', 'a', 'b'],
             ['a', 'b', 'c', 'a', 'b', 'c'],
             ['a', 'b', 'c', 'd', 'e', 'f'],
             ]
    the_test_lists = the_lists
    for the_list in the_test_lists:
        the_partition = partition(the_list)
        print(the_partition)
        conversion = convert_partition(the_partition)
        print(conversion)
        print(space.join(conversion))


def test_correct_chat():
    test_correction_tuples = correction_tuples
    for wrong, raw_correct in test_correction_tuples:
        correct = clean_utt(raw_correct)
        correction = correct_chat(wrong)
        if correction == correct:
            print(f'OK: {wrong} correctly changed into {correction}')
        else:
            print(f'NO: {wrong} changed into \n{correction}\n{correct}')


correction_tuples = [
    ("ik denk van een <van een> [/] geheime kluis <geheime kluis> [/]. [+ VU]",
     "ik denk <van een> [/] van een   <geheime kluis> [/] geheime kluis. [+ VU]"),
    ("of van vroeger deze <deze> [/]? [+ VU]",
     "of van vroeger  deze [/] deze? [+ VU]"),
    ("<hij is> [//] hij <hij> [/] moest eigenlijk zeggen ik <ik> [/] doe het zelf. [+ VU]",
     "<hij is> [//]  hij [/] hij moest eigenlijk zeggen  ik [/] ik doe het zelf. [+ VU]"),
    ("er is <er is> [/] een paadje. [+ VU]",
     " <er is> [/] er is een paadje. [+ VU]"),
    ("dan ga <dan ga> [/] je ruilen. [+ VU]",
     "<dan ga> [/] dan ga je ruilen. [+ VU]"),
    ("<zo> [//] dan <dan> [/] is de andere op de <de> [/] zwarte. [+ VU]",
     "<zo> [//]  dan [/] dan is de andere op  de [/] de zwarte. [+ VU]"),
    ("< als als als > [/] als Semsom er is . [+ VU ]",
     "als [/] als [/] als [/] als Semsom er is . [+ VU ]"),
    ("ja maar < als als als > [/] als Semsom er is . [+ VU ]",
     "ja maar als [/] als [/] als [/] als Semsom er is . [+ VU ]"),
    ("als < als als als > [/] Semsom er is . [+ VU ]",
     "als [/] als [/] als [/] als Semsom er is . [+ VU ]"),
    ("ja maar als < als als als > [/] Semsom er is . [+ VU ]",
     "ja maar als [/] als [/] als [/] als Semsom er is . [+ VU ]"),
    ("als Semsom < als Semsom als Semsom als Semsom > [/]  er is . [+ VU ]",
     "< als Semsom > [/] < als Semsom > [/] < als Semsom > [/] als Semsom er is . [+ VU ]"),
    ("en toen had ik < toen > [/] in me broek gepist . [+ VU ]",      # unclear how/whether this should be corrected
     "en toen had ik < toen > [/] in me broek gepist . [+ VU ]"),
    ("het gaat toen ook niet over < toen > [/] wie de sterkste was . [+ VU ]",   # also unclear
     "het gaat toen ook niet over < toen > [/] wie de sterkste was . [+ VU ]")
   ]



if __name__ == '__main__':
    test_correct_chat()
