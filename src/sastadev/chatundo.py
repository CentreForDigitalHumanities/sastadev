import re

from chamd.cleanCHILDESMD import (atsignletters, barezero, bch, blocking,
                                  chat_ca_syms, cliticlink, complexlocalevent,
                                  dependenttier, doubleexclam, doubleslash1,
                                  doubleslash2, endquote, eqexclam, eqtext1,
                                  eqtext2, errormark1, errormark2, exclam1,
                                  exclam2, gtreplre1, gtreplre2, inlinecom,
                                  internalpause, interpunction, ltreplre1,
                                  ltreplre2, pauses1, pauses2, pauses3,
                                  phonfrag1, plus2, plus3, plusdot3,
                                  postcodes, precodes, qre1, qre2,
                                  scopedinlinecom, scopedreformul, scopedtimes,
                                  segmentrep, slash1, slash2,
                                  squarebracketseen, squarebracketstwee,
                                  syllablepause, times, trn, whitespace, www,
                                  zerostr)

space = ' '
eps = ''

simpleinterpunction = re.compile(r'([.?!,])')


undocolonre = re.compile(r'([^ ]+)\s+\[:[^\]]*\]')
roundbracketinsert = re.compile(r'\([-\'\w]+\)')
phonfragmarker = re.compile(r'&-|&\+|&')
prosody = re.compile(r'[:\u02c8\u02cc]')
generalsquarebrackets = re.compile(r'\[.*?\]')
leftangle = re.compile(r'<')
rightangle = re.compile(r'>')
plusvaria = re.compile(r'\+//\.|\+"\.|\+"/\.|\+\.')
correctplusquote = re.compile(r'\+"\.')

lve = re.compile(r'&{l=[\w:]+(.*?)&}l=[\w:]+')
nve = re.compile(r'&{n=[\w:]+(.*?)&}n=[\w:]+')

picbullet = re.compile(r'\u00b7%pic:\s*[\w\.]+\u00b7')
txtbullet = re.compile(r'\u00b7%txt:\s*[\w\.]+\u00b7')
# bullet code (Unicode middle dot)
bulletedtimealign = re.compile(r'\u00b7[0123456789_ ]+\u00b7')
bulletedtimealign2 = re.compile(
    r'\u0015[0123456789_ ]+\u0015')  # NAK is sometimes used

pluscompoundmarker = re.compile(r'\+')

blockingsequence = re.compile(r'\u2260.*?\u2260')
interposedword = re.compile(r'&\*\w\w\w:[\w:]+')


def chatundo(instr):
    result = instr

    result = interposedword.sub(eps, result)

    # blockingsequence
    result = blockingsequence.sub(eps, result)

    # remove time alignment p. 67
    result = bulletedtimealign.sub(space, result)
    result = bulletedtimealign2.sub(space, result)

    # picbullet
    result = picbullet.sub(eps, result)

    # txtbullet
    result = txtbullet.sub(eps, result)

    # long vocal event
    result = lve.sub(r'\1', result)

    # long nonvocal event
    result = nve.sub(r'\1', result)

    # remove scoped times <...> [x ...] keeping the ... between <> not officially defined
    result = scopedtimes.sub(r'\1', result)

    # remove scoped inlinecom <...> [% ...] keeping the ... between <> not officially defined
    result = scopedinlinecom.sub(r'\1', result)

    # remove pauses
    result = pauses3.sub(space, result)
    result = pauses2.sub(space, result)
    result = pauses1.sub(space, result)

    # remove round brackets and everything in between
    result = roundbracketinsert.sub(eps, result)

    # remove multiple wordmarker p. 43, 73-74
    result = times.sub(eps, result)

    # remove @letters+:
    result = atsignletters.sub(eps, result)

    # remove inline comments [% ...] p70, 78, 85
    result = inlinecom.sub(eps, result)

    #  remove scoped reformulation symbols [///] p 73
    result = scopedreformul.sub(r'\1', result)

    # result = wreformul.sub(r'\1', result)   #checked this one not

    # remover errormark1 [*] and preceding <>
    result = errormark1.sub(r'\1 ', result)

    # remover errormark2 [*]
    result = errormark2.sub(eps, result)

    # remove inline dependent tier [%xxx: ...]

    result = dependenttier.sub(eps, result)

    # remove    postcodes p. 75-76
    result = postcodes.sub(eps, result)

    # remove precodes p.75-76
    result = precodes.sub(eps, result)

    # remove bch p. 75-76
    result = bch.sub(eps, result)

    # remove trn p.75-76
    result = trn.sub(eps, result)

    # remove +...  p. 63
    result = plusdot3.sub(eps, result)

    # remove [<] and preceding > on purpose before [//]
    result = ltreplre1.sub(r'\1 ', result)

    # remove [<]   on purpose before [//]
    result = ltreplre2.sub(space, result)

    # remove [>] and preceding <>
    result = gtreplre1.sub(r'\1 ', result)

    # remove [>]
    result = gtreplre2.sub(space, result)

    # remove [//] keep preceding part between <>, drop <>
    result = doubleslash1.sub(r'\1', result)

    # remove [//] keep preceding word
    result = doubleslash2.sub(eps, result)

    # remove [!] and <> around preceding text    p.68
    result = exclam1.sub(r'\1', result)

    # remove [!] p.68
    result = exclam2.sub(space, result)

    # remove [/] keep preceding part between <> depending
    result = slash2.sub(r'\1', result)

    # remove [/] keep the word before or delete it depending on repkeep option
    result = slash1.sub(eps, result)  # checked

    #    result = re.sub(r'\[<\]', '', result)

    # remove [?] and preceding <>
    result = qre1.sub(r'\1 ', result)

    # remove [?]
    result = qre2.sub(space, result)

    # remove [=! <text>] and preceding <>
    result = eqexclam.sub(r'\1 ', result)

    # remove [= <text> ] and preceding <>  p 68/69 explanation
    result = eqtext1.sub(r'\1 ', result)

    # remove [= <text>]
    result = eqtext2.sub(space, result)

    # replace word [: text] by word
    result = undocolonre.sub(r'\1 ', result)

    # remove phonological fragments p. 61 &= (simple events)
    result = phonfrag1.sub(eps, result)

    # remove  fileld pause and phonological fragment markers &- &+ &
    #    https://talkbank.org/manuals/Clin-CLAN.pdf states &+ for phonological fragments(p. 18)
    result = phonfragmarker.sub(eps, result)

    # remove www intentionally after phonological fragments
    result = www.sub(eps, result)

    # remove 0[A-z]
    result = zerostr.sub(eps, result)

    # delete any remaining 0's
    result = barezero.sub(space, result)

    # remove underscore
    result = re.sub(r'_', eps, result)

    # remove [!!]
    result = doubleexclam.sub(space, result)

    # remove +"/. p. 64-65
    result = endquote.sub(eps, result)

    # remove +/. +/? +//. +//?
    result = plus3.sub(r' ', result)

    # remove +".    (p. 65)  +!? (p. 63)
    result = correctplusquote.sub(r' ', result)

    # remove +.  +^ +< +, ++ +" (p. 64-66)
    result = plus2.sub(r' ', result)

    # remove silence marks (.) (..) (...) done above see pauses
    #    result = re.sub(r'\(\.(\.)?(\.)?\)', r' ', result)

    # remove syllablepauses p. 60
    result = syllablepause.sub(r'\1', result)

    # remove complexlocalevent p. 61
    result = complexlocalevent.sub(space, result)

    # replace clitic link ~by space
    result = cliticlink.sub(space, result)

    # replace chat-ca codes by space p. 86,87
    result = chat_ca_syms.sub(space, result)

    # remove segment repetitions p89 Unicode 21AB UTF8 e2 86 ab
    result = segmentrep.sub(eps, result)

    # remove blocking Unicode 2260 not-equal sign    p89
    result = blocking.sub(eps, result)

    # remove  internal pausing ^  p. 89
    result = internalpause.sub(eps, result)

    # remove primary stress, secondary stress, lengthening
    result = prosody.sub(eps, result)

    result = plusvaria.sub(eps, result)

    # next is an ad-hoc extension for Lotti
    # replace [een], [twee] by space
    result = squarebracketseen.sub(space, result)
    result = squarebracketstwee.sub(space, result)

    # remove any other square brackets plus everything in between
    result = generalsquarebrackets.sub(eps, result)

    # remove any remaining < and > scope markers
    result = leftangle.sub(eps, result)
    result = rightangle.sub(eps, result)

    # remove + compound marker
    result = pluscompoundmarker.sub(eps, result)

    # surround interpunction with whitespace
    result = interpunction.sub(lambda m: ' ' + m.group(0) + ' ', result)

    # remove superfluous spaces etc. this also removes CR etc
    result = whitespace.sub(' ', result)
    result = result.strip()
    return (result)


def cleanspaces(instr):
    instr2 = cleaninterpunction(instr)
    resultrow = instr2.split()
    result = space.join(resultrow)
    return result


def cleaninterpunction(instr):
    result = instr
    result = simpleinterpunction.sub(r' \1', result)
    return result
