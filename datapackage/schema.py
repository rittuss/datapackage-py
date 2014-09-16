from .util import Specification
import sys

if sys.version_info[0] < 3:
    next = lambda x: x.next()
    bytes = str
    str = unicode


class Field(Specification):
    """
    Field object for adding fields to a resource schema.

    Currently this is built around the Tabular Data Package.
    """

    SPECIFICATION = {'name': str,
                     'title': str,
                     'type': str,
                     'format': str,
                     'constraints': dict}

    def __init__(self, *args, **kwargs):
        # Name is a required field
        if 'name' not in kwargs:
            raise AttributeError(
                "'{0}' must be instantiated with attribute 'name'".format(
                    self.__class__.__name__))
        super(Field, self).__init__(*args, **kwargs)


class Constraints(Specification):
    """
    Constraints object which can be added to a field in a resource schema
    in order to represent the constraints put on that particular field.
    """

    SPECIFICATION = {'required': bool,
                     'minLength': int,
                     'maxLength': int,
                     'unique': bool,
                     'pattern': str,
                     'minimum': None,
                     'maximum': None}


class Reference(Specification):
    """
    Reference object which can be added to a ForeignKey object to represent
    the reference to the other datapackage.
    """

    SPECIFICATION = {'datapackage': str,
                     'resource': str,
                     'fields': (str, list)}

    def __setattr__(self, attribute, value):
        if attribute == 'fields':
            # We need to make sure all fields are represented with by their
            # names if it is a list
            if type(value) == list:
                modified_value = []
                for single_value in value:
                    if type(single_value) == str:
                        modified_value.append(single_value)
                    elif isinstance(single_value, Field):
                        modified_value.append(single_value.name)
                    else:
                        raise TypeError(
                            'Field type ({0}) is not supported'.format(
                                type(single_value)))
                value = modified_value
            elif type(value) == str:
                # We don't need to do anything with a str
                pass
            elif isinstance(value, Field):
                # Set the name from the field as the value
                value = value.name
            else:
                raise TypeError("Type of field ({0}) is not supported".format(
                    type(value)))

        super(Reference, self).__setattr__(attribute, value)


class ForeignKey(Specification):
    """
    ForeignKey object which can be added to a resource schema object to
    represent a foreign key in another data package.
    """

    SPECIFICATION = {'fields': (str, list),
                     'reference': Reference}

    def __setattr__(self, attribute, value):
        # If the attribute is 'reference' we need to check if there is a
        # fields attribute and do some checks to see if they are inconsistent
        # because they shouldn't be
        if attribute == 'reference' and dict.__contains__(self, 'fields'):
            fields = dict.__getitem__(self, 'fields')
            if type(fields) != type(value.fields):
                    raise TypeError(
                        'Reference fields must have the same type as fields')
            if type(value.fields) == list:
                if len(value.fields) != len(fields):
                    raise ValueError(
                        'Reference fields and fields are inconsistent')
        if attribute == 'fields':
            value_type = type(value)

            # We only want to show the names of the fields so we add we need
            # to go through a list and get out the names and use them as the
            # value
            if value_type == list:
                modified_value = []
                for single_value in value:
                    if type(single_value) == str:
                        modified_value.append(single_value)
                    elif isinstance(single_value, Field):
                        modified_value.append(single_value.name)
                    else:
                        raise TypeError(
                            'Foreign key type ({0}) is not supported'.format(
                                type(single_value)))
                value = modified_value
            elif value_type == str:
                # We don't need to do anything if the value is a str
                pass
            elif isinstance(value, Field):
                value = value.name
            else:
                raise TypeError("Type of field ({0}) is not supported".format(
                    value_type))

            # Same check as before about inconsistencies but just the other
            # way around
            if dict.__contains__(self, 'reference'):
                reference_fields = dict.__getitem__(self, 'reference').fields
                if type(reference_fields) != value_type:
                    raise TypeError(
                        'Fields must have the same type as Reference fields')
                if type(reference_fields) == list:
                    if len(reference_fields) != len(value):
                        raise ValueError(
                            'Reference fields and fields are inconsistent')

        super(ForeignKey, self).__setattr__(attribute, value)


class Schema(Specification):
    """
    Schema object which holds the representation of the schema for a
    Tabular Data Package (using the JSON Table Schema protocol). The
    schema can be used just like a dictionary which means it is ready
    for json serialization and export as part of a data package
    descriptor (when added to a resource).
    """

    SPECIFICATION = {'fields': list,
                     'primaryKey': (str, list),
                     'foreignKeys': list}

    def __init__(self, *args, **kwargs):
        dict.__init__(self, args)

        # We need to initialize an empty fields array
        dict.__setitem__(self, 'fields', [])
        # We add the fields using the internal method so we can do
        # validation of each field
        self.add_fields(kwargs.pop('fields', []))
        for (key, value) in kwargs.iteritems():
            self.__setattr__(key, value)

    def __setattr__(self, attribute, value):
        if attribute == 'primaryKey' and value is not None:
            # Primary Keys must be a reference to existing fields so we
            # need to check if the primary key is in the fields array
            field_names = [f.name for f in dict.get(self, 'fields', [])]
            if type(value) == list:
                modified_value = []
                for single_value in value:
                    if type(single_value) == str:
                        if single_value in field_names:
                            modified_value.append(single_value)
                        else:
                            raise AttributeError(
                                "Unknown '{0}' cannot be primaryKey".format(
                                    single_value))
                    elif isinstance(single_value, Field):
                        if single_value.name in field_names:
                            modified_value.append(single_value.name)
                        else:
                            raise AttributeError(
                                "Unknown '{0}' cannot be primaryKey".format(
                                    single_value.name))
                    else:
                        raise TypeError(
                            'primaryKey type ({0}) is not supported'.format(
                                type(single_value)))
                value = modified_value
            elif type(value) == str:
                if value not in field_names:
                    raise AttributeError(
                        "Unknown '{0}' cannot be primaryKey".format(
                            value))
            elif isinstance(value, Field):
                if value.name in field_names:
                    value = value.name
                else:
                    raise AttributeError(
                        "Unknown '{0}' cannot be primaryKey".format(
                            value.name))
            else:
                raise TypeError('Primary Key type ({0}) not supported'.format(
                    type(value)))

        super(Schema, self).__setattr__(attribute, value)

    def add_field(self, field):
        """
        Adds a field to the resource schema

        :param ~Field field: A Field instance containing the field to be
            appended to the schema.
        """
        if isinstance(field, Field):
            dict.__getitem__(self, 'fields').append(field)
        elif type(field) == dict:
            self.data['fields'].append(Field(field))
        else:
            raise TypeError("Type of parameter field is not supported.")

    def add_fields(self, fields):
        """
        Adds fields to the resource schema

        :param list fields: A list of Field instances which should be
            appended (extend) to the resource schema fields.
        """
        # We loop through the fields list to make sure all elements
        # in the list are of the proper type
        for field in fields:
            self.add_field(field)

    def add_foreign_key(self, foreign_key):
        """
        Adds a foreign key to the resource schema.

        :param ~ForeignKey foreign_key: A ForeignKey object which keeps
            track of a foreign key relationship to another data package.
        """
        # We can only accept ForeignKey objects
        if not isinstance(foreign_key, ForeignKey):
            raise TypeError("Foreign Key type is not supported")

        # ForeignKey fields must be a schema field
        field_names = [f.name for f in dict.get(self, 'fields', [])]
        for field in foreign_key.fields:
            if field not in field_names:
                raise ValueError(
                    "Foreign key field '{0}' is not in schema fields".format(
                        field))

        # Append the ForeignKey to the foreignKeys object or create it if it
        # doesn't exist
        foreign_keys = dict.get(self, 'foreignKeys', [])
        foreign_keys.append(foreign_key)
        dict.__setitem__(self, 'foreignKeys', foreign_keys)

    def add_foreign_keys(self, foreign_keys):
        """
        Adds foreign keys to the resource schema

        :param list foreign_keys: A list of ForeignKey instances which should
            be appended (extend) to the resource schema fields or create a
            foreignKeys attribute if it doesn't exist.
        """
        # We loop through the foreign keys list to make sure all elements
        # in the list are of the proper type and validate
        for foreign_key in foreign_keys:
            self.add_foreign_key(foreign_key)
