import requests

def main(ip, username, password):
    """
    @Block
    :desc: Authorize proxy mesh to work with given IP address

    :param ip: IP address to authenticate
    :type ip: string
    :example ip: "38.140.96.18"

    :param username: ProxyMesh username
    :type username: string
    :example username: "solutionloft"

    :param password: ProxyMesh password
    :type password: string
    :example password: "password"

    :returns: Whether or not the authentication was successful
    :rtype: bool
    """
    r = requests.post("https://proxymesh.com/api/ip/add/",
                      auth=requests.auth.HTTPBasicAuth(username, password),
                      data={"ip": ip})
    if 200 == r.status_code:
        return True
    else:
        return False
