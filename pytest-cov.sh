#!/usr/bin/env bash

source ./venv/bin/activate
py.test --cov-config .coveragerc --cov-report html --cov=rest_client_gen test/
