# RadonEye Development

## Workspace

Install dependencies:

```sh
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt
```

Enable Visual Studio Code:

```sh
echo "PYTHONPATH=.venv/lib" > .env
```

Run CLI:

```sh
PYTHONPATH=src .venv/bin/python3 -m radoneye
```

Run tests:

```sh
.venv/bin/pytest
```

Update test snapshots:

```sh
.venv/bin/pytest --inline-snapshot=create
```

## Commands

### Beep

Beep is the same on all version of device. Technically command is invoked by app as
`A1 11 YY MM DD T1 T2 T3`, where YY - is 2 digit year, MM - month, DD - day of the month, T1+T2+T3 -
3 byte sequence that looks like time from application start (not random, not timestamp). However,
based on tests, sending just `A1` is enough to trigger beep.

## Publishing

```sh

# install dependencices
.venv/bin/pip3 install twine build
# install locally
.venv/bin/pip3 install -e .
# test using cli
.venv/bin/radoneye --help
# build
.venv/bin/python3 -m build
# view what is included into wheel
unzip -l dist/*.whl
# check wheel
.venv/bin/twine check dist/*.whl
# upload to pypi
.venv/bin/twine upload --repository pypi dist/*
```