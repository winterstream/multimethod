# Copyright (c) 2013, Wynand Winterbach
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#   * Neither the name of the Dojo Foundation nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__ = 'wynand'

import rwlock
import multimethod


class ParentAlreadyInHierarchy(Exception):
    pass


class CircularRelationship(Exception):
    pass


class Hierarchy(object):
    def __init__(self):
        self.__version__ = 0
        self.rw = rwlock.ReadWriteLock()
        self.parents = {}
        self.ancestors = {}
        self.children = {}

    def _add_node(self, node):
        if node not in self.parents:
            self.parents[node] = set()
            self.ancestors[node] = {node}
            self.children[node] = set()

    def _add_edge(self, child, parent):
        self._add_node(parent)
        self._add_node(child)

        self.children[parent].add(child)
        self.parents[child].add(parent)
        self.ancestors[child] |= self.ancestors[parent]
        self._add_ancestor_to_descendants(child, parent)

        self.__version__ += 1

    def _add_ancestor_to_descendants(self, child, parent):
        seen = set()

        def loop(node):
            for child in self.children[node]:
                if child not in seen:
                    seen.add(node)
                    self.ancestors[child].add(parent)
                    loop(child)

        loop(child)

    def _derive_dict(self, children, parent):
        if children is not None:
            if isinstance(children, dict):
                for child, child_dct in children.viewitems():
                    self._derive(child, parent)
                    self._derive_dict(child_dct, child)
            else:
                self._derive(children, parent)

    def _derive(self, child, parent):
        if child in self.parents and parent in self.parents:
            # If we are simply re-deriving a previously derived
            # relationship, just return, as nothing has changed.
            if parent in self.parents[child]:
                return
            if child in self.ancestors[parent]:
                raise CircularRelationship()
            if parent in self.ancestors[child]:
                raise ParentAlreadyInHierarchy()
        self._add_edge(child, parent)

    def derive(self, child, parent=None):
        with self.rw.write():
            if parent is None and isinstance(child, dict):
                for parent, children in child.viewitems():
                    self._derive_dict(children, parent)
            else:
                self._derive(child, parent)

    def is_a(self, child, parent):
        # At least a read-lock must be held before calling this

        # We treat strings specially, since otherwise they are
        # treated as sequences, which is probably not what most
        # people want.
        if isinstance(child, (str, unicode)):
            try:
                return parent in self.ancestors[child]
            except KeyError:
                return False
        # First, let's see whether we're dealing with sequences...
        try:
            child_seq = list(child)
            parent_seq = list(parent)
            # If so, then the sequences must be of equal length...
            if len(child_seq) == len(parent_seq):
                # and the is_a relationship must hold for each component
                return all(self.is_a(child_seq[i], parent_seq[i])
                           for i in xrange(len(child_seq)))
        except TypeError:
            # Okay, so we're not dealing with strings or sequences.
            try:
                # Do we already have a relationship between parent and child?
                return parent in self.ancestors[child]
            except KeyError:
                # There is no relationship between parent.
                try:
                    # If we're dealing with classes, check whether they are
                    # related in the Python class hierarchy
                    if issubclass(child, parent):
                        return True
                except TypeError:
                    pass
        return False

    def multimethod(self, dispatch_func=lambda x: x, default_dispatch_val=multimethod.DefaultDispatchValue):
        def decorator(func):
            return multimethod.MultiMethod(func.__name__, dispatch_func, default_dispatch_val, self, default_func=func)
        return decorator
