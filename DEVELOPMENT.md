# RadonEye Development

## Workspace

Install dependencies and create venv:

```sh
brew install python
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt -r requirements.dev.txt
.venv/bin/pip3 install -e .
```

Enable Visual Studio Code support:

```sh
echo "PYTHONPATH=.venv/lib" > .env
```

Run CLI:

```sh
.venv/bin/radoneye
```

Run tests:

```sh
.venv/bin/pytest
```

Update test snapshots:

```sh
# create new snapshots
.venv/bin/pytest --inline-snapshot=create
# fix existing snapshots
.venv/bin/pytest --inline-snapshot=fix
```

Check coverage:

```sh
open coverage/index.html
```

Run integration tests:

```sh
brew install tox python@3.9 python@3.10 python@3.11 python@3.12 python@3.13
tox
```

## Debugging

Enable Bleak logs:

```sh
BLEAK_LOGGING=1 radoneye ...
```

Enable debug mode (dump messages):

```sh
radoneye -d ...
```

Turn off rounding:

```sh
RADONEYE_ROUNDING_OFF=true radoneye ...
```

## Publishing

```sh
# install locally
.venv/bin/pip3 install -e .
# test using cli
.venv/bin/radoneye --help
# clean
rm -rf dist
# test
tox
# build
.venv/bin/python3 -m build
# view what is included into wheel
unzip -l dist/*.whl
# check wheel
.venv/bin/twine check dist/*.whl
# upload to pypi
.venv/bin/twine upload --repository pypi dist/*
```
