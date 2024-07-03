#!/bin/bash

# This is a sample script for client-side setup
# It requests a WireGuard token, configures the VPN and sets up TinyProxy

# Replace these variables with appropriate values
API_URL="http://your_api_server:8000"
CLIENT_ID="your_client_id"
GEO_LOCATION="your_geo_location"
INTERNET_SPEED="your_internet_speed"

# Request a WireGuard token
response=$(curl -X POST "$API_URL/register" -H "Content-Type: application/json" \
  -d "{\"client_id\":\"$CLIENT_ID\",\"geo_location\":\"$GEO_LOCATION\",\"internet_speed\":\"$INTERNET_SPEED\"}")

wireguard_config=$(echo $response | jq -r '.wireguard_config')
proxy_port=$(echo $response | jq -r '.proxy_port')

# Save WireGuard configuration
echo "$wireguard_config" > /etc/wireguard/wg0.conf

# Start WireGuard
wg-quick up wg0

# Install TinyProxy
apt-get install -y tinyproxy
