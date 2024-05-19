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

## Commands

| Name    | Version | Command | Arguments         | Response | Details                                 |
| ------- | ------- | ------- | ----------------- | -------- | --------------------------------------- |
| Beep    | 1/2     | A1 11   | YY MM DD T1 T2 T3 | -        | T1-3 seems to be a timer from app start |
| Status  |         |         |                   |          |                                         |
| History |         |         |                   |          |                                         |

## Publishing

```sh
# install dependencices
pip3 install twine
# install locally
pip3 install -e .
# test using cli
radoneye --help
# build
python3 -m build
# view what is included into wheel
unzip -l dist/*.whl
# check wheel
twine check dist/*.whl
# upload to pypi
twine upload --repository pypi dist/*
```
