#!/usr/bin/env bash

py.test --cov-config .coveragerc --cov-report html --cov=rest_client_gen test/
