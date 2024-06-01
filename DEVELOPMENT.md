# RadonEye Development

## Workspace

Install dependencies and create venv:

```sh
brew install python@3.9
python3.9 -m venv .venv
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
brew install tox python@3.9 python@3.10 python@3.11 python@3.12
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

Override e constant:

```sh
# default is 2.718281828459045
RADONEYE_E=2.71828 radoneye ...
```

## Details

### Beep

Beep is the same on all versions of device. Technically command is invoked by app as
`A1 11 YY MM DD T1 T2 T3`, where YY - is 2 digit year, MM - month, DD - day of the month, T1+T2+T3 -
3 byte sequence that looks like time from application start (not random, not timestamp). However,
based on tests, sending just `A1` is enough to trigger beep.

## Publishing

```sh
# install locally
.venv/bin/pip3 install -e .
# test using cli
.venv/bin/radoneye --help
# clean
rm -rf dist
# build
.venv/bin/python3 -m build
# view what is included into wheel
unzip -l dist/*.whl
# check wheel
.venv/bin/twine check dist/*.whl
# upload to pypi
.venv/bin/twine upload --repository pypi dist/*
```
