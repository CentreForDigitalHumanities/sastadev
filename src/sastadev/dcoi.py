"""
This module provides properties of DCOI features as implementred in Alpino.
For more, see dcoi package under python
"""

# the maximum number of features for a given pt
dcoi_features = {
   'n':  ['genus', 'getal', 'graad', 'naamval', 'ntype'],
    'adj': ['buiging', 'getaL-n', 'graad', 'naamval', 'positie'],
    'ww': ['buiging', 'positie', 'pvagr',  'pvtijd', 'wvorm'],
    'tw': ['graad', 'naamval', 'numtype', 'positie'],
    'vnw': ['buiging', 'genus', 'getal', 'graad', 'naamval', 'npagr', 'pdtype', 'persoon', 'positie', 'status',
            'vwtype'],
    'lid': ['lwtype', 'naamval', 'npagr'],
    'vz': ['vztype'],
    'vw': ['conjtype'],
    'spec': ['spectype']
}
