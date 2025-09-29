#!/bin/bash

# Build script for doc-proc-ui backend-app
# This script should be run from the project root directory

echo "Building doc-proc-ui backend app Docker image..."
echo "Building from project root to include doc-proc-lib dependency"

# Check if we're in the right directory
if [ ! -d "doc-proc-lib" ] || [ ! -d "doc-proc-ui/backend-app" ]; then
    echo "Error: This script must be run from the project root directory"
    echo "Make sure you're in the directory that contains both 'doc-proc-lib' and 'doc-proc-ui' folders"
    exit 1
fi

# Build the Docker image
docker build -f doc-proc-ui/backend-app/Dockerfile -t doc-proc-ui-backend-app .

echo "Build complete! You can now run the container with:"
echo "docker run -p 8090:8090 doc-proc-ui-backend-app"