#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0', 'beautifulsoup4', 'requests', 'habanero', 'events', 'selenium', 'toml'
    # TODO: put package requirements here
]

setup_requirements = [
    # TODO(ericgcc): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='crosscholar',
    version='0.1.0',
    description="crosscholar is a python program to scrap Google Scholar data",
    long_description=readme + '\n\n' + history,
    author="Eric Garcia Cano @ericgcc",
    author_email='ericgcc@gmail.com',
    url='https://bitbucket.org/iingen-biblio/crosscholar-scarper',
    packages=find_packages(include=['crosscholar']),
    entry_points={
        'console_scripts': [
            'crosscholar=crosscholar.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='crosscholar',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    python_requires=">=3.6"
)
