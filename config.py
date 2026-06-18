# MTProto proxy configuration
# Reference: https://github.com/alexbers/mtprotoproxy

# Port Koyeb will route traffic to. Must match the Dockerfile EXPOSE
# and the port you set in your Koyeb service settings.
PORT = 8080

# Users and their secrets. Each secret must be a 32-char hex string.
# Generate your own with: python3 -c "import secrets; print(secrets.token_hex(16))"
# Replace these placeholder secrets before deploying.
USERS = {
    "tg": "A7k9X2mP8qR4tY1nB6vC3dE5fG0hJ2Lz",
}

# Which connection modes to allow.
# "tls" (a.k.a. "ee" mode) disguises the proxy as an HTTPS server talking to
# TLS_DOMAIN below, which is the mode least likely to be blocked/detected
# and is the recommended default for private use.
MODES = {
    "classic": False,
    "secure": False,
    "tls": True,
}

# Domain the proxy pretends to be when in tls mode. Use a real, popular,
# already-HTTPS domain (the default is fine for most cases).
TLS_DOMAIN = "www.telegram.org"

# Leave blank unless you've registered a sponsor channel tag via @MTProxybot.
# A non-empty AD_TAG switches the proxy into "middle proxy" mode.
AD_TAG = ""

# Bind to all interfaces so Koyeb's network can reach the container.
LISTEN_ADDR_IPV4 = "0.0.0.0"
LISTEN_ADDR_IPV6 = "::"
