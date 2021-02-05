# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Doni test utilities."""

from oslo_utils import uuidutils


def get_test_hardware(**kw):
    default_uuid = uuidutils.generate_uuid()
    return {
        'created_at': kw.get('created_at'),
        'updated_at': kw.get('updated_at'),
        'id': kw.get('id', 234),
        'name': kw.get('name', u'fake_name'),
        'uuid': kw.get('uuid', default_uuid),
        'project_id': kw.get('project_id', 'fake_project_id'),
    }
