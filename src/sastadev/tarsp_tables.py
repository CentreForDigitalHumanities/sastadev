from collections import defaultdict
import os
from sastadev.CHILDES_age import CHILDESAge, childes_age_from_string, normalise_age
from sastadev.conf import settings
from sastadev.constants import datafolder
from sastadev.xlsx import getxlsxdata
from typing import Callable, List, Optional, Tuple

girl = 'meisje'
boy = 'jongen'

tarsp_tabellen_folder = 'tarsp_tabellen'
tarsp_tabellen_path = os.path.join(settings.SD_DIR, datafolder, tarsp_tabellen_folder)
gzw_by_stage_filename = 'gzw_by_stage.xlsx'
gzw_by_stage_fullname = os.path.join(tarsp_tabellen_path, gzw_by_stage_filename)
header, data = getxlsxdata(gzw_by_stage_fullname)
gzw_by_stage = {}
for row in data:
    gzw_by_stage[row[0]] = row

gzw_by_age_filename = 'gzw_by_age.xlsx'
gzw_by_age_fullname = os.path.join(tarsp_tabellen_path, gzw_by_age_filename)
header, data = getxlsxdata(gzw_by_age_fullname)
gzw_by_age = {}
for row in data:
    gzw_by_age[(row[0], row[1])] =row

norm_tabel_1_filename = 'Tarsp_Norm_Table_1_1-4.xlsx'
norm_tabel_1_fullname = os.path.join(tarsp_tabellen_path, norm_tabel_1_filename)
header, norm_tabel_1_data = getxlsxdata(norm_tabel_1_fullname)
norm_tabel_1 = defaultdict(list)
norm_tabel_1_by_stage = defaultdict(list)
for row in norm_tabel_1_data:
    norm_tabel_1[row[0]].append(row)
    norm_tabel_1_by_stage[row[5]].append(row)

norm_tabel_2_filename = 'Tarsp_Norm_Table_2_1-4.xlsx'
norm_tabel_2_fullname = os.path.join(tarsp_tabellen_path, norm_tabel_1_filename)
header, norm_tabel_2_data = getxlsxdata(norm_tabel_2_fullname)
norm_tabel_2 = defaultdict(list)
for row in norm_tabel_2_data:
    norm_tabel_2[row[0]].append(row)



max_z = 2
def compare_with_norm_by_stage(gzw, stage) -> Optional[Tuple[float, float]]:
    if stage in gzw_by_stage:
        norm_row = gzw_by_stage[stage]
        diff = gzw - norm_row[2]
        sd = norm_row[3]
        z = diff / sd
        return diff, z
    else:
        return None

def compare_with_norm_by_age(gzw, age) -> Optional[Tuple[float, float]]:
    norm_data = gzw_by_age
    norm_row = None
    ch_age = childes_age_from_string(age)
    for b, e in norm_data:
        ch_b = childes_age_from_string(b)
        ch_e = childes_age_from_string(e)
        if ch_age >= ch_b and ch_age <= ch_e:
            norm_row = gzw_by_age[(b,e)]
            break
    if norm_row is not None:
        diff = gzw - norm_row[2]
        sd = norm_row[3]
        z = diff / sd
        return diff, z
    else:
        return None



