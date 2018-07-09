import sqlalchemy

import ckan.plugins.toolkit as toolkit
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.navl.dictization_functions import validate
from ckan.logic import NotAuthorized

from ckanext.experience.logic.schema import (experience_package_list_schema,
                                           package_experience_list_schema)
from ckanext.experience.model import ExperiencePackageAssociation, ExperienceAdmin

import logging
log = logging.getLogger(__name__)

_select = sqlalchemy.sql.select
_and_ = sqlalchemy.and_


@toolkit.side_effect_free
def experience_show(context, data_dict):
    '''Return the pkg_dict for a experience (package).

    :param id: the id or name of the experience
    :type id: string
    '''

    toolkit.check_access('ckanext_experience_show', context, data_dict)

    pkg_dict = toolkit.get_action('package_show')(context, data_dict)

    return pkg_dict


@toolkit.side_effect_free
def experience_list(context, data_dict):
    '''Return a list of all experiences in the site.'''

    toolkit.check_access('ckanext_experience_list', context, data_dict)

    model = context["model"]

    q = model.Session.query(model.Package) \
        .filter(model.Package.type == 'experience') \
        .filter(model.Package.state == 'active')

    experience_list = []
    for pkg in q.all():
        experience_list.append(model_dictize.package_dictize(pkg, context))

    return experience_list


@toolkit.side_effect_free
def experience_package_list(context, data_dict):
    '''List packages associated with a experience.

    :param experience_id: id or name of the experience
    :type experience_id: string

    :rtype: list of dictionaries
    '''

    toolkit.check_access('ckanext_experience_package_list', context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(data_dict,
                                           experience_package_list_schema(),
                                           context)

    if errors:
        raise toolkit.ValidationError(errors)

    # get a list of package ids associated with experience id
    pkg_id_list = ExperiencePackageAssociation.get_package_ids_for_experience(
        validated_data_dict['experience_id'])

    pkg_list = []
    if pkg_id_list is not None:
        # for each package id, get the package dict and append to list if
        # active
        for pkg_id in pkg_id_list:
            try:
                pkg = toolkit.get_action('package_show')(context,
                                                         {'id': pkg_id})
                if pkg['state'] == 'active':
                    pkg_list.append(pkg)
            except NotAuthorized:
                log.debug(
                    'Not authorized to access Package with ID: ' + str(pkg_id))
    return pkg_list


@toolkit.side_effect_free
def package_experience_list(context, data_dict):
    '''List experiences associated with a package.

    :param package_id: id or name of the package
    :type package_id: string

    :rtype: list of dictionaries
    '''

    toolkit.check_access('ckanext_package_experience_list', context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(data_dict,
                                           package_experience_list_schema(),
                                           context)

    if errors:
        raise toolkit.ValidationError(errors)

    # get a list of experience ids associated with the package id
    experience_id_list = ExperiencePackageAssociation.get_experience_ids_for_package(
        validated_data_dict['package_id'])

    experience_list = []
    if experience_id_list is not None:
        for experience_id in experience_id_list:
            try:
                experience = toolkit.get_action('package_show')(
                    context,
                    {'id': experience_id}
                )
                experience_list.append(experience)
            except NotAuthorized:
                log.debug('Not authorized to access Package with ID: '
                          + str(experience_id))
    return experience_list


@toolkit.side_effect_free
def experience_admin_list(context, data_dict):
    '''
    Return a list of dicts containing the id and name of all active experience
    admin users.

    :rtype: list of dictionaries
    '''

    toolkit.check_access('ckanext_experience_admin_list', context, data_dict)

    model = context["model"]

    user_ids = ExperienceAdmin.get_experience_admin_ids()

    if user_ids:
        q = model.Session.query(model.User) \
            .filter(model.User.state == 'active') \
            .filter(model.User.id.in_(user_ids))

        experience_admin_list = []
        for user in q.all():
            experience_admin_list.append({'name': user.name, 'id': user.id})
        return experience_admin_list

    return []
