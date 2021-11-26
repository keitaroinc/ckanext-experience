# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict
import six
from six.moves.urllib.parse import urlencode

from flask import Blueprint

import ckantoolkit as tk

from ckan import model
import ckan.plugins as p
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.views.dataset as dataset

from ckanext.experience.model import ExperiencePackageAssociation

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
                   'save': 'save' in request.form}

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
                dataset.tuplize_dict(dataset.parse_params(request.form))))
        data_dict.update(
            dataset.clean_dict(
                dataset.dict_fns.unflatten(
                    dataset.tuplize_dict(dataset.parse_params(
                        request.files)))))
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
        return redirect(url)


def delete(id):
    if 'cancel' in request.form:
        tk.redirect_to('experience_blueprint.edit', id=id)

    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}

    try:
        check_access('ckanext_experience_delete', context, {'id': id})
    except NotAuthorized:
        abort(401, _('Unauthorized to delete experience'))

    try:
        if request.method == 'POST':
            get_action('ckanext_experience_delete')(context, {'id': id})
            h.flash_notice(_('Experience has been deleted.'))
            return tk.redirect_to('experience_blueprint.index')
        c.pkg_dict = get_action('package_show')(context, {'id': id})
    except NotAuthorized:
        abort(401, _('Unauthorized to delete experience'))
    except NotFound:
        abort(404, _('Experience not found'))
    return render('experience/confirm_delete.html',
                  extra_vars={'dataset_type': DATASET_TYPE_NAME})


def read(id):
    '''
    Detail view for a single experience, listing its associated datasets.
    '''

    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'for_view': True,
               'auth_user_obj': c.userobj}
    data_dict = {'id': id}

    # check if experience exists
    try:
        c.pkg_dict = get_action('package_show')(context, data_dict)
    except NotFound:
        abort(404, _('Experience not found'))
    except NotAuthorized:
        abort(401, _('Unauthorized to read experience'))

    # get experience packages
    c.experience_pkgs = get_action('ckanext_experience_package_list')(
        context, {'experience_id': c.pkg_dict['id']})

    package_type = DATASET_TYPE_NAME
    return tk.render('experience/read.html',
                     extra_vars={'dataset_type': package_type})


class EditView(dataset.EditView):
    def get(self, id, data=None, errors=None, error_summary=None):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.form,
                   'moderated': tk.config.get('moderated'),
                   'pending': True}

        try:
            check_access('ckanext_experience_update', context)
        except NotAuthorized:
            abort(401, _('User not authorized to edit {experience_id}').format(
                experience_id=id))

        return super(EditView, self).get(DATASET_TYPE_NAME, id, data,
                                         errors, error_summary)

    def post(self, id):
        context = self._prepare(id)

        data_dict = dataset.clean_dict(
            dataset.dict_fns.unflatten(
                dataset.tuplize_dict(dataset.parse_params(tk.request.form))))
        data_dict.update(
            dataset.clean_dict(
                dataset.dict_fns.unflatten(
                    dataset.tuplize_dict(dataset.parse_params(
                        tk.request.files)))))

        data_dict['id'] = id
        try:
            pkg = tk.get_action('ckanext_experience_update')(context, data_dict)
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

        c.pkg_dict = pkg

        # redirect to experience details page
        url = h.url_for('experience_blueprint.read', id=pkg['name'])
        return redirect(url)


def dataset_experience_list(id):
    '''
    Display a list of experiences a dataset is associated with, with an
    option to add to experience from a list.
    '''
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'for_view': True,
               'auth_user_obj': c.userobj}
    data_dict = {'id': id}

    try:
        check_access('package_show', context, data_dict)
    except NotFound:
        abort(404, _('Dataset not found'))
    except NotAuthorized:
        abort(401, _('Not authorized to see this page'))

    try:
        c.pkg_dict = get_action('package_show')(context, data_dict)
        c.experience_list = get_action('ckanext_package_experience_list')(
            context, {'package_id': c.pkg_dict['id']})
    except NotFound:
        abort(404, _('Dataset not found'))
    except NotAuthorized:
        abort(401, _('Unauthorized to read package'))

    if request.method == 'POST':

        form_data = tk.request.form

        # Are we adding the dataset to a experience?
        new_experience = form_data.get('experience_added')
        if new_experience:
            data_dict = {"experience_id": new_experience,
                         "package_id": c.pkg_dict['id']}
            try:
                get_action('ckanext_experience_package_association_create')(
                    context, data_dict)
            except NotFound:
                abort(404, _('Experience not found'))
            else:
                h.flash_success(
                    _("The dataset has been added to the experience."))

        # Are we removing a dataset from a experience?
        experience_to_remove = form_data.get('remove_experience_id')
        if experience_to_remove:
            data_dict = {"experience_id": experience_to_remove,
                         "package_id": c.pkg_dict['id']}
            try:
                get_action('ckanext_experience_package_association_delete')(
                    context, data_dict)
            except NotFound:
                abort(404, _('Experience not found'))
            else:
                h.flash_success(
                    _("The dataset has been removed from the experience."))
        redirect(h.url_for('experience_blueprint.dataset_experience_list', id=c.pkg_dict['name']))

    pkg_experience_ids = [experience['id'] for experience in c.experience_list]
    site_experiences = get_action('ckanext_experience_list')(context, {})

    c.experience_dropdown = [[experience['id'], experience['title']]
                             for experience in site_experiences
                             if experience['id'] not in pkg_experience_ids]

    return render("package/dataset_experience_list.html",
                  extra_vars={'pkg_dict': c.pkg_dict})


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

    form_data = request.form

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

        return redirect(h.url_for('experience_blueprint.admins'))

    c.experience_admins = get_action('ckanext_experience_admin_list')()

    return render('admin/manage_experience_admins.html')


def admin_remove():
    '''
    Remove a user from the Experience Admin list.
    '''
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}

    try:
        check_access('sysadmin', context, {})
    except NotAuthorized:
        abort(401, _('User not authorized to view page'))

    form_data = request.form

    if 'cancel' in form_data:
        tk.redirect_to('experience_blueprint.admins')

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

        return redirect(h.url_for('experience_blueprint.admins'))

    c.user_dict = get_action('user_show')(data_dict={'id': user_id})
    c.user_id = user_id
    return render('admin/confirm_remove_experience_admin.html')


def _add_dataset_search(experience_id, experience_name):
    '''
    Search logic for discovering datasets to add to a experience.
    '''

    from ckan.lib.search import SearchError

    package_type = 'dataset'

    # unicode format (decoded from utf8)
    q = c.q = tk.request.params.get('q', u'')
    c.query_error = False
    page = h.get_page_number(tk.request.params)

    limit = int(tk.config.get('ckan.datasets_per_page', 20))

    # most search operations should reset the page counter:
    params_nopage = [(k, v) for k, v in tk.request.params.items()
                     if k != 'page']

    def drill_down_url(alternative_url=None, **by):
        return h.add_url_param(alternative_url=alternative_url,
                               controller='dataset'
                               if tk.check_ckan_version('2.9') else 'package',
                               action='search',
                               new_params=by)

    c.drill_down_url = drill_down_url

    def remove_field(key, value=None, replace=None):
        return h.remove_url_param(key,
                                  value=value,
                                  replace=replace,
                                  controller='dataset' if
                                  tk.check_ckan_version('2.9') else 'package',
                                  action='search')

    c.remove_field = remove_field

    sort_by = tk.request.params.get('sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

    def _sort_by(fields):
        """
        Sort by the given list of fields.

        Each entry in the list is a 2-tuple: (fieldname, sort_order)

        eg - [('metadata_modified', 'desc'), ('name', 'asc')]

        If fields is empty, then the default ordering is used.
        """
        params = params_nosort[:]

        if fields:
            sort_string = ', '.join('%s %s' % f for f in fields)
            params.append(('sort', sort_string))
        return _search_url(params, experience_name)

    c.sort_by = _sort_by
    if sort_by is None:
        c.sort_by_fields = []
    else:
        c.sort_by_fields = [field.split()[0] for field in sort_by.split(',')]

    def pager_url(q=None, page=None):
        params = list(params_nopage)
        params.append(('page', page))
        return _search_url(params, experience_name)

    c.search_url_params = urlencode(_encode_params(params_nopage))

    try:
        c.fields = []
        # c.fields_grouped will contain a dict of params containing
        # a list of values eg {'tags':['tag1', 'tag2']}
        c.fields_grouped = {}
        search_extras = {}
        fq = ''
        for (param, value) in tk.request.params.items():
            if param not in ['q', 'page', 'sort'] \
                    and len(value) and not param.startswith('_'):
                if not param.startswith('ext_'):
                    c.fields.append((param, value))
                    fq += ' %s:"%s"' % (param, value)
                    if param not in c.fields_grouped:
                        c.fields_grouped[param] = [value]
                    else:
                        c.fields_grouped[param].append(value)
                else:
                    search_extras[param] = value

        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author,
            'for_view': True,
            'auth_user_obj': c.userobj
        }

        if package_type and package_type != 'dataset':
            # Only show datasets of this particular type
            fq += ' +dataset_type:{type}'.format(type=package_type)
        else:
            # Unless changed via config options, don't show non standard
            # dataset types on the default search page
            if not tk.asbool(
                    tk.config.get('ckan.search.show_all_types', 'False')):
                fq += ' +dataset_type:dataset'

        # Only search for packages that aren't already associated with the
        # Experience
        associated_package_ids = ExperiencePackageAssociation.get_package_ids_for_experience(experience_id)
        # flatten resulting list to space separated string
        if associated_package_ids:
            associated_package_ids_str = \
                ' OR '.join([id[0] for id in associated_package_ids])
            fq += ' !id:({0})'.format(associated_package_ids_str)

        facets = OrderedDict()

        default_facet_titles = {
            'organization': _('Organizations'),
            'groups': _('Groups'),
            'tags': _('Tags'),
            'res_format': _('Formats'),
            'license_id': _('Licenses'),
        }

        # for CKAN-Versions that do not provide the facets-method from
        # helper-context, import facets from ckan.common
        if hasattr(h, 'facets'):
            current_facets = h.facets()
        else:
            from ckan.common import g
            current_facets = g.facets

        for facet in current_facets:
            if facet in default_facet_titles:
                facets[facet] = default_facet_titles[facet]
            else:
                facets[facet] = facet

        # Facet titles
        for plugin in p.PluginImplementations(p.IFacets):
            facets = plugin.dataset_facets(facets, package_type)

        c.facet_titles = facets

        data_dict = {
            'q': q,
            'fq': fq.strip(),
            'facet.field': list(facets.keys()),
            'rows': limit,
            'start': (page - 1) * limit,
            'sort': sort_by,
            'extras': search_extras
        }

        query = tk.get_action('package_search')(context, data_dict)
        c.sort_by_selected = query['sort']

        c.page = h.Page(collection=query['results'],
                        page=page,
                        url=pager_url,
                        item_count=query['count'],
                        items_per_page=limit)
        c.facets = query['facets']
        c.search_facets = query['search_facets']
        c.page.items = query['results']
    except SearchError as se:
        log.error('Dataset search error: %r', se.args)
        c.query_error = True
        c.facets = {}
        c.search_facets = {}
        c.page = h.Page(collection=[])
    c.search_facets_limits = {}
    for facet in c.search_facets.keys():
        try:
            limit = int(
                tk.request.params.get(
                    '_%s_limit' % facet,
                    int(tk.config.get('search.facets.default', 10))))
        except tk.ValueError:
            abort(
                400,
                _("Parameter '{parameter_name}' is not an integer").format(
                    parameter_name='_%s_limit' % facet))
        c.search_facets_limits[facet] = limit


def _search_url(params, name):
    url = h.url_for('experience_blueprint.manage_datasets', id=name)
    return url_with_params(url, params)


def _encode_params(params):
    return [(k, six.ensure_str(six.text_type(v))) for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


def manage_datasets(id):
    '''
    List datasets associated with the given experience id.
    '''

    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}
    data_dict = {'id': id}

    try:
        check_access('ckanext_experience_update', context)
    except NotAuthorized:
        abort(401, _('User not authorized to edit {experience_id}').format(
            experience_id=id))

    # check if experience exists
    try:
        c.pkg_dict = get_action('package_show')(context, data_dict)
    except NotFound:
        abort(404, _('Experience not found'))
    except NotAuthorized:
        abort(401, _('Unauthorized to read experience'))

    form_data = request.form

    # Are we removing a experience/dataset association?
    if (request.method == 'POST'
            and 'bulk_action.experience_remove' in form_data):
        # Find the datasets to perform the action on, they are prefixed by
        # dataset_ in the form data
        dataset_ids = []
        for param in form_data:
            if param.startswith('dataset_'):
                dataset_ids.append(param[8:])
        if dataset_ids:
            for dataset_id in dataset_ids:
                get_action('ckanext_experience_package_association_delete')(
                    context,
                    {'experience_id': c.pkg_dict['id'],
                     'package_id': dataset_id})
            h.flash_success(
                tk.ungettext(
                    "The dataset has been removed from the experience.",
                    "The datasets have been removed from the experience.",
                    len(dataset_ids)))
            url = h.url_for('experience_blueprint.manage_datasets', id=id)
            redirect(url)

    # Are we creating a experience/dataset association?
    elif (request.method == 'POST'
          and 'bulk_action.experience_add' in form_data):
        # Find the datasets to perform the action on, they are prefixed by
        # dataset_ in the form data
        dataset_ids = []
        for param in form_data:
            if param.startswith('dataset_'):
                dataset_ids.append(param[8:])
        if dataset_ids:
            successful_adds = []
            for dataset_id in dataset_ids:
                try:
                    get_action(
                        'ckanext_experience_package_association_create')(
                        context, {'experience_id': c.pkg_dict['id'],
                                  'package_id': dataset_id})
                except ValidationError as e:
                    h.flash_notice(e.error_summary)
                else:
                    successful_adds.append(dataset_id)
            if successful_adds:
                h.flash_success(
                    tk.ungettext(
                        "The dataset has been added to the experience.",
                        "The datasets have been added to the experience.",
                        len(successful_adds)))
            url = h.url_for('experience_blueprint.manage_datasets', id=id)
            redirect(url)

    _add_dataset_search(c.pkg_dict['id'], c.pkg_dict['name'])

    # get experience packages
    c.experience_pkgs = get_action('ckanext_experience_package_list')(
        context, {'experience_id': c.pkg_dict['id']})

    return render('experience/manage_datasets.html')


experience.add_url_rule('/experience',
                        view_func=index)
experience.add_url_rule('/experience/new',
                        view_func=CreateView.as_view('new'))
experience.add_url_rule('/experience/delete/<id>',
                        view_func=delete,
                        methods=[u'GET', u'POST'])
experience.add_url_rule('/experience/edit/<id>',
                        view_func=EditView.as_view('edit'),
                        methods=[u'GET', u'POST'])
experience.add_url_rule('/dataset/experience/<id>',
                        view_func=dataset_experience_list,
                        methods=[u'GET', u'POST'])
experience.add_url_rule('/experience/<id>', view_func=read)
experience.add_url_rule('/experience/manage_datasets/<id>',
                        view_func=manage_datasets,
                        methods=[u'GET', u'POST'])
experience.add_url_rule('/ckan-admin/experience_admins',
                        view_func=admins,
                        methods=[u'GET', u'POST'])
experience.add_url_rule('/ckan-admin/experience_admin_remove',
                        view_func=admin_remove,
                        methods=[u'GET', u'POST'])


def get_blueprints():
    return [experience]
