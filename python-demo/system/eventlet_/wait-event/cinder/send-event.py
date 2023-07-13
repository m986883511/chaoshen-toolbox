import logging
from . import message_api, db_base, message_field
from . import db_base

from novaclient import client as nova_client

LOG = logging.getLogger()


def novaclient(context, privileged_user=False, timeout=None, api_version=None):
    """Returns a Nova client

    @param privileged_user:
        If True, use the account from configuration
        (requires 'auth_type' and the other usual Keystone authentication
        options to be set in the [nova] section)
    @param timeout:
        Number of seconds to wait for an answer before raising a
        Timeout exception (None to disable)
    @param api_version:
        api version of nova
    """

    if privileged_user and CONF[NOVA_GROUP].auth_type:
        LOG.debug('Creating Keystone auth plugin from conf')
        n_auth = ks_loading.load_auth_from_conf_options(CONF, NOVA_GROUP)
    else:
        if CONF[NOVA_GROUP].token_auth_url:
            url = CONF[NOVA_GROUP].token_auth_url
        else:
            url = _get_identity_endpoint_from_sc(context)
        LOG.debug('Creating Keystone token plugin using URL: %s', url)
        n_auth = identity.Token(auth_url=url,
                                token=context.auth_token,
                                project_name=context.project_name,
                                project_domain_id=context.project_domain_id)

    if CONF.auth_strategy == 'keystone':
        n_auth = service_auth.get_auth_plugin(context, auth=n_auth)

    keystone_session = ks_loading.load_session_from_conf_options(
        CONF,
        NOVA_GROUP,
        auth=n_auth)

    c = nova_client.Client(
        api_versions.APIVersion(api_version or NOVA_API_VERSION),
        session=keystone_session,
        insecure=CONF[NOVA_GROUP].insecure,
        timeout=timeout,
        region_name=CONF[NOVA_GROUP].region_name,
        endpoint_type=CONF[NOVA_GROUP].interface,
        cacert=CONF[NOVA_GROUP].cafile,
        global_request_id=context.global_id,
        extensions=nova_extensions)

    return c
class ClientException(Exception):
    """
    The base exception class for all exceptions this library raises.
    """
    message = 'Unknown Error'

    def __init__(self, code, message=None, details=None, request_id=None,
                 url=None, method=None):
        self.code = code
        self.message = message or self.__class__.message
        self.details = details
        self.request_id = request_id
        self.url = url
        self.method = method

    def __str__(self):
        formatted_string = "%s (HTTP %s)" % (self.message, self.code)
        if self.request_id:
            formatted_string += " (Request-ID: %s)" % self.request_id

        return formatted_string


class NotFound(ClientException):
    """
    HTTP 404 - Not found
    """
    http_status = 404
    message = "Not found"


class API(db_base):
    """API for interacting with novaclient."""
    NotFound = NotFound

    def __init__(self):
        self.message_api = message_api.API()
        super().__init__()

    def _get_volume_reimaged_event(self, server_id, volume_id):
        return {'name': 'volume-reimaged', 'server_uuid': server_id, 'tag': volume_id}

    def reimage_volume(self, context, server_ids, volume_id):
        api_version = '2.93'
        events = [self._get_volume_reimaged_event(server_id, volume_id)
                  for server_id in server_ids]
        result = self._send_events(context, events, api_version=api_version)
        if not result:
            self.message_api.create(
                context,
                message_field.Action.REIMAGE_VOLUME,
                resource_uuid=volume_id,
                detail=message_field.Detail.REIMAGE_VOLUME_FAILED)
        return result

    def _send_events(self, context, events, api_version=None):
        nova = novaclient(context, privileged_user=True, api_version=api_version)
        try:
            response = nova.server_external_events.create(events)
        except nova_exceptions.NotFound:
            LOG.warning('Nova returned NotFound for events: %s.', events)
            return False
        except Exception:
            LOG.exception('Failed to notify nova on events: %s.', events)
            return False
        else:
            if not isinstance(response, list):
                LOG.error('Error response returned from nova: %s.', response)
                return False
            response_error = False
            for event in response:
                code = event.get('code')
                if code is None:
                    response_error = True
                    continue
                if code != 200:
                    LOG.warning(
                        'Nova event: %s returned with failed status.', event)
                else:
                    LOG.info('Nova event response: %s.', event)
            if response_error:
                LOG.error('Error response returned from nova: %s.', response)
                return False
        return True
