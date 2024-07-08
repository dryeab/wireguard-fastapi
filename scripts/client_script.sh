#!/bin/bash

# Replace these variables with appropriate values
API_URL="http://localhost:8000"
CLIENT_ID="client_id"
GEO_LOCATION="geo_location"
INTERNET_SPEED="internet_speed"
WG_CONF_PATH="/etc/wireguard/wg0.conf"

# Register the client and get the WireGuard configuration
response=$(curl -s -X POST "$API_URL/register" -H "Content-Type: application/json" -d '{
  "client_id": "'$CLIENT_ID'",
  "geo_location": "'$GEO_LOCATION'",
  "internet_speed": "'$INTERNET_SPEED'"
}')

# Extract the WireGuard configuration and proxy port from the response
wireguard_config=$(echo $response | jq -r '.wireguard_config')
proxy_port=$(echo $response | jq -r '.proxy_port')

# Ensure the directory for WireGuard configuration exists
mkdir -p $(dirname $WG_CONF_PATH)

# Write the WireGuard configuration to the file
echo "$wireguard_config" > $WG_CONF_PATH

# Set up WireGuard
wg-quick up wg0

# Install TinyProxy if not already installed
if ! command -v tinyproxy &> /dev/null
then
    echo "TinyProxy could not be found, installing..."
    apt-get update && apt-get install -y tinyproxy
fi

# Configure TinyProxy
sed -i "s/^Port .*/Port $proxy_port/" /etc/tinyproxy/tinyproxy.conf
systemctl restart tinyproxy

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1

# Set up IP tables for TinyProxy (adjust as necessary)
iptables -t nat -A PREROUTING -i wg0 -p tcp --dport 8888 -j REDIRECT --to-port $proxy_port

echo "WireGuard and TinyProxy setup completed."
