from sastadev.NLtypes import Activity, alt, Alt, And, Animate, Event, Human, Location, NonAnimate, NonHuman, Object, Property, Quantity, SemType, State, UnKnown
from typing import List

su = 'su'
obj1 = 'obj1'
obj2 = 'obj2'
mod = 'mod'
ld = 'ld'
predc = 'predc'


def s(x: SemType) -> Alt:
    return alt([x])

def sh(sem: SemType) -> Alt:
    result = Alt([And([sem])])
    return result
def aa(semtypelist: List[SemType]) -> Alt:
    result = Alt([And(semtypelist)])
    return result

# $node.pt	$node.pdtype	$node.vwtype	$node.lemma	semtype Count
vnws_auris_vankampen_schlichtingvankampen =[
('vnw',	'adv-pron',	'aanw',	'daar', alt([Object, Event, Location]), 3416),
('vnw',	'adv-pron',	'aanw',	'er',  alt([Object, Event, Location]),	4333),
('vnw',	'adv-pron',	'aanw',	'hier',  alt([Object, Event, Location]),	4505),
('vnw',	'adv-pron',	'onbep',	'ergens',  alt([Object, Event, Location]),	132),
('vnw',	'adv-pron',	'onbep',	'nergens',  alt([Object, Event, Location]),	22),
('vnw',	'adv-pron',	'onbep',	'overal',  alt([Object, Event, Location]),	25),
('vnw',	'adv-pron',	'vb',	'waar',  alt([Object, Event, Location]),	1766),
('vnw',	'grad',	'onbep',	'allebei',  alt([Object]),	12),
('vnw',	'grad',	'onbep',	'allemaal',  alt([Object]),	86),
('vnw',	'grad',	'onbep',	'alletwee',  alt([Object]),	11),
('vnw',	'grad',	'onbep',	'beiden',  alt([Human]),	1),
('vnw',	'grad',	'onbep',	'meer', aa([Object, Quantity]),	1617),
('vnw',	'grad',	'onbep',	'meest', aa([Object,Quantity]),	2),
('vnw',	'grad',	'onbep',	'minder', aa([Object, Quantity]),	13),
('vnw',	'grad',	'onbep',	'teveel', aa([Object, Quantity]),	23),
('vnw',	'grad',	'onbep',	'veel', aa([Object, Quantity]),	598),
('vnw',	'grad',	'onbep',	'weinig', aa([Object, Quantity]),	29),
('vnw',	'pron',	'aanw',	'dat',  alt([NonHuman, Event]),	9964),
('vnw',	'pron',	'aanw',	'die',  alt([Object, Event]),	7284),
('vnw',	'pron',	'aanw',	'dit',  alt([NonHuman, Event]),	3198),
('vnw',	'pron',	'aanw',	'zulk',  alt([NonHuman, Event]),	1),
('vnw',	'pron',	'betr',	'dat',  alt([Object, Event]),	55),   # must inherit it from its antecedent
('vnw',	'pron',	'betr',	'die',  alt([Object, Event]),	966),
('vnw',	'pron',	'onbep',	'alles',  alt([NonAnimate, Event]),	289),
('vnw',	'pron',	'onbep',	'andermans',  alt([Human]),	1),
('vnw',	'pron',	'onbep',	'eentje',  alt([Object, Quantity]),	119),  # Count v. Mass
('vnw',	'pron',	'onbep',	'iedereen',  alt([Human]),	74),
('vnw',	'pron',	'onbep',	'iemand',  alt([Human]),	95),
('vnw',	'pron',	'onbep',	'iets',  alt([NonHuman, Event]),	451),
('vnw',	'pron',	'onbep',	'niemand',  alt([Human]),	38),
('vnw',	'pron',	'onbep',	'niets',  alt([NonHuman, Event]),	537),
('vnw',	'pron',	'onbep',	'wat',  alt([NonHuman, Event]),	1180),
('vnw',	'pron',	'onbep',	'zoiets',  alt([NonHuman, Event]),	35),
('vnw',	'pron',	'pers',	"'t",  alt([NonHuman, Event]) ,	1),
('vnw',	'pron',	'pers',	'da',  alt([NonHuman, Event]),	1),
('vnw',	'pron',	'pers',	'dat',  alt([NonHuman, Event]),	202),
('vnw',	'pron',	'pers',	'dit',  alt([NonHuman, Event]),	124),
('vnw',	'pron',	'pers',	'ge',  alt([Human]),	7),
('vnw',	'pron',	'pers',	'haar',  alt([Human]),	193),
('vnw',	'pron',	'pers',	'haarzelf',  alt([Human]),	3),
('vnw',	'pron',	'pers',	'hem',  alt([Human]),	1927),
('vnw',	'pron',	'pers',	'het',  alt([NonHuman]),	6113),
('vnw',	'pron',	'pers',	'hij',  alt([Human]),	4513),
('vnw',	'pron',	'pers',	'hun',  alt([Human]),	16),
('vnw',	'pron',	'pers',	'ik',  alt([Human]),	19243),
('vnw',	'pron',	'pers',	'je',  alt([Human]),	15448),
('vnw',	'pron',	'pers',	'jij',  alt([Human]),	5251),
('vnw',	'pron',	'pers',	'jijzelf',  alt([Human]),	1),
('vnw',	'pron',	'pers',	'jou',  alt([Human]),	1066),
('vnw',	'pron',	'pers',	'jullie',  alt([Human]),	302),
('vnw',	'pron',	'pers',	'u',  alt([Human]),	36),
('vnw',	'pron',	'pers',	'we',  alt([Human]),	4182),
('vnw',	'pron',	'pers',	'wij',  alt([Human]),	455),
('vnw',	'pron',	'pers',	'ze',  alt([Human]),	3421),
('vnw',	'pron',	'pers',	'zij',  alt([Human]),	230),
('vnw',	'pron',	'pers',	'zijn',  alt([Human]),	1),
('vnw',	'pron',	'pr',	'je',  alt([Human]),	871),
('vnw',	'pron',	'pr',	'jezelf',  alt([Human]),	39),
('vnw',	'pron',	'pr',	'me',  alt([Human]),	394),
('vnw',	'pron',	'pr',	'mezelf',  alt([Human]),	18),
('vnw',	'pron',	'pr',	'mij',  alt([Human]),	1458),
('vnw',	'pron',	'pr',	'mijn',  alt([Human]),	2),
('vnw',	'pron',	'pr',	'mijzelf',  alt([Human]),	1),
('vnw',	'pron',	'pr',	'ons',  alt([Human]),	121),
('vnw',	'pron',	'recip',	'elkaar',  alt([Human]),	246),
('vnw',	'pron',	'refl',	'zich',  alt([Human]),	73),
('vnw',	'pron',	'refl',	'zichzelf',  alt([Human]),	13),
('vnw',	'pron',	'vb',	"'n'",  alt([Object]),	10),
('vnw',	'pron',	'vb',	'een',  alt([Object]),	18),
('vnw',	'pron',	'vb',	'voor',  alt([UnKnown]),	18),
('vnw',	'pron',	'vb',	'wat',  alt([NonHuman, Event]),	6410),
('vnw',	'pron',	'vb',	'wie',  alt([Human]),	824),
('vnw',	'pron',	'vb',	'wiens',  alt([Human]),	3)

]

vnwsemdict = {(lemma, vnwtype, pdtype): semtype
              for (_, vnwtype, pdtype, lemma, semtype, _) in vnws_auris_vankampen_schlichtingvankampen}

# lemma frame[2] semreq=List[Dict[rel: semtype]] semtype
verbs = [ ('liggen', 'intransitive', [{su: sh(Object)}], sh(State)),
          ('maken', 'pred_np', [{su: sh(Animate), obj1: sh(Object), predc:Alt([And([State]), And([Property])])}], sh(Activity)),
          ('kapot_maken', 'part_transitive(kapot)', [{su: sh(Animate), obj1: sh(Object)}], sh(Activity)),
          ('maaien', 'intransitive', [{su: sh(Animate)}], sh(Activity) ),
          ('maaien', 'transitive', [{su:sh(Animate), obj1: sh(NonAnimate)}], sh(Activity))
]

wwsemdict = {(lemma, frame): semtype for (lemma, frame, _, semtype) in verbs }
wwreqsemdict = {(lemma, frame): reqsemtype for (lemma, frame, reqsemtype, _) in verbs}


defaultreqsemdict = {'transitive': [{su: sh(Animate), obj1: sh(Object)}],
                     'unacc': [{su: sh(Object)}]
                    }