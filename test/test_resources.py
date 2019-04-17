# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 3 of the License, or
     (at your option) any later version.

"""

__author__ = 'mathracinne@gmail.com'
__date__ = '2019-03-25'
__copyright__ = 'Copyright 2019, Mathis RACINNE-DIVET, IRISA, Université Bretagne Sud'

import unittest

from PyQt5.QtGui import QIcon



class Sen2CorAdapterDialogTest(unittest.TestCase):
    """Test rerources work."""

    def setUp(self):
        """Runs before each test."""
        pass

    def tearDown(self):
        """Runs after each test."""
        pass

    def test_icon_png(self):
        """Test we can click OK."""
        path = ':/plugins/Sen2CorAdapter/icon.png'
        icon = QIcon(path)
        self.assertFalse(icon.isNull())

if __name__ == "__main__":
    suite = unittest.makeSuite(Sen2CorAdapterResourcesTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
