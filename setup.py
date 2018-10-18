#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=6.0', 'python_jwt', 'requests', 'url-normalize']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Paolo Cozzi",
    author_email='cozzi@ibba.cnr.it',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries',
    ],
    description=("Python USI submission REST API contain all methods to "
                 "interact with EMBL-EBI Unified Submissions interface"),
    entry_points={
        'console_scripts': [
            'pyUSIrest=pyUSIrest.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pyUSIrest',
    name='pyUSIrest',
    packages=find_packages(include=['pyUSIrest']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/cnr-ibba/pyUSIrest',
    version="0.2.0-dev",
    zip_safe=False,
)
