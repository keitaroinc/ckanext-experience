import logging

import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit
from ckan.logic.converters import convert_user_name_or_id_to_id
from ckan.lib.navl.dictization_functions import validate

import ckanext.experience.logic.converters as experience_converters
import ckanext.experience.logic.schema as experience_schema
from ckanext.experience.model import ExperiencePackageAssociation, ExperienceAdmin

convert_package_name_or_id_to_title_or_name = \
    experience_converters.convert_package_name_or_id_to_title_or_name
experience_package_association_create_schema = \
    experience_schema.experience_package_association_create_schema
experience_admin_add_schema = experience_schema.experience_admin_add_schema

log = logging.getLogger(__name__)


def experience_create(context, data_dict):
    '''Upload the image and continue with package creation.'''

    # force type to 'experience'
    data_dict['type'] = 'experience'

    # If get_uploader is available (introduced for IUploader in CKAN 2.5), use
    # it, otherwise use the default uploader.
    # https://github.com/ckan/ckan/pull/2510
    try:
        upload = uploader.get_uploader('experience')
    except AttributeError:
        upload = uploader.Upload('experience')

    upload.update_data_dict(data_dict, 'image_url',
                            'image_upload', 'clear_upload')

    upload.upload(uploader.get_max_image_size())

    pkg = toolkit.get_action('package_create')(context, data_dict)

    return pkg


def experience_package_association_create(context, data_dict):
    '''Create an association between a experience and a package.

    :param experience_id: id or name of the experience to associate
    :type experience_id: string

    :param package_id: id or name of the package to associate
    :type package_id: string
    '''

    toolkit.check_access('ckanext_experience_package_association_create',
                         context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(
        data_dict, experience_package_association_create_schema(), context)

    if errors:
        raise toolkit.ValidationError(errors)

    package_id, experience_id = toolkit.get_or_bust(validated_data_dict,
                                                  ['package_id',
                                                   'experience_id'])

    if ExperiencePackageAssociation.exists(package_id=package_id,
                                         experience_id=experience_id):
        raise toolkit.ValidationError(toolkit._("ExperiencePackageAssociation with package_id '{0}' and experience_id '{1}' already exists.").format(package_id, experience_id),
                                      error_summary=toolkit._(u"The dataset, {0}, is already in the experience").format(convert_package_name_or_id_to_title_or_name(package_id, context)))

    # create the association
    return ExperiencePackageAssociation.create(package_id=package_id,
                                             experience_id=experience_id)


def experience_admin_add(context, data_dict):
    '''Add a user to the list of experience admins.

    :param username: name of the user to add to experience user admin list
    :type username: string
    '''

    toolkit.check_access('ckanext_experience_admin_add', context, data_dict)

    # validate the incoming data_dict
    validated_data_dict, errors = validate(
        data_dict, experience_admin_add_schema(), context)

    username = toolkit.get_or_bust(validated_data_dict, 'username')
    try:
        user_id = convert_user_name_or_id_to_id(username, context)
    except toolkit.Invalid:
        raise toolkit.ObjectNotFound

    if errors:
        raise toolkit.ValidationError(errors)

    if ExperienceAdmin.exists(user_id=user_id):
        raise toolkit.ValidationError(toolkit._("ExperienceAdmin with user_id '{0}' already exists.").format(user_id),
                                      error_summary=toolkit._(u"User '{0}' is already an Experience Admin.").format(username))

    # create experience admin entry
    return ExperienceAdmin.create(user_id=user_id)
