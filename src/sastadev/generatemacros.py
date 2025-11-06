'''
The generatemacros module provides the function generatemacros of type None -> Dict[str, str], which generates a macrodictionary
for systematically constructed macro definitions.

In particular, the module generatemacros.py generates macros for a list of pairs (verb, adposition),
e.g. (*slaan*, *op*) in which Alpino analyzes the adposition as the head of an prepositional complement (pc),
but where it should be considered the head of a modifier. These cases should also count as such if the
adposition is written together with *er*, *hier* or *daar* (e.g. *erop*, *hierop*, *daarop*),
which are considered unanalysable adverbs by Alpino.
So we need a macro which characterizes these exceptions for each (verb, adposition) pair and, for each pair,
for the combinations of the adposition with *er*, *hier* en *daar* when written together with the adposition.

The generatemacros function generates this macro on the basis of a list of  (verb, adposition) pairs contained in this module.
[These should probably better be moved to an exceptionslexicon module.]

Running the module standalone outputs the macrodefinitions to stdout
'''

from typing import Dict, List, Set, Tuple

StrPair = Tuple[str, str]

tarsp_wvzexceptions: Set[StrPair] = {('hebben', 'van'),  # hebben can occur with pc/van but only in fixed expressions: last hebben van, spijt hebben van
                                     ('slaan', 'op'),  # of course correct but not used in this sense with very young children
                                     ('lukken', 'in'), \
                                     ('passen', 'bij'), \
                                     ('vallen', 'vanaf'),
                                     # next list derived from CHILDES via Paqu
                                     # query: https://paqu.let.rug.nl:8068/?db=childesdutch&word=&rel=pc&hword=&postag=vz&hpostag=ww&meta=&sn=10
                                     # and manual filtering see file Tarsp_wrongpcs.txt in the lassy folder
                                     ('af_brengen', 'vanaf'),
                                     ('af_komen', 'op'),
                                     ('af_komen', 'van'),
                                     ('af_komen', 'vanaf'),
                                     ('bouwen', 'op'),
                                     ('dansen', 'op'),
                                     ('doen', 'overheen'),
                                     ('door_gaan', 'op'),
                                     ('draaien', 'om'),
                                     ('eten', 'van'),
                                     ('gaan', 'aan'),
                                     ('gaan', 'om'),
                                     ('gaan', 'overheen'),
                                     ('gaan', 'tussendoor'),
                                     ('gaan', 'voor'),
                                     ('hebben', 'af'),
                                     ('hebben', 'uit'),
                                     ('helpen', 'bij'),
                                     ('houden', 'voor'),
                                     ('komen', 'achteraan'),
                                     ('komen', 'af'),
                                     ('komen', 'bij'),
                                     ('komen', 'doorheen'),
                                     ('komen', 'om'),
                                     ('komen', 'tot'),
                                     ('krijgen', 'af'),
                                     ('krijgen', 'op'),
                                     ('kunnen', 'omheen'),
                                     ('liggen', 'bij'),
                                     ('mee_gaan', 'met'),
                                     ('plakken', 'aan'),
                                     ('rijden', 'op'),
                                     ('sabbelen', 'op'),
                                     ('spelen', 'in'),
                                     ('staan', 'op'),
                                     ('staan', 'voor'),
                                     ('struikelen', 'over'),
                                     ('tellen', 'tot'),
                                     ('uit_komen', 'in'),
                                     ('varen', 'op'),
                                     ('vast_knopen', 'aan'),
                                     ('zeggen', 'in '),
                                     ('zien', 'op'),
                                     ('zijn', 'tegen'),
                                     ('zijn', 'voor'),
                                     ('zitten', 'op'),
                                     ('zitten', 'voor'),
                                     ('zoeken', 'op')
                                     }

# also do erin erbij etc

Rlemma: str = """( @lemma="er{vz}" or @lemma="daar{vz}" or @lemma="hier{vz}" ) """

Tarsp_WVz_exception_basemodel: str = """(@pt="ww"  and @rel ="hd" and @lemma="{ww}" and
     ../node[@rel="pc" and
            ( (node[@rel="hd" and @lemma="{vz}"]) or
                ( @lemma="er{rvz}" or @lemma="daar{rvz}" or @lemma="hier{rvz}" )
            )
            ]
 )"""

pc_vc_exception_basemodel: str = """( @rel="pc" and (node[@rel = "hd" and @lemma="{vz}"] or 
                                                   ( @lemma="er{rvz}" or @lemma="daar{rvz}" or @lemma="hier{rvz}" )) and 
                                     ../node[@rel="hd" and @pt="ww" and @lemma="{ww}"] )"""

macrodef_model: str = '{name} = """{exp}"""\n'


def getrvz(vz:str) -> str:
    if vz == 'tot':
        rvz = 'toe'
    elif vz == 'met':
        rvz = 'mee'
    else:
        rvz = vz
    return rvz

def generatemacros() -> Dict[str, str]:
    newmacros: Dict[str, str] = {}
    newparts: List[str] = []
    for (ww, vz) in tarsp_wvzexceptions:
        rvz = getrvz(vz)
        newpart = Tarsp_WVz_exception_basemodel.format(ww=ww, vz=vz, rvz=rvz)
        newparts.append(newpart)
    partsor = ' or \n'.join(newparts)
    newmacro = "( {} )".format(partsor)
    newmacros['Tarsp_WVz_exception'] = newmacro

    newparts = []
    for (ww, vz) in tarsp_wvzexceptions:
        rvz = getrvz(vz)
        newpart = pc_vc_exception_basemodel.format(ww=ww, vz=vz, rvz=rvz)
        newparts.append(newpart)
    partsor = ' or \n'.join(newparts)
    newmacro = "( {} )".format(partsor)
    newmacros['Tarsp_pc_vc_exception'] = newmacro
    return newmacros


def main():
    macros = generatemacros()
    for macroname in macros:
        macrodef = macrodef_model.format(name=macroname, exp=macros[macroname])
        print(macrodef)


if __name__ == '__main__':
    main()
