def listener_pinger_get_local_servers(login, password, direct_access):
    params = {
        "server_ip": "string",
        "direct_access": direct_access,
        "guid": "{6F9619FF-8B86-D011-B42D-00CF4FC964FF}",
        "hash": "no hash",
        "version": "v1"
    }
    sysparams = {
        "login": login,
        "password": password,
        "session_id": "testing",
        "timeout": 50
    }
    return params, sysparams, 'listener_pinger:get_local_servers'


def listener_pinger_get_down_servers(login, password, direct_access):
    params = {
        "server_ip": "string",
        "direct_access": direct_access,
        "guid": "{6F9619FF-8B86-D011-B42D-00CF4FC964FF}",
        "hash": "no hash",
        "version": "v1"
    }
    sysparams = {
        "login": login,
        "password": password,
        "session_id": "testing",
        "timeout": 50
    }
    return params, sysparams, 'listener_pinger:get_down_servers'