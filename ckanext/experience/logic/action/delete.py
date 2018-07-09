import logging

import ckan.plugins.toolkit as toolkit
from ckan.logic.converters import convert_user_name_or_id_to_id
import ckan.lib.navl.dictization_functions

from ckanext.experience.logic.schema import (
    experience_package_association_delete_schema,
    experience_admin_remove_schema)

from ckanext.experience.model import ExperiencePackageAssociation, ExperienceAdmin

validate = ckan.lib.navl.dictization_functions.validate

log = logging.getLogger(__name__)


def experience_delete(context, data_dict):
    '''Delete a experience. Experience delete cascades to
    ExperiencePackageAssociation objects.

    :param id: the id or name of the experience to delete
    :type id: string
    '''

    model = context['model']
    id = toolkit.get_or_bust(data_dict, 'id')

    entity = model.Package.get(id)

    if entity is None:
        raise toolkit.ObjectNotFound

    toolkit.check_access('ckanext_experience_delete', context, data_dict)

    entity.purge()
    model.repo.commit()


def experience_package_association_delete(context, data_dict):
    '''Delete an association between a experience and a package.

    :param experience_id: id or name of the experience in the association
    :type experience_id: string

    :param package_id: id or name of the package in the association
    :type package_id: string
    '''

    model = context['model']

    toolkit.check_access('ckanext_experience_package_association_delete',
                         context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(
        data_dict, experience_package_association_delete_schema(), context)

    if errors:
        raise toolkit.ValidationError(errors)

    package_id, experience_id = toolkit.get_or_bust(validated_data_dict,
                                                  ['package_id',
                                                   'experience_id'])

    experience_package_association = ExperiencePackageAssociation.get(
        package_id=package_id, experience_id=experience_id)

    if experience_package_association is None:
        raise toolkit.ObjectNotFound(toolkit._("ExperiencePackageAssociation with package_id '{0}' and experience_id '{1}' doesn't exist.").format(package_id, experience_id))

    # delete the association
    experience_package_association.delete()
    model.repo.commit()


def experience_admin_remove(context, data_dict):
    '''Remove a user to the list of experience admins.

    :param username: name of the user to remove from experience user admin list
    :type username: string
    '''

    model = context['model']

    toolkit.check_access('ckanext_experience_admin_remove', context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(data_dict,
                                           experience_admin_remove_schema(),
                                           context)

    if errors:
        raise toolkit.ValidationError(errors)

    username = toolkit.get_or_bust(validated_data_dict, 'username')
    user_id = convert_user_name_or_id_to_id(username, context)

    experience_admin_to_remove = ExperienceAdmin.get(user_id=user_id)

    if experience_admin_to_remove is None:
        raise toolkit.ObjectNotFound(toolkit._("ExperienceAdmin with user_id '{0}' doesn't exist.").format(user_id))

    experience_admin_to_remove.delete()
    model.repo.commit()
