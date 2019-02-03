#!/usr/bin/env python
# -*- coding: utf-8 -*-
import posixpath
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from aiu import __meta__

with open('README.rst') as readme_file:
    README = readme_file.read()

with open('CHANGES.rst') as changes_file:
    HISTORY = changes_file.read().replace('.. :changelog:', '')


def _find_data_files(dir_name):
    files = os.listdir(dir_name)
    return [(dir_name, [posixpath.join(dir_name, f) for f in files])]


def _parse_requirements(file_path, requirements, links):
    with open(file_path, 'r') as requirements_file:
        for line in requirements_file:
            if 'git+https' in line:
                pkg = line.split('#')[-1]
                links.add(line.strip())
                requirements.add(pkg.replace('egg=', '').rstrip())
            elif line.startswith('http'):
                links.add(line.strip())
            else:
                requirements.add(line.strip())


def _filter_requirements(requirements, test_requirements):
    raw_requirements = set()
    for req in requirements:
        raw_req = req.split('>')[0].split('=')[0].split('<')[0].split('!')[0]
        raw_requirements.add(raw_req)
    filtered_test_requirements = set()
    for req in test_requirements:
        raw_req = req.split('>')[0].split('=')[0].split('<')[0].split('!')[0]
        if raw_req not in raw_requirements:
            filtered_test_requirements.add(req)
    return list(filtered_test_requirements)


# See https://github.com/pypa/pip/issues/3610
# use set to have unique packages by name
LINKS = set()
REQUIREMENTS = set()
TEST_REQUIREMENTS = set()
_parse_requirements('requirements.txt', REQUIREMENTS, LINKS)
_parse_requirements('requirements-dev.txt', TEST_REQUIREMENTS, LINKS)
LINKS = list(LINKS)
REQUIREMENTS = list(REQUIREMENTS)
TEST_REQUIREMENTS = _filter_requirements(REQUIREMENTS, TEST_REQUIREMENTS)

setup(
    # -- meta information --------------------------------------------------
    name=__meta__.__package__,
    version=__meta__.__version__,
    description=__meta__.__description__,
    long_description=README + '\n\n' + HISTORY,
    author=__meta__.__author__,
    maintainer=__meta__.__maintainer__,
    maintainer_email=__meta__.__email__,
    contact=__meta__.__maintainer__,
    contact_email=__meta__.__email__,
    url=__meta__.__url__,
    platforms=['linux_x86_64'],
    license="ISCL",
    keywords='audio,music,editor,tag,id3,mp3',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # -- Package structure -------------------------------------------------
    packages=[__meta__.__package__],
    package_dir={__meta__.__package__: 'aiu'},
    data_files=_find_data_files('config'),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    dependency_links=LINKS,
    zip_safe=False,

    # -- self - tests --------------------------------------------------------
    test_suite='tests',
    tests_require=TEST_REQUIREMENTS,

    # -- script entry points -----------------------------------------------
    # scripts=['bin/{}'.format(__meta__.__package__)],
    entry_points={'console_scripts': ['aiu=aiu.main:cli']}
)
