import ckan.plugins.toolkit as toolkit
import ckan.model as model

from ckanext.experience.model import ExperienceAdmin

import logging
log = logging.getLogger(__name__)


def _is_experience_admin(context):
    '''
    Determines whether user in context is in the experience admin list.
    '''
    user = context.get('user', '')
    userobj = model.User.get(user)
    return ExperienceAdmin.is_user_experience_admin(userobj)


def create(context, data_dict):
    '''Create an Experience.

       Only sysadmin or users listed as Experience Admins can create an Experience.
    '''
    return {'success': _is_experience_admin(context)}


def delete(context, data_dict):
    '''Delete an Experience.

       Only sysadmin or users listed as Experience Admins can delete an Experience.
    '''
    return {'success': _is_experience_admin(context)}


def update(context, data_dict):
    '''Update an Experience.

       Only sysadmin or users listed as Experience Admins can update an Experience.
    '''
    return {'success': _is_experience_admin(context)}


@toolkit.auth_allow_anonymous_access
def show(context, data_dict):
    '''All users can access a experience show'''
    return {'success': True}


@toolkit.auth_allow_anonymous_access
def list(context, data_dict):
    '''All users can access a experience list'''
    return {'success': True}


def package_association_create(context, data_dict):
    '''Create a package experience association.

       Only sysadmins or user listed as Experience Admins can create a
       package/experience association.
    '''
    return {'success': _is_experience_admin(context)}


def package_association_delete(context, data_dict):
    '''Delete a package experience association.

       Only sysadmins or user listed as Experience Admins can delete a
       package/experience association.
    '''
    return {'success': _is_experience_admin(context)}


@toolkit.auth_allow_anonymous_access
def experience_package_list(context, data_dict):
    '''All users can access a experience's package list'''
    return {'success': True}


@toolkit.auth_allow_anonymous_access
def package_experience_list(context, data_dict):
    '''All users can access a packages's experience list'''
    return {'success': True}


def add_experience_admin(context, data_dict):
    '''Only sysadmins can add users to experience admin list.'''
    return {'success': False}


def remove_experience_admin(context, data_dict):
    '''Only sysadmins can remove users from experience admin list.'''
    return {'success': False}


def experience_admin_list(context, data_dict):
    '''Only sysadmins can list experience admin users.'''
    return {'success': False}
