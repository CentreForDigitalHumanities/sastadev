from lxml import etree

from sastadev.queryfunctions import vobij, voslashbij

# find the cases written separately


streestrings = {}
streestrings[1] = """
  <alpino_ds version="1.3">
  <metadata>
<meta type="text" name="charencoding" value="UTF8"/>
<meta type="text" name="childage" value="4;6"/>
<meta type="int" name="childmonths" value="54"/>
<meta type="text" name="comment" value="##META text title = Tarsp_01"/>
<meta type="text" name="session" value="Tarsp_01"/>
<meta type="text" name="origutt" value="allemaal varkens zit erin. "/>
<meta type="text" name="parsefile" value="Unknown_corpus_Tarsp_01_u00000000001.xml"/>
<meta type="text" name="speaker" value="CHI"/>
<meta type="int" name="uttendlineno" value="8"/>
<meta type="int" name="uttid" value="1"/>
<meta type="int" name="uttstartlineno" value="8"/>
<meta type="text" name="name" value="chi"/>
<meta type="text" name="SES" value=""/>
<meta type="text" name="age" value="4;6"/>
<meta type="text" name="custom" value=""/>
<meta type="text" name="education" value=""/>
<meta type="text" name="group" value=""/>
<meta type="text" name="language" value="nld"/>
<meta type="int" name="months" value="54"/>
<meta type="text" name="role" value="Target_Child"/>
<meta type="text" name="sex" value="male"/>
<meta type="text" name="xsid" value="1"/>
<meta type="int" name="uttno" value="1"/>
<xmeta name="tokenisation" atype="list" annotationwordlist="['allemaal', 'varkens', 'zit', 'erin', '.']" annotationposlist="[]" annotatedwordlist="[]" annotatedposlist="[]" value="['allemaal', 'varkens', 'zit', 'erin', '.']" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/><xmeta name="cleanedtokenisation" atype="list" annotationwordlist="['allemaal', 'varkens', 'zit', 'erin', '.']" annotationposlist="[]" annotatedwordlist="[]" annotatedposlist="[]" value="['allemaal', 'varkens', 'zit', 'erin', '.']" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/><xmeta name="cleanedtokenpositions" atype="list" annotationwordlist="[10, 20, 30, 40, 50]" annotationposlist="[10, 20, 30, 40, 50]" annotatedwordlist="[]" annotatedposlist="[]" value="[10, 20, 30, 40, 50]" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/></metadata>
<node begin="10" cat="top" end="51" id="0" rel="top">
    <node begin="10" cat="du" end="41" id="1" rel="--">
      <node begin="10" cat="du" end="21" id="2" rel="dp">
        <node begin="10" end="11" frame="predm_adverb" id="3" lcat="advp" lemma="allemaal" pos="adv" postag="BW()" pt="bw" rel="dp" root="allemaal" sense="allemaal" special="predm" word="allemaal"/>
        <node begin="20" end="21" frame="noun(het,count,pl)" gen="het" getal="mv" graad="basis" id="4" lcat="np" lemma="varken" ntype="soort" num="pl" pos="noun" postag="N(soort,mv,basis)" pt="n" rel="dp" rnum="pl" root="varken" sense="varken" word="varkens"/>
      </node>
      <node begin="30" cat="sv1" end="41" id="5" rel="dp">
        <node begin="30" end="31" frame="verb(hebben,sg,ld_pp)" id="6" infl="sg" lcat="sv1" lemma="zitten" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="zit" sc="ld_pp" sense="zit" stype="topic_drop" tense="present" word="zit" wvorm="pv"/>
        <node begin="40" end="41" frame="er_adverb(in)" id="7" lcat="pp" lemma="erin" pos="pp" postag="BW()" pt="bw" rel="ld" root="erin" sense="erin" special="er" word="erin"/>
      </node>
    </node>
    <node begin="50" end="51" frame="punct(punt)" id="8" lcat="--" lemma="." pos="punct" postag="LET()" pt="let" rel="--" root="." sense="." special="punt" word="."/>
  </node>
  <sentence sentid="1">allemaal varkens zit erin .</sentence></alpino_ds>

"""
streestrings[2] = """
<alpino_ds version="1.3">
  <metadata>
<meta type="text" name="charencoding" value="UTF8"/>
<meta type="text" name="childage" value="5;8"/>
<meta type="int" name="childmonths" value="68"/>
<meta type="text" name="comment" value="##META text title = Tarsp_05"/>
<meta type="text" name="session" value="Tarsp_05"/>
<meta type="text" name="origutt" value="die kan d(e)r op weer."/>
<meta type="text" name="parsefile" value="Unknown_corpus_Tarsp_05_u00000000037.xml"/>
<meta type="text" name="speaker" value="CHI"/>
<meta type="int" name="uttendlineno" value="80"/>
<meta type="int" name="uttid" value="37"/>
<meta type="int" name="uttstartlineno" value="80"/>
<meta type="text" name="name" value="chi"/>
<meta type="text" name="SES" value=""/>
<meta type="text" name="age" value="5;8"/>
<meta type="text" name="custom" value=""/>
<meta type="text" name="education" value=""/>
<meta type="text" name="group" value=""/>
<meta type="text" name="language" value="nld"/>
<meta type="int" name="months" value="68"/>
<meta type="text" name="role" value="Target_Child"/>
<meta type="text" name="sex" value="female"/>
<meta type="text" name="xsid" value="37"/>
<meta type="int" name="uttno" value="37"/>
<xmeta name="Noncompletion of a Word" atype="text" annotationwordlist="['(e)']" annotationposlist="[]" annotatedwordlist="[]" annotatedposlist="[]" value="['(e)']" cat="None" subcat="None" source="None" backplacement="0" penalty="10"/><xmeta name="tokenisation" atype="list" annotationwordlist="['die', 'kan', 'd(e)r', 'op', 'weer', '.']" annotationposlist="[]" annotatedwordlist="[]" annotatedposlist="[]" value="['die', 'kan', 'd(e)r', 'op', 'weer', '.']" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/><xmeta name="cleanedtokenisation" atype="list" annotationwordlist="['die', 'kan', 'der', 'op', 'weer', '.']" annotationposlist="[]" annotatedwordlist="[]" annotatedposlist="[]" value="['die', 'kan', 'der', 'op', 'weer', '.']" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/><xmeta name="cleanedtokenpositions" atype="list" annotationwordlist="[10, 20, 30, 40, 50, 60]" annotationposlist="[10, 20, 30, 40, 50, 60]" annotatedwordlist="[]" annotatedposlist="[]" value="[10, 20, 30, 40, 50, 60]" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/></metadata>
<node begin="10" cat="top" end="61" id="0" rel="top">
    <node begin="10" cat="smain" end="51" id="1" rel="--">
      <node begin="10" end="11" frame="determiner(de,nwh,nmod,pro,nparg)" getal="getal" id="2" infl="de" lcat="np" lemma="die" naamval="stan" pdtype="pron" persoon="3" pos="det" postag="VNW(aanw,pron,stan,vol,3,getal)" pt="vnw" rel="su" rnum="sg" root="die" sense="die" status="vol" vwtype="aanw" wh="nwh" word="die"/>
      <node begin="20" end="21" frame="verb(hebben,modal_not_u,ld_pp)" id="3" infl="modal_not_u" lcat="smain" lemma="kunnen" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="kan" sc="ld_pp" sense="kan" stype="declarative" tense="present" word="kan" wvorm="pv"/>
      <node begin="30" cat="pp" end="41" id="4" rel="ld">
        <node begin="30" end="31" frame="er_vp_adverb" getal="getal" id="5" lcat="advp" lemma="er" naamval="stan" pdtype="adv-pron" persoon="3" pos="adv" postag="VNW(aanw,adv-pron,stan,red,3,getal)" pt="vnw" rel="obj1" root="er" sense="er" special="er" status="red" vwtype="aanw" word="der"/>
        <node begin="40" end="41" frame="preposition(op,[af,na])" id="6" lcat="pp" lemma="op" pos="prep" postag="VZ(fin)" pt="vz" rel="hd" root="op" sense="op" vztype="fin" word="op"/>
      </node>
      <node begin="50" end="51" frame="adverb" id="7" lcat="advp" lemma="weer" pos="adv" postag="BW()" pt="bw" rel="mod" root="weer" sense="weer" word="weer"/>
    </node>
    <node begin="60" end="61" frame="punct(punt)" id="8" lcat="punct" lemma="." pos="punct" postag="LET()" pt="let" rel="--" root="." sense="." special="punt" word="."/>
  </node>
  <sentence sentid="37">die kan der op weer .</sentence></alpino_ds>
"""
streestrings[3] = """
  <alpino_ds version="1.3">
  <metadata>
<meta type="text" name="charencoding" value="UTF8"/>
<meta type="text" name="childage" value="5;2"/>
<meta type="int" name="childmonths" value="62"/>
<meta type="text" name="comment" value="##META text title = Tarsp_04"/>
<meta type="text" name="session" value="Tarsp_04"/>
<meta type="text" name="origutt" value="die [: daar] heb wij ook een boekje van"/>
<meta type="text" name="parsefile" value="Unknown_corpus_Tarsp_04_u00000000002.xml"/>
<meta type="text" name="speaker" value="CHI"/>
<meta type="int" name="uttendlineno" value="10"/>
<meta type="int" name="uttid" value="2"/>
<meta type="int" name="uttstartlineno" value="10"/>
<meta type="text" name="name" value="chi"/>
<meta type="text" name="SES" value=""/>
<meta type="text" name="age" value="5;2"/>
<meta type="text" name="custom" value=""/>
<meta type="text" name="education" value=""/>
<meta type="text" name="group" value=""/>
<meta type="text" name="language" value="nld"/>
<meta type="int" name="months" value="62"/>
<meta type="text" name="role" value="Target_Child"/>
<meta type="text" name="sex" value="female"/>
<meta type="text" name="xsid" value="2"/>
<meta type="int" name="uttno" value="2"/>
<xmeta name="GrammarError" atype="text" annotationwordlist="['hebben']" annotationposlist="[50]" annotatedwordlist="['heb']" annotatedposlist="[50]" value="SVAerror" cat="Error" subcat="None" source="SASTA" backplacement="2" penalty="10"/><xmeta name="Replacement" atype="text" annotationwordlist="['daar']" annotationposlist="[30]" annotatedwordlist="['die']" annotatedposlist="[10]" value="['daar']" cat="None" subcat="None" source="CHAT" backplacement="0" penalty="10"/><xmeta name="tokenisation" atype="list" annotationwordlist="['die', '[: ', 'daar', ']', 'heb', 'wij', 'ook', 'een', 'boekje', 'van']" annotationposlist="[]" annotatedwordlist="[]" annotatedposlist="[]" value="['die', '[: ', 'daar', ']', 'heb', 'wij', 'ook', 'een', 'boekje', 'van']" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/><xmeta name="cleanedtokenisation" atype="list" annotationwordlist="['daar', 'heb', 'wij', 'ook', 'een', 'boekje', 'van']" annotationposlist="[]" annotatedwordlist="[]" annotatedposlist="[]" value="['daar', 'heb', 'wij', 'ook', 'een', 'boekje', 'van']" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/><xmeta name="cleanedtokenpositions" atype="list" annotationwordlist="[30, 50, 60, 70, 80, 90, 100]" annotationposlist="[30, 50, 60, 70, 80, 90, 100]" annotatedwordlist="[]" annotatedposlist="[]" value="[30, 50, 60, 70, 80, 90, 100]" cat="None" subcat="None" source="CHAT/Tokenisation" backplacement="0" penalty="10"/><xmeta name="parsed_as" atype="text" annotationwordlist="daar hebben wij ook een boekje van" annotationposlist="[]" annotatedwordlist="[]" annotatedposlist="[]" value="daar hebben wij ook een boekje van" cat="Correction" subcat="None" source="SASTA" backplacement="0" penalty="0"/></metadata>
<node begin="30" cat="top" end="101" id="0" rel="top">
    <node begin="30" cat="smain" end="101" id="1" rel="--">
      <node begin="50" end="51" frame="verb(hebben,sg1,transitive_ndev)" id="1" infl="sg1" lcat="--" lemma="hebben" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="heb" sc="transitive_ndev" sense="heb" tense="present" word="heb" wvorm="pv"/>
    <node begin="60" case="nom" def="def" end="61" frame="pronoun(nwh,fir,pl,de,nom,def)" gen="de" getal="mv" id="3" lcat="np" lemma="wij" naamval="nomin" num="pl" pdtype="pron" per="fir" persoon="1" pos="pron" postag="VNW(pers,pron,nomin,vol,1,mv)" pt="vnw" rel="su" rnum="pl" root="wij" sense="wij" status="vol" vwtype="pers" wh="nwh" word="wij"/>
      <node begin="70" end="71" frame="sentence_adverb" id="4" lcat="advp" lemma="ook" pos="adv" postag="BW()" pt="bw" rel="mod" root="ook" sense="ook" special="sentence" word="ook"/>
      <node begin="80" cat="np" end="91" id="5" rel="obj1">
        <node begin="80" end="81" frame="determiner(een)" id="6" infl="een" lcat="detp" lemma="een" lwtype="onbep" naamval="stan" npagr="agr" pos="det" postag="LID(onbep,stan,agr)" pt="lid" rel="det" root="een" sense="een" word="een"/>
        <node begin="90" end="91" frame="noun(het,count,sg)" gen="het" genus="onz" getal="ev" graad="dim" id="7" lcat="np" lemma="boek" naamval="stan" ntype="soort" num="sg" pos="noun" postag="N(soort,ev,dim,onz,stan)" pt="n" rel="hd" rnum="sg" root="boek_DIM" sense="boek_DIM" word="boekje"/>
      </node>
      <node begin="30" cat="pp" end="101" id="8" rel="pc">
        <node begin="30" end="31" frame="er_loc_adverb" getal="getal" id="9" lcat="advp" lemma="daar" naamval="obl" pdtype="adv-pron" persoon="3o" pos="adv" postag="VNW(aanw,adv-pron,obl,vol,3o,getal)" pt="vnw" rel="obj1" root="daar" sense="daar" special="er_loc" status="vol" vwtype="aanw" word="daar"/>
        <node begin="100" end="101" frame="preposition(van,[af,uit,vandaan,[af,aan]])" id="10" lcat="pp" lemma="van" pos="prep" postag="VZ(fin)" pt="vz" rel="hd" root="van" sense="van" vztype="fin" word="van"/>
      </node>
    </node>
  </node>
  <sentence sentid="2">daar heb wij ook een boekje van</sentence><comments>
    <comment>Q#ng1664379677|daar hebben wij ook een boekje van|1|1|-3.187513080109999</comment>
  </comments>
</alpino_ds>

"""

strees = {i: etree.fromstring(ts) for i, ts in streestrings.items()}

# reference dictionary contains tuples with (1) VoBij reference results; (2) Voslashbij reference results
reference = {}
reference[1] = (['40'], [])
reference[2] = (['30'], [])
reference[3] = ([], ['30'])


def test():
    for i, stree in strees.items():
        results = [n.attrib['begin'] for n in vobij(stree)]
        try:
            assert results == reference[i][0]
        except AssertionError as e:
            print(
                f'Vobij: i={i}, reference={reference[i][0]}, =/= results={results}')
            raise AssertionError

        results = [n.attrib['begin'] for n in voslashbij(stree)]
        try:
            assert results == reference[i][1]
        except AssertionError as e:
            print(
                f'Vo/bij: i={i}, reference={reference[i][1]}, =/= results={results}')
            raise AssertionError


def main():
    # define tests
    test()


if __name__ == '__main__':
    main()
