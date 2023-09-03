#!/usr/bin/env bash

if [ -d build ]; then
  rm -rf build
fi

# Recreate build directory
mkdir -p build/function/ build/layer/

# copy lambda function file
echo "copy lambda function file"
cp -r lambda_function/ build/function/

# create lambda layer zip
echo "create lambda layer zip"
pip install -r requirements.txt -t build/layer/python