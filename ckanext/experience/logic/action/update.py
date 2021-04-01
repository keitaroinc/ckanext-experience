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

import logging

import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


def experience_update(context, data_dict):

    # If get_uploader is available (introduced for IUploader in CKAN 2.5), use
    # it, otherwise use the default uploader.
    # https://github.com/ckan/ckan/pull/2510
    try:
        upload = uploader.get_uploader('experience', data_dict['image_url'])
    except AttributeError:
        upload = uploader.Upload('experience', data_dict['image_url'])

    upload.update_data_dict(data_dict, 'image_url',
                            'image_upload', 'clear_upload')

    upload.upload(uploader.get_max_image_size())

    pkg = toolkit.get_action('package_update')(context, data_dict)

    return pkg
