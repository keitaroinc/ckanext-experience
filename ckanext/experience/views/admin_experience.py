from urllib.parse import urlencode
import logging


from flask import Blueprint, request
from ckan.plugins import toolkit as tk
import ckan.model as model
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.plugins as p
from ckan.common import ungettext, config
from ckan.views.dataset import (url_with_params, _encode_params)
                                      
                                      

from ckanext.experience.model import ExperiencePackageAssociation
DATASET_TYPE_NAME = 'experience'

_ = tk._
c = tk.c
request = tk.request
render = tk.render
abort = tk.abort
redirect = tk.redirect_to
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
check_access = tk.check_access
get_action = tk.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
NotAuthorized = tk.NotAuthorized


log = logging.getLogger(__name__)

admin_experience = Blueprint(u'admin_experience', __name__, url_prefix=u'ckan-admin')

@admin_experience.before_request
def before_request():
    try:
        context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
        logic.check_access(u'sysadmin', context)
    except NotAuthorized:
        abort(403, _(u'Need to be system administrator to administer'))


def manage_experience_admins(self):
        '''
        A ckan-admin page to list and add experience admin users.
        '''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

        try:
            check_access('sysadmin', context, {})
        except NotAuthorized:
            abort(401, _('User not authorized to view page'))

        # We're trying to add a user to the experience admins list.
        if request.method == 'POST' and request.params['username']:
            username = request.params['username']
            try:
                get_action('ckanext_experience_admin_add')(
                    data_dict={'username': username})
            except NotAuthorized:
                abort(401, _('Unauthorized to perform that action'))
            except NotFound:
                h.flash_error(_("User '{user_name}' not found.").format(
                    user_name=username))
            except ValidationError as e:
                h.flash_notice(e.error_summary)
            else:
                h.flash_success(_("The user is now an Experience Admin"))

            return redirect(h.url_for(
                'ckanext.experience.views.admin_experience.manage_experience_admins'))

        c.experience_admins = get_action('ckanext_experience_admin_list')()

        return render('admin/manage_experience_admins.html')

def remove_experience_admin(self):
    '''
    Remove a user from the Experience Admin list.
    '''
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}

    try:
        check_access('sysadmin', context, {})
    except NotAuthorized:
        abort(401, _('User not authorized to view page'))

    if 'cancel' in request.params:
        tk.redirect_to(
            'ckanext.experience.views.admin_experience.manage_experience_admins')

    user_id = request.params['user']
    if request.method == 'POST' and user_id:
        user_id = request.params['user']
        try:
            get_action('ckanext_experience_admin_remove')(
                data_dict={'username': user_id})
        except NotAuthorized:
            abort(401, _('Unauthorized to perform that action'))
        except NotFound:
            h.flash_error(_('The user is not an Experience Admin'))
        else:
            h.flash_success(_('The user is no longer an Experience Admin'))

        return redirect(h.url_for(
           'ckanext.experience.views.admin_experience.manage_experience_admins'))

    c.user_dict = get_action('user_show')(data_dict={'id': user_id})
    c.user_id = user_id
    return render('admin/confirm_remove_experience_admin.html')
    
    
admin_experience.add_url_rule(u'/experience/manage_experience_admins',view_func=manage_experience_admins, methods=[u'GET', u'POST'])  
admin_experience.add_url_rule(u'/experience/remove_experience_admin',view_func=remove_experience_admin, methods=[u'GET', u'POST'])      
