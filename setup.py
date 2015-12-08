from setuptools import setup, find_packages

setup(
    name = "hotdoc_dbus_extension",
    version = "0.6",
    keywords = "DBus hotdoc dbus-deviation",
    url='https://github.com/hotdoc/hotdoc_dbus_extension',
    author_email = 'mathieu.duponchelle@opencreed.com',
    license = 'LGPL',
    description = ("An extension for hotdoc that parses DBus interfaces using"
                   " dbus-deviation"),
    author = "Mathieu Duponchelle",
    packages = find_packages(),
    entry_points = {'hotdoc.extensions': 'get_extension_classes = hotdoc_dbus_extension.dbus_extension:get_extension_classes'},
    install_requires = [
        'hotdoc>=0.6',
        'dbus-deviation==0.3.0',
    ]
)
