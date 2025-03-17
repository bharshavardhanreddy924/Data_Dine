#!/bin/bash

# Exit on error
set -e

echo "Updating system packages..."
apt-get update && apt-get install -y build-essential libffi-dev libssl-dev libev-dev python3-dev

echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "Installing Cython to avoid gevent errors..."
pip install --no-cache-dir Cython

echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "Starting Flask app..."
gunicorn -w 4 -b 0.0.0.0:8080 wsgi:app
