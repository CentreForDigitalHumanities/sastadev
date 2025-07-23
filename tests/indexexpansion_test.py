import os

import pytest
from lxml import etree

from sastadev.treebankfunctions import getstree, indextransform

bareindexnodexpath = './/node[@index and not(@cat) and not(@word)]'

streestrings = {}
streestrings[1] = """
<alpino_ds version="1.3" id="dpc-vla-001171-nl-sen.p.114.s.7">
  <node begin="0" cat="top" end="20" id="0" rel="top">
    <node begin="13" end="14" id="1" lemma="," pos="punct" postag="LET()" pt="let" rel="--" root="," word=","/>
    <node begin="0" cat="smain" end="19" id="2" rel="--">
      <node begin="0" cat="np" end="13" id="3" index="1" rel="su" highlight="yes">
        <node begin="0" end="1" id="4" lemma="het" lwtype="bep" naamval="stan" npagr="evon" pos="det" postag="LID(bep,stan,evon)" pt="lid" rel="det" root="het" word="Het" highlight="yes"/>
        <node begin="1" buiging="met-e" end="2" graad="basis" id="5" lemma="blauw-groen" naamval="stan" pos="adj" positie="prenom" postag="ADJ(prenom,basis,met-e,stan)" pt="adj" rel="mod" root="blauw_groen" word="blauw-groene" highlight="yes"/>
        <node begin="2" end="3" genus="onz" getal="ev" graad="basis" id="6" lemma="logo" naamval="stan" ntype="soort" pos="noun" postag="N(soort,ev,basis,onz,stan)" pt="n" rel="hd" root="logo" word="logo" highlight="yes"/>
        <node begin="3" cat="pp" end="6" id="7" rel="mod" highlight="yes">
          <node begin="3" end="4" id="8" lemma="met" pos="prep" postag="VZ(init)" pt="vz" rel="hd" root="met" vztype="init" word="met" highlight="yes"/>
          <node begin="4" cat="np" end="6" id="9" rel="obj1" highlight="yes">
            <node begin="4" end="5" id="10" lemma="de" lwtype="bep" naamval="stan" npagr="rest" pos="det" postag="LID(bep,stan,rest)" pt="lid" rel="det" root="de" word="de" highlight="yes"/>
            <node begin="5" end="6" id="11" lemma="N" pos="noun" postag="SPEC(meta)" pt="spec" rel="hd" root="N" spectype="meta" word="N" highlight="yes"/>
          </node>
        </node>
        <node begin="6" cat="rel" end="13" id="12" rel="mod" highlight="yes">
          <node begin="6" end="7" getal="ev" id="13" index="2" lemma="dat" naamval="stan" pdtype="pron" persoon="3" pos="pron" postag="VNW(betr,pron,stan,vol,3,ev)" pt="vnw" rel="rhd" root="dat" status="vol" vwtype="betr" word="dat" highlight="yes"/>
          <node begin="6" cat="ssub" end="13" id="14" rel="body" highlight="yes">
            <node begin="6" end="7" id="15" index="2" rel="obj1" highlight="yes"/>
            <node begin="7" cat="np" end="12" id="16" rel="su" highlight="yes">
              <node begin="7" buiging="met-e" end="8" id="17" lemma="al" naamval="stan" npagr="agr" pdtype="det" pos="det" positie="prenom" postag="VNW(onbep,det,stan,prenom,met-e,agr)" pt="vnw" rel="det" root="alle" vwtype="onbep" word="alle" highlight="yes"/>
              <node begin="8" buiging="met-e" end="9" graad="basis" id="18" lemma="Nederlandstalig" naamval="stan" pos="adj" positie="prenom" postag="ADJ(prenom,basis,met-e,stan)" pt="adj" rel="mod" root="Nederlandstalig" word="Nederlandstalige" highlight="yes"/>
              <node begin="9" end="10" getal="mv" graad="basis" id="19" lemma="school" ntype="soort" pos="noun" postag="N(soort,mv,basis)" pt="n" rel="hd" root="school" word="scholen" highlight="yes"/>
              <node begin="10" cat="pp" end="12" id="20" rel="mod" highlight="yes">
                <node begin="10" end="11" id="21" lemma="in" pos="prep" postag="VZ(init)" pt="vz" rel="hd" root="in" vztype="init" word="in" highlight="yes"/>
                <node begin="11" end="12" genus="onz" getal="ev" graad="basis" id="22" lemma="Brussel" naamval="stan" ntype="eigen" pos="name" postag="N(eigen,ev,basis,onz,stan)" pt="n" rel="obj1" root="Brussel" word="Brussel" highlight="yes"/>
              </node>
            </node>
            <node begin="12" end="13" id="23" lemma="dragen" pos="verb" postag="WW(pv,tgw,mv)" pt="ww" pvagr="mv" pvtijd="tgw" rel="hd" root="draag" word="dragen" wvorm="pv" highlight="yes"/>
          </node>
        </node>
      </node>
      <node begin="14" end="15" id="24" lemma="zijn" pos="verb" postag="WW(pv,tgw,ev)" pt="ww" pvagr="ev" pvtijd="tgw" rel="hd" root="ben" word="is" wvorm="pv"/>
      <node begin="0" cat="ppart" end="19" id="25" rel="vc">
        <node begin="0" end="13" id="26" index="1" rel="su"/>
        <node begin="15" buiging="zonder" end="16" id="27" lemma="uitgroeien" pos="verb" positie="vrij" postag="WW(vd,vrij,zonder)" pt="ww" rel="hd" root="groei_uit" word="uitgegroeid" wvorm="vd"/>
        <node begin="16" cat="pp" end="19" id="28" rel="pc">
          <node begin="16" end="17" id="29" lemma="tot" pos="prep" postag="VZ(init)" pt="vz" rel="hd" root="tot" vztype="init" word="tot"/>
          <node begin="17" cat="np" end="19" id="30" rel="obj1">
            <node begin="17" end="18" id="31" lemma="een" lwtype="onbep" naamval="stan" npagr="agr" pos="det" postag="LID(onbep,stan,agr)" pt="lid" rel="det" root="een" word="een"/>
            <node begin="18" end="19" genus="onz" getal="ev" graad="basis" id="32" lemma="kwaliteitslabel" naamval="stan" ntype="soort" pos="noun" postag="N(soort,ev,basis,onz,stan)" pt="n" rel="hd" root="kwaliteitslabel" word="kwaliteitslabel"/>
          </node>
        </node>
      </node>
    </node>
    <node begin="19" end="20" id="33" lemma="." pos="punct" postag="LET()" pt="let" rel="--" root="." word="."/>
  </node>
  <sentence>Het blauw-groene logo met de N dat alle Nederlandstalige scholen in Brussel dragen , is uitgegroeid tot een kwaliteitslabel .</sentence>
  <comments>
    <comment>Q#dpc-vla-001171-nl-sen.p.114.s.7|Het blauw-groene logo met de N dat alle Nederlandstalige scholen in Brussel dragen , is uitgegroeid tot een kwaliteitslabel .|</comment>
  </comments>
</alpino_ds>
"""

strees = {i: etree.fromstring(streestrings[i]) for i in streestrings}


@pytest.mark.skip(reason='test code does not work')
def test():
    for i in strees:
        idxnodes = strees[i].xpath(bareindexnodexpath)
        if idxnodes == []:
            print('No bare index nodes in tree {i}')
        # newtree = newindextransform(strees[i])
        newtree = indextransform(strees[i])
        etree.dump(newtree)


def testwholelassy():
    lassykleinpath = r'D:\Dropbox\various\Resources\LASSY\LASSY-Klein\Lassy-Klein\Treebank'
    for root, dirs, files in os.walk(lassykleinpath):
        print(f'Processing {root}...')
        for filename in files:
            base, ext = os.path.splitext(filename)
            if ext == '.xml':
                fullname = os.path.join(root, filename)
                fullstree = getstree(fullname)
                stree = fullstree.getroot()
                expansion = indextransform(stree)
                if expansion.xpath(bareindexnodexpath) != []:
                    print(fullname)
                    etree.dump(stree)
                    etree.dump(expansion)


def main():
    test()
    # testwholelassy()


if __name__ == '__main__':
    main()
