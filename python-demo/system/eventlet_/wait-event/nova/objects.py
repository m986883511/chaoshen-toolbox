# from nova.objects import base as obj_base
# from nova.objects import fields

from oslo_versionedobjects import base as ovoo_base
from oslo_versionedobjects import fields

EVENT_NAMES = [
    # Network has changed for this instance, rebuild info_cache
    'network-changed',

    # VIF plugging notifications, tag is port_id
    'network-vif-plugged',
    'network-vif-unplugged',
    'network-vif-deleted',

    # Volume was extended for this instance, tag is volume_id
    'volume-extended',

    # Power state has changed for this instance
    'power-update',

    # Accelerator Request got bound, tag is ARQ uuid.
    # Sent when an ARQ for an instance has been bound or failed to bind.
    'accelerator-request-bound',

    # re-image operation has completed from cinder side
    'volume-reimaged',
]

EVENT_STATUSES = ['failed', 'completed', 'in-progress']

# Possible tag values for the power-update event.
POWER_ON = 'POWER_ON'
POWER_OFF = 'POWER_OFF'


# nova/objects/base.py
class NovaObject(ovoo_base.VersionedObject):
    """Base class and object factory.

    This forms the base of all objects that can be remoted or instantiated
    via RPC. Simply defining a class that inherits from this base class
    will make it remotely instantiatable. Objects should implement the
    necessary "get" classmethod routines as well as "save" object methods
    as appropriate.
    """

    OBJ_SERIAL_NAMESPACE = 'nova_object'
    OBJ_PROJECT_NAMESPACE = 'nova'

    # NOTE(ndipanov): This is nova-specific
    @staticmethod
    def should_migrate_data():
        """A check that can be used to inhibit online migration behavior

        This is usually used to check if all services that will be accessing
        the db directly are ready for the new format.
        """
        raise NotImplementedError()

    # NOTE(danms): This is nova-specific

    def obj_alternate_context(self, context):
        original_context = self._context
        self._context = context
        try:
            yield
        finally:
            self._context = original_context


# nova/objects/external_event.py
class InstanceExternalEvent(NovaObject):
    # Version 1.0: Initial version
    #              Supports network-changed and vif-plugged
    # Version 1.1: adds network-vif-deleted event
    # Version 1.2: adds volume-extended event
    # Version 1.3: adds power-update event
    # Version 1.4: adds accelerator-request-bound event
    # Version 1.5: adds volume-reimaged event
    VERSION = '1.5'

    fields = {
        'instance_uuid': fields.UUIDField(),
        'name': fields.EnumField(valid_values=EVENT_NAMES),
        'status': fields.EnumField(valid_values=EVENT_STATUSES),
        'tag': fields.StringField(nullable=True),
        'data': fields.DictOfStringsField(),
    }

    @staticmethod
    def make_key(name, tag=None):
        if tag is not None:
            return '%s-%s' % (name, tag)
        else:
            return name

    @property
    def key(self):
        return self.make_key(self.name, self.tag)
