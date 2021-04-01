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

import ckan.model as model
import ckan.lib.navl.dictization_functions as df
from ckan.common import _


def convert_package_name_or_id_to_title_or_name(package_name_or_id, context):
    '''
    Return the package title, or name if no title, for the given package name
    or id.

    :returns: the name of the package with the given name or id
    :rtype: string
    :raises: ckan.lib.navl.dictization_functions.Invalid if there is no
        package with the given name or id

    '''
    session = context['session']
    result = session.query(model.Package).filter_by(
            id=package_name_or_id).first()
    if not result:
        result = session.query(model.Package).filter_by(
                name=package_name_or_id).first()
    if not result:
        raise df.Invalid('%s: %s' % (_('Not found'), _('Dataset')))
    return result.title or result.name
