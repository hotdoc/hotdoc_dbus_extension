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
from hotdoc.core.symbols import *
from hotdoc.parsers.gtk_doc_parser import GtkDocParser
from hotdoc.utils.loggable import warn

from hotdoc_dbus_extension.dbus_html_formatter import DBusHtmlFormatter

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

    def __comment_from_node(self, node):
        if node.comment is None:
            return None

        lineno = -1

        lines = node.comment.split('\n')
        stripped_lines = []
        column_offset = 0
        line_offset = 0
        for l in lines:
            nl = l.strip()
            if not nl and not stripped_lines:
                line_offset += 1
                continue
            if not column_offset and nl:
                column_offset = len(l) - len(nl)
            stripped_lines.append(nl)

        if hasattr(node, 'comment_lineno'):
            lineno = node.comment_lineno + line_offset

        comment = u'\n'.join(stripped_lines)
        comment = self.__raw_comment_parser.parse_comment (comment,
                self.__current_filename, lineno,
                -1, stripped=True)

        if comment:
            comment.col_offset = column_offset + 1
            for param in comment.params.values():
                param.col_offset = comment.col_offset

        return comment

    def __create_function_symbol (self, node):
        unique_name = '%s.%s' % (self.__current_class_name, node.name)
        comment = self.__comment_from_node(node)
        parameters = self.__create_parameters (node.arguments, comment)

        self.__doc_db.get_or_create_symbol(FunctionSymbol,
                parameters=parameters,
                comment=comment,
                display_name=node.name,
                filename=self.__current_filename,
                unique_name=unique_name)

    def __create_class_symbol (self, node):
        self.__current_class_name = node.name
        comment = self.__comment_from_node(node)
        self.__doc_db.get_or_create_symbol(ClassSymbol,
                comment=comment,
                display_name=node.name,
                filename=self.__current_filename)

    def __create_property_symbol (self, node):
        comment = self.__comment_from_node(node)
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
        comment = self.__comment_from_node(node)

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


class DBusExtension(BaseExtension):
    extension_name = 'dbus-extension'
    argument_prefix = 'dbus'

    def __init__(self, doc_repo):
        BaseExtension.__init__(self, doc_repo)
        self.formatters['html'] = DBusHtmlFormatter()

    def setup (self):
        stale, unlisted = self.get_stale_files(DBusExtension.sources)

        if not stale:
            return

        self.scanner = DBusScanner (self.doc_repo, self, stale)

    def get_or_create_symbol(self, *args, **kwargs):
        kwargs['language'] = 'dbus'
        return super(DBusExtension, self).get_or_create_symbol(*args,
            **kwargs)

    def _get_languages(self):
        return ['dbus']

    @staticmethod
    def add_arguments (parser):
        group = parser.add_argument_group('DBus extension',
                DESCRIPTION)
        DBusExtension.add_index_argument(group)
        DBusExtension.add_sources_argument(group)

    @staticmethod
    def parse_config(doc_repo, config):
        DBusExtension.parse_standard_config(config)

def get_extension_classes():
    return [DBusExtension]
