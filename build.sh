#!/bin/bash

# Exit immediately if any command fails
set -e

echo "Updating system packages..."
apt-get update && apt-get install -y build-essential libffi-dev libssl-dev libev-dev python3-dev

echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "Installing Cython first to avoid gevent errors..."
pip install --no-cache-dir Cython

echo "Installing dependencies from requirements.txt..."
pip install --no-cache-dir -r requirements.txt

echo "Build completed successfully!"
