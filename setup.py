# -*- coding: utf-8 -*-
#
# Copyright © 2015,2016 Mathieu Duponchelle <mathieu.duponchelle@opencreed.com>
# Copyright © 2015,2016 Collabora Ltd
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import os

from setuptools import setup, find_packages

with open(os.path.join('hotdoc_dbus_extension', 'VERSION.txt'), 'r') as _:
    VERSION = _.read().strip()

setup(
    name = "hotdoc_dbus_extension",
    version = VERSION,
    keywords = "DBus hotdoc dbus-deviation",
    url='https://github.com/hotdoc/hotdoc_dbus_extension',
    author_email = 'mathieu.duponchelle@opencreed.com',
    license = 'LGPLv2.1+',
    description = ("An extension for hotdoc that parses DBus interfaces using"
                   " dbus-deviation"),
    author = "Mathieu Duponchelle",
    packages = find_packages(),
    package_data = {'hotdoc_dbus_extension': ['VERSION.txt']},
    entry_points = {'hotdoc.extensions': 'get_extension_classes = hotdoc_dbus_extension.dbus_extension:get_extension_classes'},
    install_requires = [
        'dbus-deviation>=0.4.0',
    ]
)
