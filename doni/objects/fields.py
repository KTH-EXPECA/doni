# Copyright 2015 Red Hat, Inc.
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

from oslo_versionedobjects import fields as object_fields

from doni.worker import WorkerState


class IntegerField(object_fields.IntegerField):
    pass


class UUIDField(object_fields.UUIDField):
    pass


class StringField(object_fields.StringField):
    pass


class DateTimeField(object_fields.DateTimeField):
    pass


class BooleanField(object_fields.BooleanField):
    pass


class EnumField(object_fields.EnumField):
    pass


class WorkerStateField(object_fields.StateMachine):
    STEADY = WorkerState.STEADY
    PENDING = WorkerState.PENDING
    IN_PROGRESS = WorkerState.IN_PROGRESS
    ERROR = WorkerState.ERROR

    ALLOWED_TRANSITIONS = {
        STEADY: {
            PENDING,
        },
        PENDING: {
            IN_PROGRESS,
        },
        IN_PROGRESS: {
            STEADY,
            ERROR
        },
        ERROR: {
            PENDING,
        },
    }

    _TYPES = (STEADY, PENDING, IN_PROGRESS, ERROR)

    def __init__(self, **kwargs):
        super().__init__(self._TYPES, **kwargs)


class FlexibleDict(object_fields.FieldType):
    pass


class FlexibleDictField(object_fields.AutoTypedField):
    AUTO_TYPE = FlexibleDict()
