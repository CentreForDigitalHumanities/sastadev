import pathlib

from setuptools import setup

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")


setup(
    name='sastadev',
    version='0.3.1',
    description='Linguistic functions for SASTA tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/UUDigitalHumanitieslab/sastadev',
    author='Research Software Lab - Centre for Digital Humanities - Utrecht University',
    author_email='digitalhumanities@uu.nl',
    package_dir={'': 'src'},
    packages=['sastadev'],
    python_requires='>=3.7, <4',
    package_data={'sastadev': ['py.typed', 'data/**/*']},
    license='BSD-3-Clause',
    entry_points={
        'console_scripts': [
            'sastadev=sastadev.__main__:main'
        ],
    },
    install_requires=[
        'auchann',
        'lxml',
        'openpyxl',
        'XlsxWriter',
        'typing-extensions',
        'pyspellchecker'
    ],
)
