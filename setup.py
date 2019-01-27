#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from aiu import __meta__

with open('README.rst') as readme_file:
    README = readme_file.read()

with open('CHANGES.rst') as changes_file:
    HISTORY = changes_file.read().replace('.. :changelog:', '')


def parse_requirements(requirements_path='requirements.txt'):
    links = set()   # See https://github.com/pypa/pip/issues/3610
    reqs = set()    # use set to have unique packages by name
    with open(requirements_path, 'r') as requirements_file:
        for line in requirements_file:
            if 'git+https' in line:
                pkg = line.split('#')[-1]
                links.add(line.strip())
                reqs.add(pkg.replace('egg=', '').rstrip())
            elif line.startswith('http'):
                links.add(line.strip())
            else:
                reqs.add(line.strip())
    return list(reqs), list(links)


REQUIREMENTS, LINKS = parse_requirements('requirements.txt')
TEST_REQUIREMENTS, _ = parse_requirements('requirements-dev.txt')

raw_requirements = set()
for req in REQUIREMENTS:
    raw_req = req.split('>')[0].split('=')[0].split('<')[0].split('!')[0]
    raw_requirements.add(raw_req)
filtered_test_requirements = set()
for req in TEST_REQUIREMENTS:
    raw_req = req.split('>')[0].split('=')[0].split('<')[0].split('!')[0]
    if raw_req not in raw_requirements:
        filtered_test_requirements.add(req)
TEST_REQUIREMENTS = list(filtered_test_requirements)

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
    include_package_data=True,
    install_requires=REQUIREMENTS,
    dependency_links=LINKS,
    zip_safe=False,

    # -- self - tests --------------------------------------------------------
    #test_suite='nose.collector',
    #test_suite='tests.test_runner',
    #test_loader='tests.test_runner:run_suite',
    tests_require=TEST_REQUIREMENTS,

    # -- script entry points -----------------------------------------------
    #scripts=['bin/{}'.format(__meta__.__package__)],
    entry_points={'console_scripts': ['aiu=aiu.main:cli']}
)
