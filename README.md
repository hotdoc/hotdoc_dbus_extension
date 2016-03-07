This is a DBus extension for [hotdoc](https://github.com/hotdoc/hotdoc)

This extension uses dbus-deviation to generate symbols for DBus interfaces.

### Install instructions:

This extension has no system-wide dependencies.

You can install it either through pip:

```
pip install hotdoc_dbus_extension
```

Or with setup.py if you checked out the code from git:

```
python setup.py install
```

This will of course work in a virtualenv as well.

### Usage:

Just run hotdoc's wizard for more information once the extension is installed with:

```
hotdoc conf --quickstart
```

### Hacking

Checkout the code from github, then run:

```
python setup.py develop
```

### Licensing

hotdoc's DBus extension is licensed under the LGPL version 2.1 (or, at your option, any
later version). See COPYING for more details.
