#!/usr/bin/env python
# Copyright (C) 2014-2017 Shea G Craig
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""queryset.py

Class that adds some extra functionality to a basic list. Used for the
result of all queries in python-jss, as well as unpickling and loading.
"""


from collections import MutableMapping
import cPickle
import os


class QuerySet(object):
    old_docstring = """A list style collection of JSSObjects.

    List operations retrieve minimal or overview information for most
    object types. For example, we may want to see all the Computers on
    the JSS but that does not mean we want to do a full object GET for
    each one.

    The JSSObjectList provides Methods to retrieve individual members'
    full information (retrieve_by_id, retrieve), and to retrieve the
    full information for each member of the entire list (retrieve_all).

    Attributes:
        factory: A JSSObjectFactory for managing object construction and
            searching.
        obj_class: A JSSObject class (e.g. jss.Computer) that the list
            contains.
    """

    def __init__(self, factory, obj_class, objects=None):
        """"""
        self.contained_class = obj_class
        if not isinstance(objects, (list, tuple, set)):
            raise TypeError

        self._objects = list(objects) if objects else []

    def __len__(self):
        return len(self._objects)

    def __iter__(self):
        return iter(self._objects)

    def __str__(self):
        """Make data human readable."""
        #Note: Large lists/objects may take a long time to indent!
        name_max= max(len(item[0].name) for item in self._objects)
        id_max = max(len(str(item[0].id)) for item in self._objects)
        results = ["QueryResults for JSS object type: '{}':".format(
            self.contained_class)]
        results.append((name_max + id_max + 11) * '-')
        for item in self._objects:
            line = "Name: {0:>{2}} ID: {1:>{3}}".format(
                item.name, item.id, name_max, id_max)
            results.append(line)
        return "\n".join(results)

    def __repr__(self):
        """Make data human readable."""
        return "<{}> {}".format(self.__class__.__name__, repr(self._objects))



    def old__init__(self, factory, obj_class, objects):
        """Construct a list of JSSObjects.

        Args:
            factory: A JSSObjectFactory for managing object construction
                in the event one of the retrieval methods is used.
            obj_class: A JSSObject class (e.g. jss.Computer) that the
                list contains, or None, if you are providing the full
                    objects.
            objects: A list of JSSListData objects (incomplete data
                about a JSSObject, as returned by the JSS from a listing
                request).
        """
        self.factory = factory
        self.obj_class = obj_class
        super(JSSObjectList, self).__init__(objects)

    def old__repr__(self):
        """Make data human readable."""
        # Note: Large lists/objects may take a long time to indent!
        if self and all([isinstance(item, JSSListData) for item in self]):
            max_key_width = max([len(key) for obj in self for key in obj])
            list_index = "List index"
            if max_key_width < len(list_index):
                max_key_width = len(list_index)
            max_val_width = max([len(unicode(val)) for obj in self for val in
                                obj.values()])
            max_width = max_key_width + max_val_width + 2
            delimeter = max_width * "-"
            output = [delimeter]
            for obj in self:
                output.append("{:>{max_key}}: {:>{max_val}}".format(
                    list_index, self.index(obj), max_key=max_key_width,
                    max_val=max_val_width))
                for key, val in obj.items():
                    output.append(u"{:>{max_key}}: {:>{max_val}}".format(
                        key, val, max_key=max_key_width,
                        max_val=max_val_width))
                output.append(delimeter)
            return "\n".join(output).encode("utf-8")
        else:
            output = []
            for item in self:
                output.append(item.__repr__())
            return "[\n%s]" % ",\n".join(output)


    # def __getitem__(self, index):
    #     item = super(JSSObjectList, self).__getitem__(index)
    #     return item.retrieve()

    def sort(self):
        """Sort list elements by ID."""
        super(JSSObjectList, self).sort(key=lambda k: k.id)

    def sort_by_name(self):
        """Sort list elements by name."""
        super(JSSObjectList, self).sort(key=lambda k: k.name)

    def retrieve(self, index):
        """Return a JSSObject for the JSSListData element at index."""
        return self[index].retrieve()

    def retrieve_by_id(self, id_):
        """Return a JSSObject for the element with ID id_"""
        items_with_id = [item for item in self if item.id == int(id_)]
        if len(items_with_id) == 1:
            return items_with_id[0].retrieve()

    def retrieve_all(self, subset=None):
        """Return a list of all JSSListData elements as full JSSObjects.

        This can take a long time given a large number of objects,
        and depending on the size of each object. Subsetting to only
        include the data you need can improve performance.

        Args:
            subset: For objects which support it, a list of sub-tags to
                request, or an "&" delimited string, (e.g.
                "general&purchasing").  Default to None.
        """
        # Attempt to speed this procedure up as much as can be done.

        get_object = self.factory.get_object
        obj_class = self.obj_class

        full_objects = [get_object(obj_class, list_obj.id, subset) for list_obj
                        in self]
        return JSSObjectList(self.factory, obj_class, full_objects)

    def pickle(self, path):
        """Write objects to python pickle.

        Pickling is Python's method for serializing/deserializing
        Python objects. This allows you to save a fully functional
        JSSObject to disk, and then load it later, without having to
        retrieve it from the JSS.

        This method will pickle each item as it's current type; so
        JSSListData objects will be serialized as JSSListData, and
        JSSObjects as JSSObjects. If you want full data, do:
            my_list.retrieve_all().pickle("filename")

        Args:
            path: String file path to the file you wish to (over)write.
                Path will have ~ expanded prior to opening.
        """
        with open(os.path.expanduser(path), "wb") as pickle:
            cPickle.Pickler(pickle, cPickle.HIGHEST_PROTOCOL).dump(self)

    @classmethod
    def from_pickle(cls, path):
        """Load objects from pickle file.

        Pickling is Python's method for serializing/deserializing
        Python objects. This allows you to save a fully functional
        JSSObject to disk, and then load it later, without having to
        retrieve it from the JSS.

        This method loads up a JSSObjectList from a pickle file.

        Args:
            path: String file path to the file you wish to load from.
                Path will have ~ expanded prior to opening.
        """
        with open(os.path.expanduser(path), "rb") as pickle:
            return cPickle.Unpickler(pickle).load()

