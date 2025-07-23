.. _lexicons:

Lexicons
========

SASTA uses a range of lexicons. We will briefly describe these here.

.. _Alpinolexicon:

Alpinolexicon
-------------
The Alpinolexicon is used inside Alpino. This lexicon is not just a list of words with their properties but has a more complex structure and also contains rules to deal with systematic cases, programmed in Prolog. This makes it less usable outside of Alpino.

The predicate ‘is contained in the Alpino-lexicon’ is also not easy to define. One can only do this by parsing the relevant word. But Alpino will come back with a word analysed as a compound if it can analyse it as a compound, even if it is not listed as such in the Alpino lexicon, and the difference cannot be seen. The properties that a word will get in the parse are also in part dependent on the context in which it occurs. For example, a verb may have many frame options but will have only one left in a particular utterance.

Gertjan van Noord wrote to me about this::

	als je Alpino hebt, gaat het zo
	 
	Alpino
	p lex_all
	 
	en nu kun je per regel een zin (of een woord) ingeven. Alpino toont vervolgens alle categorieën die het woord heeft gekregen. Vb:
	 
	1 |: p lex_all
	1 |: de autootje
	[... debug info ...]
	TAG#0|1|de|determiner(de)|normal(normal)|de|0.0
	TAG#1|2|autootje|noun(het,count,sg)|diminutive|auto_DIM|0.6931471805599453
	TAG#1|2|autootje|noun(het,count,sg)|normal(normal)|auto_DIM|0.6931471805599453
	 
	de regels die met TAG beginnen zijn relevant. En die hebben velden, gescheiden door | veld 4 is de woordsoort, veld 5 is de naam van de heuristiek die is gebruikt. Als die naam met 'normal(' begint, zou je kunnen zeggen dat het woord gewoon in het woordenboek staat.

.. _CELEX:

CELEX
-----
The lexicon that we use most is CELEX. There is a module lexicon.py which provides the interface to the lexion actually used:

.. automodule:: sastadev.lexicon

But in it the actual lexicon used is the CELEX lexicon, taken care of by the celexlexicon module:

.. automodule:: sastadev.celexlexicon

.. _top3000:

Top3000
-------

.. automodule:: sastadev.top3000

.. _namelexicons:

Name lexicons
-------------

Names very often consist of multiple words.
For individual words it is therefore important to check whether they can be a part of a (possibly multiword) name.
The relevant module is the namepartlexicon module.

.. automodule:: sastadev.namepartlexicon

 
.. _filledpauseslexicon:

Filled pauses lexicon
---------------------

The filledpauseslexicon is a set created in the module dedup on the basis of the file filledpauseslexicon/filledpauseslexicon.txt in the code folder.

This file has been created by searching for strings marked with & in the Dutch CHILDES corpora (with the script getchildes.py), and manual filtering.


.. _compounds:

Compounds
---------

.. automodule:: sastadev.compounds

.. _exceptionslists:

Exception Lists
--------------- 

There are several  lists of words in SASTA for a variety of reasons. 
At the moment they are distributed over multiple files. But it would be a good idea to put them all together in  a single module.
We will call this module (that does not exist yet) exceptionlists.py.
