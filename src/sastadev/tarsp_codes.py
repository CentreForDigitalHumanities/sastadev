import itertools

stage2 = 2
stage3 = 3
stage4 = 4
stage5 = 5
stage6 = 6
stage7 = 7

anymood = 0
decl = 1
question = 2
imp = 3

VBcombinations = {}
Vcombinations = {}

VBcombinationsbystage = {}
Vcombinationsbystage = {}

noVcombinations = {}
noVcombinationsbystage = {}

noVcombinationsbystage[stage2] = ['T030', 'T035', 'T064', 'T071', 'T078']         # BX een OndB OndVC Ov2: all 2
noVcombinationsbystage[stage3] = ['T014', 'T065', 'T079', 'T140', 'T027', 'T117']
    # BBX (3) OndBVC (3) Ov3 (3) Xneg (2) # BvZn (2)  VzN (2)
noVcombinationsbystage[stage4] =  ['T010', 'T012', 'T013', 'T016', 'T017', 'T025', 'T032',
                                   'T033', 'T083', 'T111', 'T116', 'T147', 'T156']
                                #    BBBv (3) Bbv/B (2) BBvZn (3) BepZnBv (3) BezZn (2) BvBepZn (3)  de (2)
                                #    die/dezeZn (2)  Ov4 (4) Vr(XY) (2) VzBepZn (3)  OvZnBv4 (3) ZnZn (2)

noVcombinationsbystage[stage5] = ['T015', 'T115', 'T034', 'T042', 'T084']
                                # BepBvZn (3) BvBepZn (3) dit/datZn (2) hetZn (2) Ov5 (5)

noVcombinationsbystage[stage6] = ['T038', 'T114', 'T138']
                                # geen X (2) VzB (2) XenX (3)

noVcombinationsbystage[stage7] = ['T115']
                                # VzBepBvZn (4)

noVcombinations[2] = ['T030', 'T035', 'T064', 'T071', 'T078'] + \
                     ['T140', 'T027', 'T117'] + \
                     ['T012', 'T017',  'T032', 'T033', 'T111', 'T156'] + \
                     ['T034', 'T042'] + \
                     ['T038', 'T114'] + \
                     []
noVcombinations[3] = ['T014', 'T065', 'T079'] + \
                     ['T010', 'T013', 'T016', 'T025', 'T116', 'T147'] + \
                     ['T015', 'T115'] + \
                     ['T138']

noVcombinations[4] = ['T083'] + ['T115']

noVcombinations[5] = ['T084']


Vcombinationsbystage[(stage2, decl)] = ['T030', 'T072', 'T099', 'T140']
Vcombinationsbystage[(stage2, question)] = ['T001']              # because an utterance can consist of two words: is
# dat ?
VBcombinationsbystage[stage2] = ['T030', 'T064']

Vcombinationsbystage[(stage3, question)] = ['T001' ] + ['T111', 'T129']
Vcombinationsbystage[(stage3, imp)] = ['T121', 'T135']
Vcombinationsbystage[(stage3, decl)] = ['T014',  'T073', 'T076', 'T079', 'T125', 'T141']
VBcombinationsbystage[stage3] = ['T014',  'T073', 'T111', 'T125', 'T129']   # should T079 Ov3 be here?

Vcombinationsbystage[(stage4, question)] = ['T111', 'T129'] + [ 'T112', 'T130']  # for T112, T130 requires only 4 zinsdelem
Vcombinationsbystage[(stage4, imp)] = ['T135']
Vcombinationsbystage[(stage4, decl)] = ['T074', 'T075', 'T083']
VBcombinationsbystage[stage4] = ['T074', 'T075', 'T083', 'T111', 'T112', 'T129']

Vcombinationsbystage[stage5, question] = ['T112', 'T130']
Vcombinationsbystage[(stage5, imp)] = ['T136']
Vcombinationsbystage[(stage5, decl)] = ['T029', 'T077', 'T084', 'T100', ]
VBcombinationsbystage[stage5] = ['T029', 'T100', 'T112', 'T130', 'T136']

Vcombinationsbystage[(stage6, question)] = ['T113', 'T131']
Vcombinationsbystage[(stage6, imp)] = ['T137']
Vcombinationsbystage[(stage6, decl)] = ['T003']
VBcombinationsbystage[stage6] = ['T003', 'T113', 'T131',  'T137']

Vcombinationsbystage[(stage7, anymood)] = ['T080', 'T090']
VBcombinationsbystage[stage7] = ['T080', 'T090']

# now Vcombinations by minimal # consttuents (zinsdelen) and mood

Vcombinations[(2, decl)] = ['T030', 'T072','T099', 'T140']
Vcombinations[(2, question)] = ['T001'] + ['T111', 'T129']
Vcombinations[(2, imp)] = ['T121']
VBcombinations[2] = ['T030', 'T064'] + ['T111', 'T129'] + ['T121']

Vcombinations[(3, question)] = ['T001'] + ['T111', 'T129']
Vcombinations[(3, imp)] = ['T135']
Vcombinations[(3, decl)] = ['T014',  'T073', 'T076', 'T079', 'T125']
VBcombinations[3] = ['T014',  'T073', 'T111', 'T125', 'T129'] + ['T135']  # should T079 Ov3 be here?

Vcombinations[(4, question)] = [ 'T112', 'T130'] + ['T136']
Vcombinations[(4, imp)] =  ['T112']
Vcombinations[(4, decl)] = ['T074', 'T075', 'T083'] + ['T077']
VBcombinations[4] = ['T074', 'T075', 'T083'] + ['T077'] + ['T136'] + ['T112', 'T130']

Vcombinations[5, question] = ['T113', 'T131']
Vcombinations[(5, imp)] = ['T137']
Vcombinations[(5, decl)] = ['T029',  'T084', 'T100', ]
VBcombinations[5] = ['T029', 'T084', 'T100',  'T136'] + ['T113', 'T131']

Vcombinations[(6, decl)] = ['T003'] + ['T080']
VBcombinations[6] = ['T003', 'T080']






# Vcombinationsbystage = {}
# Vcombinationsbystage[stage2] = [code for ]
# Vcombinations[stage3] = stage3V_Decl_combinations + stage3V_Imp_combinations + stage3V_Question_combinations
# Vcombinations[stage4] = stage4V_Decl_combinations + stage4V_Imp_combinations + stage4V_Question_combinations
# Vcombinations[stage5] = stage5V_Decl_combinations + stage5V_Imp_combinations + stage5V_Question_combinations
# Vcombinations[stage6] = stage6V_Decl_combinations + stage6V_Imp_combinations + stage6V_Question_combinations
# Vcombinations[stage7] = stage7V_combinations

V1questioncodes = ['T001', 'T129', 'T130', 'T131']
noV1questioncodes = ['T111', 'T112', 'T113']

allVcombinations = list(itertools.chain.from_iterable([Vcombinations[tuple] for tuple in Vcombinations]))
allnoVcombinations = list(itertools.chain.from_iterable([noVcombinations[tuple] for tuple in noVcombinations]))

allVBcombinations = list(itertools.chain.from_iterable([VBcombinations[stage] for stage in VBcombinations]))
