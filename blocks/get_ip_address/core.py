import requests

def main(proxies={}):
    """
    @Block
    :desc: Get current IP address of server or proxy server

    :param proxies: A dict corresponding to proxy argument for requests
    :type proxies: dict
    :example proxies: {}

    :returns: The IP address
    :rtype: string
    :example: "192.0.0.1"
    """
    if proxies:
        resp = requests.get("https://api.ipify.org?format=json", proxies=proxies)
        return resp.json()["ip"]
    else:
        resp = requests.get("https://api.ipify.org?format=json")
        return resp.json()["ip"]
