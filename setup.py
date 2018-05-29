#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=6.0', 'python_jwt']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Paolo Cozzi",
    author_email='cozzi@ibba.cnr.it',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="Python EBI AAP contain all methods to interact with EBI AAP service",
    entry_points={
        'console_scripts': [
            'pyEBIrest=pyEBIrest.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pyEBIrest',
    name='pyEBIrest',
    packages=find_packages(include=['pyEBIrest']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/bunop/pyEBIrest',
    version='0.1.0',
    zip_safe=False,
)
