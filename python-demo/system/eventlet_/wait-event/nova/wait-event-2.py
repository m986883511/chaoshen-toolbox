import logging
import eventlet
import contextlib

from oslo_utils import timeutils

import objects

LOG = logging.getLogger(__name__)


# /nova/exception.py
class NovaException(Exception):
    """Base Nova Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        try:
            if not message:
                message = self.msg_fmt % kwargs
            else:
                message = str(message)
        except Exception as e:
            # NOTE(melwitt): This is done in a separate method so it can be
            # monkey-patched during testing to make it a hard failure.
            print(str(e))
            self._log_exception()
            message = self.msg_fmt

        self.message = message
        super(NovaException, self).__init__(message)

    def _log_exception(self):
        # kwargs doesn't match a variable in the message
        # log the issue and the kwargs
        LOG.exception('Exception in string format operation')
        for name, value in self.kwargs.items():
            print("%s: %s" % (name, value))  # noqa

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full NovaException message, (see __init__)
        return self.args[0]

    def __repr__(self):
        dict_repr = self.__dict__
        dict_repr['class'] = self.__class__.__name__
        return str(dict_repr)


class VirtAPI(object):
    @contextlib.contextmanager
    def wait_for_instance_event(self, instance, event_names, deadline=300,
                                error_callback=None):
        raise NotImplementedError()

    def exit_wait_early(self, events):
        raise NotImplementedError()

    def update_compute_provider_status(self, context, rp_uuid, enabled):
        """Used to add/remove the COMPUTE_STATUS_DISABLED trait on the provider

        :param context: nova auth RequestContext
        :param rp_uuid: UUID of a compute node resource provider in Placement
        :param enabled: True if the node is enabled in which case the trait
            would be removed, False if the node is disabled in which case
            the trait would be added.
        """
        raise NotImplementedError()


# _InstanceEvents = typing.Dict[typing.Tuple[str, str], eventlet.event.Event]


class InstanceEvents(object):
    def __init__(self):
        self._events = {}

    @staticmethod
    def _lock_name(instance):
        return '%s-%s' % (instance.uuid, 'events')

    def prepare_for_instance_event(
            self,
            instance,
            name,
            tag,
    ):
        """Prepare to receive an event for an instance.

        This will register an event for the given instance that we will
        wait on later. This should be called before initiating whatever
        action will trigger the event. The resulting eventlet.event.Event
        object should be wait()'d on to ensure completion.

        :param instance: the instance for which the event will be generated
        :param name: the name of the event we're expecting
        :param tag: the tag associated with the event we're expecting
        :returns: an event object that should be wait()'d on
        """

        # @utils.synchronized(self._lock_name(instance))
        def _create_or_get_event():
            if self._events is None:
                # NOTE(danms): We really should have a more specific error
                # here, but this is what we use for our default error case
                raise Exception(
                    'In shutdown, no new events can be scheduled')

            instance_events = self._events.setdefault(instance.uuid, {})
            return instance_events.setdefault((name, tag),
                                              eventlet.event.Event())

        print('Preparing to wait for external event %(name)s-%(tag)s',
              {'name': name, 'tag': tag})
        return _create_or_get_event()

    def pop_instance_event(self, instance, event):
        """Remove a pending event from the wait list.

        This will remove a pending event from the wait list so that it
        can be used to signal the waiters to wake up.

        :param instance: the instance for which the event was generated
        :param event: the nova.objects.external_event.InstanceExternalEvent
                      that describes the event
        :returns: the eventlet.event.Event object on which the waiters
                  are blocked
        """
        no_events_sentinel = object()
        no_matching_event_sentinel = object()

        # @utils.synchronized(self._lock_name(instance))
        def _pop_event():
            if self._events is None:
                print('Unexpected attempt to pop events during shutdown')
                return no_events_sentinel
            events = self._events.get(instance.uuid)
            if not events:
                return no_events_sentinel
            _event = events.pop((event.name, event.tag), None)
            if not events:
                del self._events[instance.uuid]
            if _event is None:
                return no_matching_event_sentinel
            return _event

        result = _pop_event()
        if result is no_events_sentinel:
            print('No waiting events found dispatching %(event)s',
                  {'event': event.key})
            return None
        elif result is no_matching_event_sentinel:
            print(
                'No event matching %(event)s in %(events)s',
                {
                    'event': event.key,
                    # mypy can't identify the none check in _pop_event
                    'events': self._events.get(  # type: ignore
                        instance.uuid, {}).keys(),
                }
            )
            return None
        else:
            return result

    def clear_events_for_instance(self, instance):
        """Remove all pending events for an instance.

        This will remove all events currently pending for an instance
        and return them (indexed by event name).

        :param instance: the instance for which events should be purged
        :returns: a dictionary of {event_name: eventlet.event.Event}
        """

        # @utils.synchronized(self._lock_name(instance))
        def _clear_events():
            if self._events is None:
                print('Unexpected attempt to clear events during shutdown')
                return dict()
            # NOTE(danms): We have historically returned the raw internal
            # format here, which is {event.key: [events, ...])} so just
            # trivially convert it here.
            return {'%s-%s' % k: e
                    for k, e in self._events.pop(instance.uuid, {}).items()}

        return _clear_events()

    def cancel_all_events(self):
        if self._events is None:
            print('Unexpected attempt to cancel events during shutdown.')
            return
        our_events = self._events
        # NOTE(danms): Block new events
        self._events = None

        for instance_uuid, events in our_events.items():
            for (name, tag), eventlet_event in events.items():
                print('Canceling in-flight event %(name)s-%(tag)s for '
                      'instance %(instance_uuid)s',
                      {'name': name,
                       'tag': tag,
                       'instance_uuid': instance_uuid})
                event = objects.InstanceExternalEvent(
                    instance_uuid=instance_uuid,
                    name=name, status='failed',
                    tag=tag, data={})
                eventlet_event.send(event)


# /nova/nova/virtapi.py
class ComputeVirtAPI(VirtAPI):
    def __init__(self, compute):
        super(ComputeVirtAPI, self).__init__()
        self._compute = compute

        # self.reportclient = compute.reportclient

        class ExitEarly(Exception):
            def __init__(self, events):
                super(Exception, self).__init__()
                self.events = events

        self._exit_early_exc = ExitEarly

    @staticmethod
    def _wait_for_instance_events(
            instance,
            events,
            error_callback,
    ):
        for event_name, event in events.items():
            if event.is_received_early():
                continue
            else:
                actual_event = event.wait()
                if actual_event.status == 'completed':
                    continue
            # If we get here, we have an event that was not completed,
            # nor skipped via exit_wait_early(). Decide whether to
            # keep waiting by calling the error_callback() hook.
            decision = error_callback(event_name, instance)
            if decision is False:
                break

    class _InstanceEvent:
        EXPECTED = "expected"
        WAITING = "waiting"
        RECEIVED = "received"
        RECEIVED_EARLY = "received early"
        TIMED_OUT = "timed out"
        RECEIVED_NOT_PROCESSED = "received but not processed"

        def __init__(self, name, event):
            self.name = name
            self.event = event
            self.status = self.EXPECTED
            self.wait_time = None

        def mark_as_received_early(self):
            self.status = self.RECEIVED_EARLY

        def is_received_early(self):
            return self.status == self.RECEIVED_EARLY

        def _update_status_no_wait(self):
            if self.status == self.EXPECTED and self.event.ready():
                self.status = self.RECEIVED_NOT_PROCESSED

        def wait(self):
            self.status = self.WAITING
            try:
                with timeutils.StopWatch() as sw:
                    instance_event = self.event.wait()
            except eventlet.timeout.Timeout:
                self.status = self.TIMED_OUT
                self.wait_time = sw.elapsed()

                raise

            self.status = self.RECEIVED
            self.wait_time = sw.elapsed()
            return instance_event

        def __str__(self):
            self._update_status_no_wait()
            if self.status == self.EXPECTED:
                return "{}: expected but not received".format(self.name)
            if self.status == self.RECEIVED:
                return ("{}: received after waiting {:.2f} seconds".format(self.name, self.wait_time))
            if self.status == self.TIMED_OUT:
                return ("{}: timed out after {:.2f} seconds".format(self.name, self.wait_time))
            return "{}: {}".format(self.name, self.status)

    @contextlib.contextmanager
    def wait_for_instance_event(self, instance, event_names, deadline=300, error_callback=None):
        if error_callback is None:
            error_callback = self._default_error_callback
        events = {}
        for event_name in event_names:
            name, tag = event_name
            event_name = objects.InstanceExternalEvent.make_key(name, tag)
            try:
                event = (self._compute.instance_events.prepare_for_instance_event(instance, name, tag))
                # event = (self._compute.instance_events.prepare_for_instance_event(instance, name, tag))
                events[event_name] = self._InstanceEvent(event_name, event)
            except NovaException:
                error_callback(event_name, instance)
                # NOTE(danms): Don't wait for any of the events. They
                # should all be canceled and fired immediately below,
                # but don't stick around if not.
                deadline = 0
        try:
            yield
        except self._exit_early_exc as e:
            early_events = set([objects.InstanceExternalEvent.make_key(n, t) for n, t in e.events])

            # If there are expected events that received early, mark them,
            # so they won't be waited for later
            for early_event_name in early_events:
                if early_event_name in events:
                    events[early_event_name].mark_as_received_early()

        sw = timeutils.StopWatch()
        sw.start()
        try:
            with eventlet.timeout.Timeout(deadline):
                self._wait_for_instance_events(instance, events, error_callback)
        except eventlet.timeout.Timeout:
            _events = list(events.keys())
            vm_state = instance.vm_state
            task_state = instance.task_state
            event_states = ', '.join([str(event) for event in events.values()])
            print('Timeout waiting for {} for instance with vm_state {} and task_state {}. Event states are: {}'.format(
                _events, vm_state, task_state, event_states
            ))

            raise

        elapsed = sw.elapsed()
        event_names = ','.join(x[0] for x in event_names)
        print('Instance event wait completed in {} seconds for {}'.format(elapsed, event_names))


class ComputeManager():
    def __init__(self, compute_driver=None, *args, **kwargs):
        self.virtapi = ComputeVirtAPI(self)
        self.instance_events = InstanceEvents()


class Instance():
    def __init__(self, uuid):
        self.uuid = uuid
        self.vm_state = 'active'
        self.task_state = None


if __name__ == '__main__':
    def err_callback(event_name, instance):
        print('err_callback: {}'.format(event_name))
        return True


    manager = ComputeManager()
    events = [('volume-reimaged', 'volume_id')]
    instance = Instance('uuid')
    with manager.virtapi.wait_for_instance_event(instance, event_names=events, deadline=5, error_callback=err_callback):
        print('wait_for_instance_event')
