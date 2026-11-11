from sastadev.CHAT_correct import correct_dis_dit
import cleanCHILDEStokens


def tryme():
    utt = "Di's [: dit] 0is oote [: grote] ."
    # cleaned_utt, chat_metadata = cleanCHILDEStokens.cleantext(utt, repkeep=False)

    new_utt, new_metadata = correct_dis_dit(cleaned_utt, chat_metadata)
    print(new_utt)
    junk = 0


if __name__ == '__main__':
    tryme()
