"""
contains constants that are needed for queries, especially for macros and special functions
"""



Tarsp_kijkVU1 = """(@pt="ww" and @lemma="kijken" and (( @wvorm="pv" and @pvagr="ev" and @pvtijd="tgw") 
 or @word = "kij") and not(../node[@rel="vc" or @rel="su" or @cat="pp" or @pt="bw"])) """
Tarsp_kijkVU2 = """(@lemma = "kijk" and (@pt="n" or @pt="bw")) """
Tarsp_kijkVU3 = """(@pt="ww" and @lemma="kijken" and @wvorm="pv" and @pvagr="ev" and @pvtijd="tgw" and ../node[@rel="mod" and (@lemma="eens" or @lemma="hier" or @lemma="daar")] and 
                   (parent::node[count(node) = 2] or (parent::node[count(node) = 3] and ../node[@rel="obj1"]))  
				   ) """
Tarsp_kijkVU = f"""({Tarsp_kijkVU1} or {Tarsp_kijkVU2} or {Tarsp_kijkVU3})"""

