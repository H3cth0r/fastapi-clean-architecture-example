#!/bin/bash
set -e

echo "Running database migrations..."
aerich upgrade

echo "Migrations complete!"
