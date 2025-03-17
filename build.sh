#!/bin/bash

# Exit on failure
set -e

echo "Updating system packages..."
apt-get update && apt-get install -y build-essential libffi-dev libssl-dev libev-dev python3-dev

echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "Starting Flask with Gunicorn..."
gunicorn -w 4 -b 0.0.0.0:8080 wsgi:app
