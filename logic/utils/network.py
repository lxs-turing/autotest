import netifaces

LOOPBACK_INTERFACE = 'lo0'
LOOPBACK_IP_ADDRESS = '127.0.0.1'
EMPTY_MAC_ADDRESS = '00:00:00:00:00:00'


def get_interfaces():
    interfaces = netifaces.interfaces()
    return interfaces


def get_default_interface():
    gw = netifaces.gateways()['default']
    return gw[netifaces.AF_INET][1] if netifaces.AF_INET in gw else LOOPBACK_INTERFACE


def get_default_ip_address():
    gw = netifaces.gateways()['default']
    return gw[netifaces.AF_INET][0] if netifaces.AF_INET in gw else LOOPBACK_IP_ADDRESS


def get_ip_address(interface=None):
    if not interface:
        return get_default_ip_address()
    try:
        addrs = netifaces.ifaddresses(interface)
    except ValueError:
        return None
    return addrs[netifaces.AF_INET][0]['addr'] if netifaces.AF_INET in addrs else LOOPBACK_IP_ADDRESS


def get_mac_address(interface=None):
    if not interface:
        interface = get_default_interface()
    try:
        addrs = netifaces.ifaddresses(interface)
    except ValueError:
        return None
    return addrs[netifaces.AF_LINK][0]['addr'] if netifaces.AF_LINK in addrs else EMPTY_MAC_ADDRESS
