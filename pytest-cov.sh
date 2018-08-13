#!/usr/bin/env bash

py.test --cov-config .coveragerc --cov-report html --cov=attrs_api test/
