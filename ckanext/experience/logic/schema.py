"""
Copyright (c) 2018 Keitaro AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import ckan.plugins.toolkit as toolkit
from ckan.lib.navl.validators import (not_empty,
                                      empty,
                                      if_empty_same_as,
                                      ignore_missing,
                                      ignore,
                                      keep_extras)
from ckan.logic.validators import (package_id_not_changed,
                                   name_validator,
                                   user_id_or_name_exists,
                                   package_name_validator,
                                   tag_string_convert,
                                   ignore_not_package_admin,
                                   no_http)
from ckan.logic.schema import (default_tags_schema,
                               default_extras_schema,
                               default_resource_schema)

from ckanext.experience.logic.validators import (
    convert_package_name_or_id_to_id_for_type_dataset,
    convert_package_name_or_id_to_id_for_type_experience)


def experience_base_schema():
    schema = {
        'id': [empty],
        'revision_id': [ignore],
        'name': [not_empty, unicode, name_validator, package_name_validator],
        'title': [if_empty_same_as("name"), unicode],
        'author': [ignore_missing, unicode],
        'author_email': [ignore_missing, unicode],
        'notes': [ignore_missing, unicode],
        'url': [ignore_missing, unicode],
        'state': [ignore_not_package_admin, ignore_missing],
        'type': [ignore_missing, unicode],
        'log_message': [ignore_missing, unicode, no_http],
        '__extras': [ignore],
        '__junk': [empty],
        'resources': default_resource_schema(),
        'tags': default_tags_schema(),
        'tag_string': [ignore_missing, tag_string_convert],
        'extras': default_extras_schema(),
        'save': [ignore],
        'return_to': [ignore],
        'image_url': [toolkit.get_validator('ignore_missing'),
                      toolkit.get_converter('convert_to_extras')],
        'original_related_item_id': [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_converter('convert_to_extras')]
    }
    return schema


def experience_create_schema():
    return experience_base_schema()


def experience_update_schema():
    schema = experience_base_schema()

    # Users can (optionally) supply the package id when updating a package, but
    # only to identify the package to be updated, they cannot change the id.
    schema['id'] = [ignore_missing, package_id_not_changed]

    # Supplying the package name when updating a package is optional (you can
    # supply the id to identify the package instead).
    schema['name'] = [ignore_missing, name_validator,
                      package_name_validator, unicode]

    # Supplying the package title when updating a package is optional, if it's
    # not supplied the title will not be changed.
    schema['title'] = [ignore_missing, unicode]

    return schema


def experience_show_schema():
    schema = experience_base_schema()
    # Don't strip ids from package dicts when validating them.
    schema['id'] = []

    schema.update({
        'tags': {'__extras': [keep_extras]}})

    schema.update({
        'state': [ignore_missing],
        })

    # Remove validators for several keys from the schema so validation doesn't
    # strip the keys from the package dicts if the values are 'missing' (i.e.
    # None).
    schema['author'] = []
    schema['author_email'] = []
    schema['notes'] = []
    schema['url'] = []

    # Add several keys that are missing from default_create_package_schema(),
    # so validation doesn't strip the keys from the package dicts.
    schema['metadata_created'] = []
    schema['metadata_modified'] = []
    schema['creator_user_id'] = []
    schema['num_tags'] = []
    schema['revision_id'] = []
    schema['tracking_summary'] = []

    schema.update({
        'image_url': [toolkit.get_converter('convert_from_extras'),
                      toolkit.get_validator('ignore_missing')],
        'original_related_item_id': [
            toolkit.get_converter('convert_from_extras'),
            toolkit.get_validator('ignore_missing')]
    })

    return schema


def experience_package_association_create_schema():
    schema = {
        'package_id': [not_empty, unicode,
                       convert_package_name_or_id_to_id_for_type_dataset],
        'experience_id': [not_empty, unicode,
                        convert_package_name_or_id_to_id_for_type_experience]
    }
    return schema


def experience_package_association_delete_schema():
    return experience_package_association_create_schema()


def experience_package_list_schema():
    schema = {
        'experience_id': [not_empty, unicode,
                        convert_package_name_or_id_to_id_for_type_experience]
    }
    return schema


def package_experience_list_schema():
    schema = {
        'package_id': [not_empty, unicode,
                       convert_package_name_or_id_to_id_for_type_dataset]
    }
    return schema


def experience_admin_add_schema():
    schema = {
        'username': [not_empty, user_id_or_name_exists, unicode],
    }
    return schema


def experience_admin_remove_schema():
    return experience_admin_add_schema()
