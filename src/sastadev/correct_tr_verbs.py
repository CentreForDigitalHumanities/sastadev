
# considered but rejected  boeken doen kennen op_eten pakken plakken smeren vinden vragen weten willen zien
# maybe: betekenen

transitive_only_verbs = ['hebben', 'leggen', 'maken', 'neer_zetten', 'neer_leggen', 'schenken', 'stellen', 'zetten', ]

verbcondition = ' or '.join([f'@lemma="{wrd}"' for wrd in transitive_only_verbs])

lonely_transitive_verbs_xpath = f"""
//node[@pt="ww" and @wvorm="pv" and not(@pvtijd="tgw" and @pvagr="mv") and
      ({verbcondition}) and 
      (@rel="--" or @rel="dp") and 
      count(ancestor::node[@cat="top"]/descendant::node[@pt="ww"]) = 1 and
      count(ancestor::node[@cat="top"]/descendant::node[@pt="n" or @pt="vnw"]) <= 1 and
      count(ancestor::node[@cat="top"]/descendant::node[@word and @pt!="let" and @pt!="tsw"]) >= 2
      ]
"""

# also consider:
#
# //node[@pt="ww" and  @wvorm="vd" and
#        ancestor::node[@cat="top"]/descendant::node[@lemma="hebben" and @wvorm="pv"] and
#       ({verbcondition}) and
#       (@rel="--" or @rel="dp") and
#       count(ancestor::node[@cat="top"]/descendant::node[@pt="ww"]) = 2 and
#       count(ancestor::node[@cat="top"]/descendant::node[@pt="n" or @pt="vnw"]) <= 1 and
#       count(ancestor::node[@cat="top"]/descendant::node[@word and @pt!="let" and @pt!="tsw"]) >= 2
#       ]
# goves nou, ik heb net gehad, maar xxx heb van papier gemaakt (both in vankampen/Laura)

# insert "dat" immediately after the verb form found