from urllib.parse import urlparse
result = urlparse("postgres://postgres:Pn4Cs3t3Avm8vxr@floral-wind-8493.flycast:5432")
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

data = dict(
    database = database,
    user = username,
    password = password,
    host = hostname,
    port = port
)

print(data)