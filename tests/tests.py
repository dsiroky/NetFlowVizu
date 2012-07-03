#! -*- coding: utf-8 -*-
"""
@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt or 
          U{http://www.opensource.org/licenses/mit-license.php})
"""

import unittest

import net_flow_vizu_dia

#############################################################################
#############################################################################

class Test(unittest.TestCase):
    def test(self):
        f = open("../data_example.yaml", "rb")
        data = f.read()
        f.close()
        net_flow_vizu_dia.DiaConvertor(data).convert()

    #def test_diacritics(self):
    #    f = open("data_diacritics.yaml", "rb")
    #    data = f.read()
    #    f.close()
    #    net_flow_vizu_dia.DiaConvertor(data).convert()
