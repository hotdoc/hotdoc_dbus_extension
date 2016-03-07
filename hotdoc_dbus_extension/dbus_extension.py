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

import os, glob

from dbusapi.interfaceparser import InterfaceParser

from hotdoc.core.base_extension import BaseExtension
from hotdoc.core.file_includer import find_md_file
from hotdoc.core.wizard import HotdocWizard
from hotdoc.core.symbols import *
from hotdoc.parsers.gtk_doc_parser import GtkDocParser
from hotdoc.utils.wizard import QuickStartWizard
from hotdoc.utils.loggable import warn

class DBusScanner(object):
    def __init__(self, doc_repo, doc_db, sources):
        self.__current_filename = None
        self.symbols = {}
        self.doc_repo = doc_repo
        self.__doc_db = doc_db
        self.__raw_comment_parser = GtkDocParser(self.doc_repo)
        for filename in sources:
            self.__current_filename = filename
            ip = InterfaceParser(filename)
            for name, interface in ip.parse().iteritems():
                self.__create_class_symbol (interface)
                for mname, method in interface.methods.iteritems():
                    self.__create_function_symbol (method)
                for pname, prop in interface.properties.iteritems():
                    self.__create_property_symbol (prop)
                for sname, signal in interface.signals.iteritems():
                    self.__create_signal_symbol (signal)

    def __create_parameters (self, nodes, comment, omit_direction=False):
        parameters = []

        for param in nodes:
            if comment:
                param_comment = comment.params.get (param.name)
            else:
                param_comment = None

            type_tokens = []
            if not omit_direction:
                type_tokens.append (param.direction.upper() + ' ')
            type_tokens.append (param.type)
            parameters.append (ParameterSymbol (argname=param.name,
                type_tokens=type_tokens,
                comment=param_comment))

        return parameters

    def __create_function_symbol (self, node):
        unique_name = '%s.%s' % (self.__current_class_name, node.name)
        comment = '\n'.join([l.strip() for l in node.comment.split('\n')])
        comment = self.__raw_comment_parser.parse_comment (comment,
                self.__current_filename, 0, 0, stripped=True)

        parameters = self.__create_parameters (node.arguments, comment)

        self.__doc_db.get_or_create_symbol(FunctionSymbol,
                parameters=parameters,
                comment=comment,
                display_name=node.name,
                filename=self.__current_filename,
                unique_name=unique_name)

    def __create_class_symbol (self, node):
        self.__current_class_name = node.name
        comment = '\n'.join([l.strip() for l in node.comment.split('\n')])
        comment = self.__raw_comment_parser.parse_comment (comment,
                self.__current_filename, 0, 0, stripped = True)
        self.__doc_db.get_or_create_symbol(ClassSymbol,
                comment=comment,
                display_name=node.name,
                filename=self.__current_filename)

    def __create_property_symbol (self, node):
        comment = '\n'.join([l.strip() for l in node.comment.split('\n')])
        comment = self.__raw_comment_parser.parse_comment (comment,
                self.__current_filename, 0, 0, stripped = True)
        type_tokens = [node.type]
        type_ = QualifiedSymbol (type_tokens=type_tokens)

        flags = ''
        if node.access == node.ACCESS_READ:
            flags = 'Read'
        elif node.access == node.ACCESS_WRITE:
            flags = 'Write'
        elif node.access == node.ACCESS_READWRITE:
            flags = 'Read / Write'

        unique_name = '%s.%s' % (self.__current_class_name, node.name)
        sym = self.__doc_db.get_or_create_symbol(PropertySymbol,
                prop_type=type_, comment=comment,
                display_name=node.name,
                unique_name=unique_name,
                filename=self.__current_filename)

        if flags:
            sym.extension_contents['Flags'] = flags

    def __create_signal_symbol (self, node):
        comment = '\n'.join([l.strip() for l in node.comment.split('\n')])
        comment = self.__raw_comment_parser.parse_comment (comment,
                self.__current_filename, 0, 0, stripped=True)

        parameters = self.__create_parameters (node.arguments, comment,
                omit_direction=True)

        unique_name = '%s.%s' % (self.__current_class_name, node.name)
        self.__doc_db.get_or_create_symbol(SignalSymbol,
                parameters=parameters, comment=comment,
                display_name=node.name, unique_name=unique_name,
                filename=self.__current_filename)

DESCRIPTION=\
"""
Parse DBus XML files and extract symbols and comments.
"""

DBUS_SOURCES_PROMPT=\
"""
Please pass a list of dbus source files.

You can pass wildcards here, for example:

>>> ['../foo/*.xml', '../foo//bar/*.xml]

These wildcards will be evaluated each time hotdoc is run.

You will be prompted for source files to ignore afterwards.
"""

DBUS_FILTERS_PROMPT=\
"""
Please pass a list of dbus source files to ignore.

You can pass wildcards here, for example:

>>> ['../foo/*priv*.xml']

These wildcards will be evaluated each time hotdoc is run.
"""

def validate_filters(wizard, thing):
    if not QuickStartWizard.validate_globs_list(wizard, thing):
        return False

    source_files = resolve_patterns(wizard.config.get('dbus_sources', []), wizard)

    filters = resolve_patterns(thing, wizard)

    source_files = [item for item in source_files if item not in filters]

    print "The files to be parsed would now be %s" % source_files

    return wizard.ask_confirmation()

def resolve_patterns(source_patterns, conf_path_resolver):
    if source_patterns is None:
        return []

    source_files = []
    for item in source_patterns:
        item = conf_path_resolver.resolve_config_path(item)
        source_files.extend(glob.glob(item))

    return source_files

def source_files_from_config(config, conf_path_resolver):
    sources = resolve_patterns(config.get('dbus_sources', []), conf_path_resolver)
    filters = resolve_patterns(config.get('dbus_source_filters', []),
            conf_path_resolver)
    sources = [item for item in sources if item not in filters]
    return [os.path.abspath(source) for source in sources]

class DBusExtension(BaseExtension):
    EXTENSION_NAME = 'dbus-extension'
    sources = None
    index = None

    def __init__(self, doc_repo):
        BaseExtension.__init__(self, doc_repo)
        doc_repo.doc_tree.page_parser.register_well_known_name ('dbus-api',
                self.dbus_index_handler)

    def setup (self):
        stale, unlisted = self.get_stale_files(DBusExtension.sources)

        if not stale:
            return

        self.scanner = DBusScanner (self.doc_repo, self, stale)

    @staticmethod
    def add_arguments (parser):
        group = parser.add_argument_group('DBus extension',
                DESCRIPTION)
        group.add_argument ("--dbus-sources", action="store", nargs="+",
                dest="dbus_sources", help="DBus source files to parse",
                extra_prompt=DBUS_SOURCES_PROMPT,
                validate_function=QuickStartWizard.validate_globs_list,
                finalize_function=HotdocWizard.finalize_paths)
        group.add_argument ("--dbus-source-filters", action="store", nargs="+",
                dest="dbus_source_filters", help="DBus source files to ignore",
                extra_prompt=DBUS_FILTERS_PROMPT,
                validate_function=validate_filters,
                finalize_function=HotdocWizard.finalize_paths)
        group.add_argument ("--dbus-index", action="store",
                dest="dbus_index",
                help="Name of the dbus root markdown file",
                finalize_function=HotdocWizard.finalize_path)

    @staticmethod
    def parse_config(doc_repo, config):
        DBusExtension.sources = source_files_from_config(config, doc_repo)
        DBusExtension.index = config.get('dbus_index')

    def dbus_index_handler(self, doc_tree):
        if not DBusExtension.index:
            warn('parsing-issue',
                 'Well-known-name dbus-index encountered, but "dbus_index" is '
                 'missing')
            return None
        index_path = find_md_file(DBusExtension.index,
                                  self.doc_repo.include_paths)
        return index_path, '', 'dbus-extension'

def get_extension_classes():
    return [DBusExtension]
