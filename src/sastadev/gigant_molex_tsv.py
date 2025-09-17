"""
This module reads in the gigant molex tsv file, just for a check on the existence of words.
It puts all single word inflected forms as a key in the python dictionary gigant_molex_dict and appends the full
record to the value

A gigant-molex record is assumed to contain the following fields:

lemma_id
lemma
lemma_features
inflected_from_id
inflected_form
inflected_form_features

(cf. the readme file:

Het tsv bestand heeft de volgende kolommen:
Lemma id
Lemma
Lemmawoordsoort
Woordvorm id
Woordvorm
Woordvormwoordsoort

If an inflected form consists of multiple words, each individual word is included as key in the dictionary
"""
from collections import defaultdict
from sastadev.readcsv import readcsv
import os

gigant_molex_filename = 'molex_22_02_2022.tsv'
gigant_molex_path = r"D:\Dropbox\various\Resources\Gigant-Molex\V2.0\GiGaNT-Molex_2.0\GiGaNT-Molex2.0\Data" \
                    r"\molex_22_02_2022.tsv"   # must be replaced by the final value ./data/lexicons/gigant_molex/tsv

gigant_molex_fullname = os.path.join(gigant_molex_path, gigant_molex_filename)

data = readcsv(gigant_molex_fullname, header=False)

gigant_molex_dict = defaultdict(list)
for row in data:
    full_infl_form = row[3]
    infl_forms = full_infl_form.split()
    for infl_form in infl_forms:
        gigant_molex_dict[infl_form].append(row)

junk = 0    # for debug purposes
