from sastadev.lexicon import getwordinfo, getwordposinfo


def main():
    dewordinfos = getwordinfo('de')
    hetwordinfos = getwordinfo('het')
    eenwordinfo = getwordinfo('een')

    vanwordinfo = getwordinfo('van')
    aanwordinfo = getwordinfo('aan')

    delidwordinfos = getwordposinfo('de', 'lid')

    junk = 0


if __name__ == '__main__':
    main()