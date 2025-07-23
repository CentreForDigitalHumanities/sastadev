# Sastadev

[![Actions Status](https://github.com/UUDigitalHumanitieslab/sastadev/workflows/Unit%20tests/badge.svg)](https://github.com/UUDigitalHumanitieslab/sastadev/actions)

[![PyPi/sastadev](https://img.shields.io/pypi/v/sastadev)](https://pypi.org/project/sastadev/)

Method definitions for use in SASTA

## Installation
You can install SASTADEV using pip:
```
pip install sastadev
```

## Usage

### Command line interface
The installation provides an entrypoint `sastadev` which invokes `sastadev.__main__.main()`

To lists arguments and options:

```
sastadev -h
```
or
```
python -m sastadev -h
```

### Using as a library
```python
from sastadev.deregularise import correctinflection
result = correctinflection('slaapten')
print(result)
# [('sliepen', 'Overgeneralisation')]
```

## Configuration
The package contains a configuration module `sastadev.conf` that produces a `SastadevConfig` object at runtime, called `settings`.

### Using settings values
Example 1 (**correct**): 
```python
from sastadev.conf import settings
def get_dataroot():
    print(settings.DATAROOT)
```

Example 2 (**wrong!**):
```python
from sastadev.conf import settings

dataroot = settings.DATAROOT

def get_dataroot():
    print(dataroot)
```

The key difference is that the code in example 2 evaluates `settings.DATAROOT` at the moment the code is executed. If `settings.DATAROOT` changes between the first time the module is loaded and the time it is ran, the first value will be used. This disables configurable settings.


### Changing settings
`sastadev.conf.settings` can be changed at runtime. 
> :warning: **Changing `settings` properties changes _all_ code that is executed after the change**. Therefore, make sure you set the settings **once**, and at the beginning of the runtime cycle.  

## Development
To install the requirements:
```
pip install -r requirements.txt
```

### Installing locally
To install the package in editable state:
```
pip install -e .
```

### Testing
Tests should be written and run using [pytest](https://docs.pytest.org/).
To test, make sure the package is installed in editable mode.
Then, each time you wish to run the tests:
```
pytest
```

### Linting
Linting configuration is provided for [flake8](https://flake8.pycqa.org/en/latest/).
To lint, run:
```
flake8 ./src/sastadev/
```

### Upload to PyPi

Specify the files which should be included in the package in `pypi/include.txt`.

```bash
pip install twine
python setup.py sdist
twine upload dist/*.tar.gz
```

## Contributing
Enhancements, bugfixes, and new features are welcome. For major changes, please follow these steps:

- open an issue to discuss what you would like to change
- create a branch `feature/<your-branchname`>, based on `develop` that contains your changes 
- ensure the code is well tested
- create a pull request for merging the changes into `develop`
- the maintainers will take care of reviewing the code, offering suggested changes, and merging the code
- at the discretion of the maintainers, the `develop` branch will be merged into `master`, and a new release will be made
