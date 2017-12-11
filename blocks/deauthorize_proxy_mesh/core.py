import requests

def main(ip, username, password):
    """
    @Block
    :desc: Revoke authorization to proxy mesh for a given IP address

    :param ip: IP address to de-authenticate
    :type ip: string
    :example ip: "38.140.96.18"

    :param username: ProxyMesh username
    :type username: string
    :example username: "solutionloft"

    :param password: ProxyMesh password
    :type password: string
    :example password: "password"

    :returns: Whether or not the de-authentication was successful
    :rtype: bool
    """
    r = requests.post("https://proxymesh.com/api/ip/delete/",
                      auth=requests.auth.HTTPBasicAuth(username, password),
                      data={"ip": ip})

    if 204 == r.status_code:
        return True
    else:
        False
