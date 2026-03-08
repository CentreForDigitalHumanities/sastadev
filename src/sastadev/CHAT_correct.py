from sastadev.metadata import Meta, MetaValue
from typing import List
from sastadev.CHAT_Annotation import CHAT_omittedword, CHAT_replacement

tokenisation = 'tokenisation'
space = ' '

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



