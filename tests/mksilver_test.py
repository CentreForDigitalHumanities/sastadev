import os

import pytest

from sastadev import methodinfo
from sastadev.constants import (checkeditedsuffix, checksuffix, permprefix,
                                platinumeditedsuffix, platinumsuffix)
from sastadev.mksilver import getsilverannotations


@pytest.mark.skip(reason='test code does not work')
def test_mksilver():
    methodnames = ['ASTA', 'TARSP', 'STAP']
    for methodname in methodnames:
        methodpath = methodinfo.knownmethods[methodname].path
        for i in range(1, 11):
            istr = str(i).rjust(2, '0')
            basename = methodinfo.knownmethods[methodname].basenamemodel.format(
                istr)

            perm_silverfilename = permprefix + \
                methodinfo.knownmethods[methodname].silvertemplate.format(
                    basename) + '.xlsx'
            perm_silverfullname = os.path.join(
                methodinfo.knownmethods[methodname].silverpath, perm_silverfilename)

            platinumcheckeditedfilename = basename + checkeditedsuffix + '.xlsx'
            platinumcheckeditedfullname = os.path.join(
                methodpath, platinumcheckeditedfilename)

            platinumcheckfilename = basename + checksuffix + '.xlsx'
            platinumcheckfullname = os.path.join(
                methodpath, platinumcheckfilename)

            silvercheckfilename = basename + checksuffix + '.xlsx'
            silvercheckfullname = os.path.join(methodpath, silvercheckfilename)

            platinumfilename = basename + platinumsuffix + '.txt'
            platinumfullname = os.path.join(methodpath, platinumfilename)

            platinumeditedfilename = basename + platinumeditedsuffix + '.txt'
            platinumeditedfullname = os.path.join(
                methodpath, platinumeditedfilename)

            silverannotationsdict = getsilverannotations(perm_silverfullname, platinumcheckeditedfullname,
                                                         platinumcheckfullname, silvercheckfullname,
                                                         platinumfullname, platinumeditedfullname)
