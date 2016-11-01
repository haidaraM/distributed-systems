# -*- coding: utf-8 -*-
#*****************************************************************************
#       Copyright (C) 2007  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import sys

try:
    pyreadline_codepage = sys.stdout.encoding
except AttributeError:        
    # This error occurs when pdb imports readline and doctest has replaced 
    # stdout with stdout collector. We will assume ascii codepage
    pyreadline_codepage = u"ascii"

if pyreadline_codepage is None:  
    pyreadline_codepage = u"ascii"

def ensure_unicode(text):
    u"""helper to ensure that text passed to WriteConsoleW is unicode"""
    if isinstance(text, str):
        try:
            return text.decode(pyreadline_codepage, u"replace")
        except (LookupError, TypeError):
            return text.decode(u"ascii", u"replace")
    return text

def ensure_str(text):
    u"""Convert unicode to str using pyreadline_codepage"""
    if isinstance(text, unicode):
        try:
            return text.encode(pyreadline_codepage, u"replace")
        except (LookupError, TypeError):
            return text.encode(u"ascii", u"replace")
    return text
