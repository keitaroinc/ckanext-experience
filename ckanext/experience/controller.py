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

from urllib import urlencode
import logging

from pylons import config

from ckan.plugins import toolkit as tk
import ckan.model as model
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.plugins as p
from ckan.common import OrderedDict, ungettext
from ckan.controllers.package import (PackageController,
                                      url_with_params,
                                      _encode_params)

from ckanext.experience.model import ExperiencePackageAssociation
from ckanext.experience.plugin import DATASET_TYPE_NAME

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


class ExperienceController(PackageController):

    def new(self, data=None, errors=None, error_summary=None):

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

        return super(ExperienceController, self).new(data=data, errors=errors,
                                                   error_summary=error_summary)

    def edit(self, id, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params,
                   'moderated': config.get('moderated'),
                   'pending': True}

        try:
            check_access('ckanext_experience_update', context)
        except NotAuthorized:
            abort(401, _('User not authorized to edit {experience_id}').format(
                experience_id=id))

        return super(ExperienceController, self).edit(
            id, data=data, errors=errors, error_summary=error_summary)

    def _guess_package_type(self, expecting_name=False):
        """Experience packages are always DATASET_TYPE_NAME."""

        return DATASET_TYPE_NAME

    def _save_new(self, context, package_type=None):
        '''
        The experience is created then redirects to the manage_dataset page to
        associated packages with the new experience.
        '''

        data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.POST))))

        data_dict['type'] = package_type
        context['message'] = data_dict.get('log_message', '')

        try:
            pkg_dict = get_action('ckanext_experience_create')(context,
                                                             data_dict)
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            data_dict['state'] = 'none'
            return self.new(data_dict, errors, error_summary)

        # redirect to manage datasets
        url = h.url_for(
            controller='ckanext.experience.controller:ExperienceController',
            action='manage_datasets', id=pkg_dict['name'])
        redirect(url)

    def _save_edit(self, name_or_id, context, package_type=None):
        '''
        Edit a experience's details, then redirect to the experience read page.
        '''

        data_dict = clean_dict(dict_fns.unflatten(
            tuplize_dict(parse_params(request.POST))))

        data_dict['id'] = name_or_id
        try:
            pkg = get_action('ckanext_experience_update')(context, data_dict)
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(name_or_id, data_dict, errors, error_summary)

        c.pkg_dict = pkg

        # redirect to experience details page
        url = h.url_for(
            controller='ckanext.experience.controller:ExperienceController',
            action='read', id=pkg['name'])
        redirect(url)

    def read(self, id, format='html'):
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
        return render(self._read_template(package_type),
                      extra_vars={'dataset_type': package_type})

    def delete(self, id):
        if 'cancel' in request.params:
            tk.redirect_to(
                controller='ckanext.experience.controller:ExperienceController',
                action='edit', id=id)

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
                tk.redirect_to(
                    controller='ckanext.experience.controller:ExperienceController',
                    action='search')
            c.pkg_dict = get_action('package_show')(context, {'id': id})
        except NotAuthorized:
            abort(401, _('Unauthorized to delete experience'))
        except NotFound:
            abort(404, _('Experience not found'))
        return render('experience/confirm_delete.html',
                      extra_vars={'dataset_type': DATASET_TYPE_NAME})

    def dataset_experience_list(self, id):
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
        except logic.NotAuthorized:
            abort(401, _('Unauthorized to read package'))

        if request.method == 'POST':
            # Are we adding the dataset to a experience?
            new_experience = request.POST.get('experience_added')
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
            experience_to_remove = request.POST.get('remove_experience_id')
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
            redirect(h.url_for(
                controller='ckanext.experience.controller:ExperienceController',
                action='dataset_experience_list', id=c.pkg_dict['name']))

        pkg_experience_ids = [experience['id'] for experience in c.experience_list]
        site_experiences = get_action('ckanext_experience_list')(context, {})

        c.experience_dropdown = [[experience['id'], experience['title']]
                               for experience in site_experiences
                               if experience['id'] not in pkg_experience_ids]

        return render("package/dataset_experience_list.html")

    def manage_datasets(self, id):
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

        # Are we removing a experience/dataset association?
        if (request.method == 'POST'
                and 'bulk_action.experience_remove' in request.params):
            # Find the datasets to perform the action on, they are prefixed by
            # dataset_ in the form data
            dataset_ids = []
            for param in request.params:
                if param.startswith('dataset_'):
                    dataset_ids.append(param[8:])
            if dataset_ids:
                for dataset_id in dataset_ids:
                    get_action('ckanext_experience_package_association_delete')(
                        context,
                        {'experience_id': c.pkg_dict['id'],
                         'package_id': dataset_id})
                h.flash_success(
                    ungettext(
                        "The dataset has been removed from the experience.",
                        "The datasets have been removed from the experience.",
                        len(dataset_ids)))
                url = h.url_for(
                    controller='ckanext.experience.controller:ExperienceController',
                    action='manage_datasets', id=id)
                redirect(url)

        # Are we creating a experience/dataset association?
        elif (request.method == 'POST'
                and 'bulk_action.experience_add' in request.params):
            # Find the datasets to perform the action on, they are prefixed by
            # dataset_ in the form data
            dataset_ids = []
            for param in request.params:
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
                        ungettext(
                            "The dataset has been added to the experience.",
                            "The datasets have been added to the experience.",
                            len(successful_adds)))
                url = h.url_for(
                    controller='ckanext.experience.controller:ExperienceController',
                    action='manage_datasets', id=id)
                redirect(url)

        self._add_dataset_search(c.pkg_dict['id'], c.pkg_dict['name'])

        # get experience packages
        c.experience_pkgs = get_action('ckanext_experience_package_list')(
            context, {'experience_id': c.pkg_dict['id']})

        return render('experience/manage_datasets.html')

    def _search_url(self, params, name):
        url = h.url_for(
            controller='ckanext.experience.controller:ExperienceController',
            action='manage_datasets', id=name)
        return url_with_params(url, params)

    def _add_dataset_search(self, experience_id, experience_name):
        '''
        Search logic for discovering datasets to add to a experience.
        '''

        from ckan.lib.search import SearchError

        package_type = 'dataset'

        # unicode format (decoded from utf8)
        q = c.q = request.params.get('q', u'')
        c.query_error = False
        if p.toolkit.check_ckan_version(min_version='2.5.0', max_version='2.5.3'):
            page = self._get_page_number(request.params)
        else:
            page = h.get_page_number(request.params)

        limit = int(config.get('ckan.datasets_per_page', 20))

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']

        def drill_down_url(alternative_url=None, **by):
            return h.add_url_param(alternative_url=alternative_url,
                                   controller='package', action='search',
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='package', action='search')

        c.remove_field = remove_field

        sort_by = request.params.get('sort', None)
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
            return self._search_url(params, experience_name)

        c.sort_by = _sort_by
        if sort_by is None:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return self._search_url(params, experience_name)

        c.search_url_params = urlencode(_encode_params(params_nopage))

        try:
            c.fields = []
            # c.fields_grouped will contain a dict of params containing
            # a list of values eg {'tags':['tag1', 'tag2']}
            c.fields_grouped = {}
            search_extras = {}
            fq = ''
            for (param, value) in request.params.items():
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

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'for_view': True,
                       'auth_user_obj': c.userobj}

            if package_type and package_type != 'dataset':
                # Only show datasets of this particular type
                fq += ' +dataset_type:{type}'.format(type=package_type)
            else:
                # Unless changed via config options, don't show non standard
                # dataset types on the default search page
                if not tk.asbool(config.get('ckan.search.show_all_types',
                                            'False')):
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
                'facet.field': facets.keys(),
                'rows': limit,
                'start': (page - 1) * limit,
                'sort': sort_by,
                'extras': search_extras
            }

            query = get_action('package_search')(context, data_dict)
            c.sort_by_selected = query['sort']

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )
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
                limit = int(request.params.get('_%s_limit' % facet,
                                               int(config.get('search.facets.default', 10))))
            except ValueError:
                abort(400, _("Parameter '{parameter_name}' is not an integer").format(
                                 parameter_name='_%s_limit' % facet
                             ))
            c.search_facets_limits[facet] = limit

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
                controller='ckanext.experience.controller:ExperienceController',
                action='manage_experience_admins'))

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
                controller='ckanext.experience.controller:ExperienceController',
                action='manage_experience_admins')

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
                controller='ckanext.experience.controller:ExperienceController',
                action='manage_experience_admins'))

        c.user_dict = get_action('user_show')(data_dict={'id': user_id})
        c.user_id = user_id
        return render('admin/confirm_remove_experience_admin.html')
