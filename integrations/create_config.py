#! /usr/bin/env python3

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from pprint import pprint
import requests
import sys


@dataclass
class ConfigSet:
    schema_id: str
    auth: Optional[Dict[str, Any]] = None
    connect: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


@dataclass
class CreateIntegrationAccessConfigRequest:
    config_set: ConfigSet
    enabled: bool
    label: Optional[str] = None
    contact_info: Optional[str] = None
    external_console_link: Optional[str] = None
    runner_id: Optional[str] = None


@dataclass
class CreateIntegrationConfigRequest:
    access_config_id: str
    config_set: ConfigSet
    enabled: bool
    label: Optional[str] = None


# Integration Configurations contain 2 models.  The AccessConfig defines "how" we connect to the source.  eg creds and comms
# A single access config can be shared across multiple integration configs
@dataclass
class AccessConfig:
    org_id: str
    platform_id: str
    id: str
    config_set: ConfigSet
    enabled: bool
    created_timestamp: datetime
    last_updated_timestamp: datetime
    runner_id: Optional[str] = None
    label: Optional[str] = None
    contact_info: Optional[str] = None
    external_console_link: Optional[str] = None


# The IntegrationConfig defines the "what" we collect from the integration
@dataclass
class IntegrationConfig:
    org_id: str
    platform_id: str
    integration_id: str
    id: str
    access_config_id: str
    config_set: ConfigSet
    enabled: bool
    created_timestamp: datetime
    last_updated_timestamp: datetime
    label: Optional[str] = None


# Config schemas define which parameters are available when configuring each integration
# They are in JsonSchema format defining requirements for auth, connect, and settings config sections (`ConfigSet`)
def list_integration_access_schemas(platform_id: str, token: str, target_org: Optional[str]=None) -> List[Dict[str, Any]]:
    headers = {"Authorization": token}
    if target_org:
        headers['X-Sevco-Target-Org'] = target_org

    resp = requests.get(f"https://api.sev.co/v3/integration-platform/{platform_id}/access/schema", headers=headers)
    resp.raise_for_status()

    return resp.json()['items']


def list_integration_schemas(platform_id: str, integration_id: str, token: str, target_org: Optional[str]=None) -> List[Dict[str, Any]]:
    headers = {"Authorization": token}
    if target_org:
        headers['X-Sevco-Target-Org'] = target_org

    resp = requests.get(f"https://api.sev.co/v3/integration-platform/{platform_id}/integration/{integration_id}/schema", headers=headers)
    resp.raise_for_status()

    return resp.json()['items']


def create_integration_access_config(platform_id: str,
                                     create_request: CreateIntegrationAccessConfigRequest,
                                     token: str,
                                     target_org: Optional[str]=None) -> AccessConfig:
    headers = {"Authorization": token}
    if target_org:
        headers['X-Sevco-Target-Org'] = target_org

    resp = requests.post(f"https://api.sev.co/v3/integration-platform/{platform_id}/access/config", headers=headers, json=asdict(create_request))
    resp.raise_for_status()

    params = resp.json()

    return AccessConfig(org_id=params['org_id'],
                        platform_id=params['platform_id'],
                        id=params['id'],
                        config_set=params['config_set'],
                        enabled=params['enabled'],
                        created_timestamp=params['created_timestamp'],
                        last_updated_timestamp=params['last_updated_timestamp'],
                        runner_id=params.get("runner_id"),
                        label=params.get('label'),
                        contact_info=params.get('contact_info'),
                        external_console_link=params.get('external_console_link'))


def create_integration_config(platform_id: str,
                              integration_id: str,
                              create_request: CreateIntegrationConfigRequest,
                              token: str,
                              target_org: Optional[str]) -> IntegrationConfig:
    headers = {"Authorization": token}
    if target_org:
        headers['X-Sevco-Target-Org'] = target_org

    resp = requests.post(f"https://api.sev.co/v3/integration-platform/{platform_id}/integration/{integration_id}/config", headers=headers, json=asdict(create_request))
    resp.raise_for_status()

    params = resp.json()

    return IntegrationConfig(org_id=params['org_id'],
                             platform_id=params['platform_id'],
                             integration_id=params['integration_id'],
                             id=params['id'],
                             access_config_id=params['access_config_id'],
                             config_set=params['config_set'],
                             enabled=params['enabled'],
                             created_timestamp=params['created_timestamp'],
                             last_updated_timestamp=params['last_updated_timestamp'],
                             label=params.get('label'))

def get_latest_execution(integration_config_id: str, token: str, target_org: Optional[str]) -> Dict[str, Any]:
    headers = {"Authorization": token}
    if target_org:
        headers['X-Sevco-Target-Org'] = target_org

    resp = requests.get("https://api.sev.co/v1/integration/execution",
                        params={'context_id': integration_config_id, 'count': 1, 'sort_ascending': 'false'},
                        headers=headers)
    resp.raise_for_status()

    return resp.json()['items'][0]
    

def main(token: str, target_org: Optional[str]):
    access_schemas = list_integration_access_schemas('sentinelone', token=token, target_org=target_org)
    print("Access Schemas:")
    pprint(access_schemas)
    # Example JsonSchemas for SentinelOne access configs:
    # [{'$defs': {'auth': {'$id': '/schemas/auth',
    #                  'additionalProperties': False,
    #                  'properties': {'api_key': {'description': 'API Key',
    #                                             'minLength': 1,
    #                                             'type': 'string',
    #                                             'writeOnly': True}},
    #                  'required': ['api_key'],
    #                  'title': 'api_key'},
    #         'connect': {'$id': '/schemas/connect',
    #                     'additionalProperties': False,
    #                     'properties': {'insecure': {'default': False,
    #                                                 'description': 'Allow '
    #                                                                'insecure '
    #                                                                'connections',
    #                                                 'type': 'boolean'},
    #                                    'url': {'description': 'URL',
    #                                            'minLength': 1,
    #                                            'type': 'string'}},
    #                     'required': ['url'],
    #                     'title': 'url'}},
    #  'additionalProperties': False,
    #  'id': 'api-key-url',
    #  'properties': {'auth': {'$ref': '/schemas/auth'},
    #                 'connect': {'$ref': '/schemas/connect'}},
    #  'required': ['auth', 'connect']}]

    access_config = create_integration_access_config('sentinelone',
                                                     CreateIntegrationAccessConfigRequest(config_set=ConfigSet(schema_id='api-key-url',
                                                                                                               auth={"api_key": "foo"},
                                                                                                               connect={"url": "https://usea1-001-mssp.sentinelone.net/"}),
                                                                                          enabled=True,
                                                                                          label="My SentinelOne Connection"),
                                                     token=token, target_org=target_org)
    print("Access Config:")
    pprint(access_config)

    integration_schemas = list_integration_schemas('sentinelone', 'sentinelone', token=token, target_org=target_org)
    print("Integration Schemas:")
    pprint(integration_schemas)
    # Example JsonSchemas for SentinelOne integration configs:
    # [{'$defs': {'settings': {'$id': '/schemas/settings',
    #                          'additionalProperties': False,
    #                          'properties': {'site_ids': {'description': 'Comma '
    #                                                                     'separated '
    #                                                                     'list of '
    #                                                                     'site IDs '
    #                                                                     'to '
    #                                                                     'include '
    #                                                                     '(default: '
    #                                                                     'empty '
    #                                                                     'list '
    #                                                                     'indicates '
    #                                                                     'ALL '
    #                                                                     'SITES)',
    #                                                      'examples': ['1123641005321168135',
    #                                                                   '225494730938493804,225494730938493915'],
    #                                                      'minLength': 1,
    #                                                      'pattern': '^[0-9]+(,[0-9]+)*$',
    #                                                      'type': 'string'}},
    #                          'required': [],
    #                          'title': 'sentinelone'}},
    #  'additionalProperties': False,
    #  'id': 'sentinelone',
    #  'properties': {'settings': {'$ref': '/schemas/settings'}},
    #  'required': ['settings']},
    # {'$defs': {'settings': {'$id': '/schemas/settings',
    #                         'additionalProperties': False,
    #                         'properties': {'account_ids': {'description': 'Comma '
    #                                                                       'separated '
    #                                                                       'list '
    #                                                                       'of '
    #                                                                       'account  '
    #                                                                       'IDs to '
    #                                                                       'include '
    #                                                                       '(default: '
    #                                                                       'empty '
    #                                                                       'list '
    #                                                                       'indicates '
    #                                                                       'ALL '
    #                                                                       'ACCOUNTS)',
    #                                                        'examples': ['1111111112222223333',
    #                                                                     '4444111112266666888'],
    #                                                        'minLength': 1,
    #                                                        'pattern': '^[0-9]+(,[0-9]+)*$',
    #                                                        'type': 'string'}},
    #                         'required': [],
    #                         'title': 'sentinelone_with_account_ids'}},
    #  'additionalProperties': False,
    #  'id': 'sentinelone-with-account-ids',
    #  'properties': {'settings': {'$ref': '/schemas/settings'}},
    #  'required': ['settings']}]

    integration_config = create_integration_config('sentinelone',
                                                   'sentinelone',
                                                   CreateIntegrationConfigRequest(access_config_id=access_config.id,
                                                                                  config_set=ConfigSet(schema_id='sentinelone-with-account-ids',
                                                                                                       settings={"account_ids": "1111111112222223333,4444111112266666888"}),
                                                                                  enabled=True,
                                                                                  label="SentinelOne Source"),
                                                   token=token,
                                                   target_org=target_org)

    print("Integration Config:")
    pprint(integration_config)

    execution = get_latest_execution(integration_config.id, token=token, target_org=target_org)
    print("Execution:")
    pprint(execution)


if __name__ == "__main__":
    token = sys.argv[1]  # Api Token provided by https://my.sev.co/<org_name>/profile/tokens.  eg "Token AAAAAAA-BBBBBBB-CCCCCCC-DDDDDDD"

    target_org = None
    if len(sys.argv) > 2:
        target_org = sys.argv[2]  # Logins associated with multiple orgs must provide the target org for api calls

    main(token, target_org)
