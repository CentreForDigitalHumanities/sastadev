'''
The external_functions module creates the link between a function mentioned in the language measures and the python programme.
A function mentioned in a pre or core language measure takes as input a syntactic structure and
yields a list of nodes  as output.

A function mentioned in a post or form query takes as input an AllResults object and a
syntactic structure and yields  a result of any type as output.

If the function is defined in some other module, it must be imported here.
The name of the function must be added to one of the variables
*thetarspfunctions*, *thestapfunctions*, or *theastafunctions*, depending on the method that it belongs to.

'''

import re
from typing import Callable, Dict

from sastadev.allresults import QueryFunction
from sastadev.asta_queries import (asta_bijzin, asta_dellid, asta_delpv, asta_lemma,
                                   asta_lex, asta_noun, astalemmafunction, asta_xxx)
from sastadev.astaforms import astaform
from sastadev.ASTApostfunctions import (KMcount, countwordsandcutoff,
                                        finietheidsindex, getalllemmas,
                                        getlexlemmas, getnounlemmas,
                                        neologisme, phonpar, sempar,
                                        wordcountperutt)
from sastadev.compounds import getcompounds
from sastadev.dedup import correct, mlux, onvolledig, samplesize
from sastadev.imperatives import bbx, wond4, wond5plus, wondx, wx, wxy, wxyz, wxyz5
from sastadev.methods import allok, astalemmafilter
from sastadev.missing_det import get_missing_det
from sastadev.queryfunctions import (adj_agreement_errors, bx, congruentiefout,
                                     dan_toen_fout, del_bw, del_er, del_vg, del_vz,
                                     VzN, false_start, get_avn, get_pronunciation_variants, hequery,
                                     hoofdww_weg, into,
                                     no_copula, omitted_phrase, pv_regionale_vorm, pv_t_elisions,
                                     repetition, self_correction, sociolect,
                                     stam, sublid, stap_congruentiefout, stap_sublid,
                                     sub_bw, sub_lexical, sub_vnw, sub_tijd, sub_vg, sub_vz,
                                     tarsp_dellid, tarsp_mvzn, tarsp_sublid,  tarsp_verkl,
                                     topic_drop, verb_no_pv,
                                     vobij, voslashbij, vd_fout, vt_fout, vudivers, xneg_neg,
                                     xneg_x)
from sastadev.stapforms import makestapform
from sastadev.STAPpostfunctions import (GL5LVU, GLVU, BB_totaal, congruentie_fouten_count,
                                        hoofdww_weg_count, vt_fout_count,
                                        vd_fout_count, del_nmwg_count, bepaler_weg_count, bepaler_verkeerd_count,
                                        ov_uiting_count)
from sastadev.Sziplus import sziplus6, vr5plus
from sastadev.tarspform import mktarspform
from sastadev.TARSPpostfunctions import (gofase, gtotaal, mk_toelichting, pf, pf2, pf3, pf4,
                                         pf5, pf6, pf7, vutotaal)
from sastadev.TARSPscreening import tarsp_screening
from sastadev.xenx import xenx

normalfunctionpattern = r'<function\s+(\w+)\b'
builtinfunctionpattern = r'<built-in function\s+(\w+)\b'


# normalfunctionprefix = "<function "
# lnormalfunctionprefix = len(normalfunctionprefix)
# builtinfunctionprefix = "<built-in function "
# lbuiltinfunctionprefix = len(builtinfunctionprefix)

def getfname(f: Callable) -> str:
    return f.__name__


def oldgetfname(f: Callable) -> str:
    fstr = str(f)
    m = re.match(normalfunctionpattern, fstr)
    if m is not None:
        result = m.group(1)
    else:
        m = re.match(builtinfunctionpattern, fstr)
        if m is not None:
            result = m.group(1)
        else:
            result = ''
    return result


# Initialisation
thetarspfunctions = [bx, bbx, congruentiefout, del_vz, get_avn, get_missing_det, getcompounds, hequery,
                     into, sziplus6, xenx, vr5plus, wx, wxy, wxyz, wxyz5, wondx, wond4, wond5plus,
                     tarsp_screening, vutotaal, gofase, gtotaal, mk_toelichting, pf2, pf3, pf4, pf5, pf6, pf7, pf,
                     pv_regionale_vorm,
                     xneg_x, xneg_neg,
                     mktarspform, stam, sub_vz, tarsp_sublid, tarsp_dellid,
                     tarsp_mvzn, tarsp_verkl, VzN, vobij, voslashbij,vd_fout, vt_fout, vudivers, ov_uiting_count]

thestapfunctions = [adj_agreement_errors, BB_totaal, stap_congruentiefout,
                    dan_toen_fout, del_bw, del_er, del_vg, del_vz, false_start,
                    get_missing_det, get_pronunciation_variants, GLVU, GL5LVU,
                    hoofdww_weg, makestapform,  no_copula,
                    omitted_phrase, pv_t_elisions, repetition, self_correction, sociolect,
                    stap_sublid, sub_bw, sub_lexical, sub_vnw, sub_tijd, sub_vg, sub_vz,
                    topic_drop, vd_fout, verb_no_pv, vt_fout, congruentie_fouten_count, vt_fout_count,
                                        vd_fout_count, del_nmwg_count, bepaler_weg_count,
                    bepaler_verkeerd_count, hoofdww_weg_count]

theastafunctions = [samplesize, mlux, neologisme, onvolledig, correct, wordcountperutt, countwordsandcutoff,
                    astaform, KMcount, finietheidsindex, getnounlemmas, getlexlemmas, getalllemmas, asta_noun,
                    asta_bijzin, asta_lex, asta_delpv, asta_xxx, allok, pv_regionale_vorm, sempar, phonpar,
                    astalemmafilter, asta_lemma, adj_agreement_errors,
                    astalemmafunction, asta_dellid, sublid, congruentiefout]

thefunctions = thetarspfunctions + thestapfunctions + theastafunctions

str2functionmap: Dict[str, QueryFunction] = {}

for f in thefunctions:
    fname = getfname(f)
    str2functionmap[fname] = f

# Used by SASTA to find form functions
form_map: Dict[str, Callable] = {
    'TARSP': mktarspform,
    'ASTA': astaform,
    'STAP': makestapform
}
