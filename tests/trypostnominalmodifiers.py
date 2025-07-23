from sastadev.postnominalmodifiers import transformppinnp
from lxml import etree
from sastadev.treebankfunctions import showtree, treeinflate

examples = [(1, """<alpino_ds version="1.3">
  <node begin="0" cat="top" end="4" id="0" rel="top">
    <node begin="0" cat="np" end="3" id="1" rel="--">
      <node begin="0" case="nom" def="def" end="1" frame="pronoun(nwh,fir,sg,de,nom,def)" gen="de" getal="ev" id="2" lcat="np" lemma="ik" naamval="nomin" num="sg" pdtype="pron" per="fir" persoon="1" pos="pron" postag="VNW(pers,pron,nomin,vol,1,ev)" pt="vnw" rel="hd" rnum="sg" root="ik" sense="ik" status="vol" vwtype="pers" wh="nwh" word="ik"/>
      <node begin="1" cat="pp" end="3" id="3" rel="mod">
        <node begin="1" end="2" frame="preposition(naar,[toe])" id="4" lcat="pp" lemma="naar" pos="prep" postag="VZ(init)" pt="vz" rel="hd" root="naar" sense="naar" vztype="init" word="naar"/>
        <node begin="2" end="3" frame="noun(both,both,both)" gen="both" genus="zijd" getal="ev" graad="basis" id="5" lcat="np" lemma="omie" naamval="stan" ntype="soort" num="both" pos="noun" postag="N(soort,ev,basis,zijd,stan)" pt="n" rel="obj1" rnum="sg" root="omie" sense="omie" word="omie"/>
      </node>
    </node>
    <node begin="3" end="4" frame="punct(punt)" id="6" lcat="punct" lemma="." pos="punct" postag="LET()" pt="let" rel="--" root="." sense="." special="punt" word="."/>
  </node>
  <sentence sentid="13">ik naar omie .</sentence>
<metadata>
<meta type="text" name="charencoding" value="UTF8" />
<meta type="text" name="childage" value="4;9" />
<meta type="int" name="childmonths" value="57" />
<meta type="text" name="comment" value="##META text title = TARSP_06" />
<meta type="text" name="session" value="TARSP_06" />
<meta type="text" name="origutt" value="ikke [: ik] naaw [: naar] omie ." />
<meta type="text" name="parsefile" value="Unknown_corpus_TARSP_06_u00000000013.xml" />
<meta type="text" name="speaker" value="CHI" />
<meta type="int" name="uttendlineno" value="32" />
<meta type="int" name="uttid" value="13" />
<meta type="int" name="uttstartlineno" value="32" />
<meta type="text" name="name" value="chi" />
<meta type="text" name="SES" value="" />
<meta type="text" name="age" value="4;9" />
<meta type="text" name="custom" value="" />
<meta type="text" name="education" value="" />
<meta type="text" name="group" value="" />
<meta type="text" name="language" value="nld" />
<meta type="int" name="months" value="57" />
<meta type="text" name="role" value="Target_Child" />
<meta type="text" name="sex" value="female" />
<meta type="text" name="xsid" value="13" />
<meta type="int" name="uttno" value="13" />
</metadata>
</alpino_ds>""")]

exampletrees = [(i, etree.fromstring(example)) for i, example in examples]

def main():
    for i, exampletree in exampletrees:
        newtree = transformppinnp(exampletree)
        showtree(newtree, 'newtree')



if __name__ == '__main__':
    main()