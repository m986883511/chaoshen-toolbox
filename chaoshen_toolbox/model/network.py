from typing import List, Optional, Dict

from pydantic import BaseModel, validator, root_validator
from pydantic.schema import IPv4Address

from chaoshen_toolbox.config import support


class _UserConfigNetworkModel(BaseModel):
    class muti_nic(BaseModel):
        wireless: Optional[str]
        wired: Optional[str]

        @validator('wired', 'wireless')
        def check_ip(cls, v):
            return v

    class muti_route(BaseModel):
        default: Optional[str]
        custom: Optional[str]

        @validator('default', 'custom')
        def check_route(cls, v):
            return v

    """
          wireless_ip: 192.168.2.214
      wired_ip: 192.168.2.215
      route: 192.168.2.1
      route-fq: 192.168.2.30
      dns: 8.8.8.8
    """
    nic: muti_nic
    wifi: List[str]
    route: muti_route
    dns: Optional[List[IPv4Address]]

    # @root_validator(pre=True)
    # def check_card_number_omitted(cls, values):
    #     assert 'card_number' not in values, 'card_number should not be included'
    #     return values


class UserConfigNetworkFileModel(BaseModel):
    # platform: List[support.config_ip_support_platform]
    platform: str
    network: Dict[str, _UserConfigNetworkModel]







class NetshConfigIpModel(BaseModel):
    nic: str
    ip: IPv4Address
    mask: IPv4Address
    route: IPv4Address
    dns: IPv4Address


