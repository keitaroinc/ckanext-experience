# -*- coding: utf-8 -*-
import logging

from flask import Blueprint

import ckantoolkit as tk

from ckan import model
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.views.dataset as dataset

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

DATASET_TYPE_NAME = 'experience'

experience = Blueprint(u'experience_blueprint', __name__)


def index():
    return dataset.search(DATASET_TYPE_NAME)


class CreateView(dataset.CreateView):
    def get(self, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}

        # Check access here, then continue with PackageController.new()
        # PackageController.new will also check access for package_create.
        # This is okay for now, while only sysadmins can create Experiences, but
        # may not work if we allow other users to create Experiences, who don't
        # have access to create dataset package types. Same for edit below.
        try:
            check_access('ckanext_experience_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a package'))
        return super(CreateView, self).get(DATASET_TYPE_NAME, data,
                                           errors, error_summary)

    def post(self):

        data_dict = dataset.clean_dict(
            dataset.dict_fns.unflatten(
                dataset.tuplize_dict(dataset.parse_params(tk.request.form))))
        data_dict.update(
            dataset.clean_dict(
                dataset.dict_fns.unflatten(
                    dataset.tuplize_dict(dataset.parse_params(
                        tk.request.files)))))
        context = self._prepare()
        data_dict['type'] = DATASET_TYPE_NAME
        context['message'] = data_dict.get('log_message', '')

        try:
            pkg_dict = tk.get_action('ckanext_experience_create')(context,
                                                                  data_dict)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            data_dict['state'] = 'none'
            return self.get(data_dict, errors, error_summary)

        # redirect to manage datasets
        url = h.url_for('experience_blueprint.manage_datasets',
                        id=pkg_dict['name'])
        return h.redirect_to(url)


def admins():
    '''
            A ckan-admin page to list and add experience admin users.
            '''
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}

    try:
        check_access('sysadmin', context, {})
    except NotAuthorized:
        abort(401, _('User not authorized to view page'))

    form_data = tk.request.form

    # We're trying to add a user to the experience admins list.
    if request.method == 'POST' and form_data['username']:
        username = form_data['username']
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

        return tk.redirect_to(h.url_for('experience_blueprint.admins'))

    c.experience_admins = get_action('ckanext_experience_admin_list')()

    return render('admin/manage_experience_admins.html')


experience.add_url_rule('/experience',
                        view_func=index)
experience.add_url_rule('/experience/new',
                        view_func=CreateView.as_view('new'))



experience.add_url_rule('/ckan-admin/experience_admins',
                        view_func=admins,
                        methods=[u'GET', u'POST'])


def get_blueprints():
    return [experience]
