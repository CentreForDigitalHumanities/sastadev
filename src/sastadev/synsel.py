import copy
from dataclasses import dataclass
from sastadev.filefunctions import get_corrected_tree_fullname
from sastadev.sastatypes import SynTree
from sastadev.lexicon import predicative_pp_expressions
from sastadev.macros import expandmacros
from sastadev.test_functions import test_f
from sastadev.treebankfunctions import getattval as gav, getyieldstr, indextransform
from typing import Callable, List


@dataclass
class Selection_Item:
    rel: str
    cond: str = ""
    python_cond: Callable = lambda x: True

def si(rel: str, cond: str="", python_cond = lambda x: True) -> Selection_Item:
    return Selection_Item(rel, cond=cond, python_cond=python_cond)

su = si('su')
ld = si('ld')
mod = si('mod')
obj1 = si('obj1')
pc = si('pc')
predc = si('predc')
predm = si('predm')
vc = si('vc')


def is_pred_pp_expression(node: SynTree) -> bool:
    yield_str = getyieldstr(node)
    result = yield_str in predicative_pp_expressions
    return result



defpron = """(@lemma="dit" or @lemma="dat" or @lemma="het")"""

tag_s_xpath = """
.//node[@pt="ww" and @rel="hd" 
       and parent::node[(@cat="sv1" or @cat="smain") and @rel="tag" ]
       ]
"""

synsel = {('doen', 'ww') : [[su, obj1], [su, vc], [su, si('mod', '@lemma="zo"')], [su, predc] ],
          ('gaan', 'ww') : [[su,vc], [su, ld], [su], [su, predc], [su, pc]],
          ('hebben', 'ww'): [[su, obj1], [su, vc], [su, si('svp', '@lemma="vrij"')]],
          ('kennen', 'ww'): [[su, obj1]],
          ('kijken', 'ww'): [[su], [su, ld], [su, pc], [su, vc]],
          ('kunnen', 'ww'): [[su, obj1], [su, vc], [su, ld], [su, mod], [su, pc]],
          ('moeten', 'ww'): [[su,vc], [su],[su, ld], [su, predc]],
          ('mogen', 'ww'): [[su], [su, ld]],
          ('uit_blazen', 'ww'): [[su, obj1]],
          ('weten', 'ww'): [[su, obj1], [su, vc], [su,pc]],
          ('willen', 'ww'): [[su, obj1], [su, vc], [su, ld], [su, mod]],
          ('zijn', 'ww'): [[su, predc], [su, pc], [su, vc], [su, ld],
                           [su, si('mod', '%new_STAP_BB_p%')], [su, predm],
                           [su, si('mod', '%new_STAP_BB_t% and ../node[@rel="hd" and @wvorm="vd"]')],
                           # ik ben nog een keer geweest, ik ben in januari geweest
                           [si('su', f'{defpron}'), si('mod', '@cat="cp"')],
                           [su, si('mod', python_cond = lambda x: is_pred_pp_expression(x))]],

}

parent_imperative_xpath = expandmacros('./parent::node[%basicimperative%]')

def extend_syns(syns, head) -> dict:
    head_wvorm = gav(head, 'wvorm')
    if head_wvorm not in  ['inf', 'vd']:
        return syns
    new_syns = copy.deepcopy(syns)
    for syn in syns:
        new_syn = [syn_item for syn_item in syn if syn_item != su]
        new_syns.append(new_syn)
    return new_syns




test_utts = [('vklstap', 'stap_02', '10'),
                ('vklstap', 'stap_02', '12'),
                ('vklstap', 'stap_02', '21'),
                ('vklstap', 'stap_02', '25'),
                ('vklstap', 'stap_02', '35'),
                ('vklstap', 'stap_02', '44')
            ]


def main():
    selected_test_utts = test_utts # [test_utts[5]]
    test_f(selected_test_utts, omitted_phrase)



if __name__ == '__main__':
    main()



