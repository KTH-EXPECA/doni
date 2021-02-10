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
