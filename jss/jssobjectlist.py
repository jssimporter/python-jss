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
"""jssobjectlist.py

Classes representing lists of objects returned from GET requests to the
JSS.
"""


from collections import MutableMapping
import cPickle
import os


class JSSListData(MutableMapping):
    """Holds overview information returned from a listing GET."""

    def __init__(self, obj_class, data, factory):
        """Configure a JSSListData item."""
        self.obj_class = obj_class
        self.factory = factory
        self.store = dict(data)

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        """Make data human readable."""
        # Note: Large lists/objects may take a long time to indent!
        max_key_width = max([len(key) for key in self.store])
        max_val_width = max([len(unicode(val)) for val in self.store.values()])
        output = []
        for key, val in self.store.items():
            output.append(u"{:>{max_key}}: {:>{max_val}}".format(
                key, val, max_key=max_key_width, max_val=max_val_width))
        return "\n".join(output).encode("utf-8")

    @property
    def id(self):   # pylint: disable=invalid-name
        """Return the object's ID property."""
        return int(self["id"])

    @property
    def name(self):
        """Return the object's name property."""
        return self["name"]

    def retrieve(self):
        """Retrieve the full object XML for this item."""
        return self.factory.get_object(self.obj_class, self.id)


class JSSObjectList(object):
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
        if not isinstance(objects, (list, tuple, set)):
            raise TypeError

        self._objects = []
        if objects:
            for obj in objects:
                if isinstance(obj, JSSListData):
                    item = (obj, None)
                else:
                    item = (None, obj)
                self._objects.append(item)

    def __len__(self):
        return len(self._objects)

    def __iter__(self):
        def whoa():
            for index, item in enumerate(self._objects):
                if item[1] is None:
                    if item[0]:
                        result = item[0].retrieve()
                        self._objects[index] = (item[0], result)
                yield self._objects[index][1]
        return whoa()

    def simple_iter(self):
        def whoa():
            for item in self._objects:
                yield item[0]
        return whoa()

    def __getitem__(self, index):
        item = self._objects[index]
        if item[1] is None:
            if item[0]:
                result = self._objects[index][0].retrieve()
                self._objects[index] = (item[0], result)
        return self._objects[index][1]

    def __str__(self):
        """Make data human readable."""
        #Note: Large lists/objects may take a long time to indent!
        if self._objects:
            item = self._objects[0]
            obj_class = item[0].obj_class.__name__

        name_max= max(len(item[0].name) for item in self._objects)
        id_max = max(len(str(item[0].id)) for item in self._objects)
        results = ["QueryResults for JSS object type: '{}':".format(obj_class)]
        results.append((name_max + id_max + 11) * '-')
        for simple, _ in self._objects:
            line = "Name: {0:>{2}} ID: {1:>{3}}".format(
                simple.name, simple.id, name_max, id_max)
            results.append(line)
        return "\n".join(results)

    def __repr__(self):
        """Make data human readable."""
        results = []
        for item, cached in self._objects:
            line = "<instance of '{}' name: {} id: {} cached: {}>".format(
                item.__class__.__name__, item.name, item.id,
                bool(cached is not None))

            results.append(line)

        return ", ".join(results)



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

