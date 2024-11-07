import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning # type: ignore
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

async def main(*args, **kwargs):
    schema = kwargs
    url =  args[0]

    response = requests.post(url=url, json=schema, verify=False)
    print("Disparado rotina para o Power Automate")
    return response.status_code