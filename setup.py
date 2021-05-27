#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Setup script for speach

Latest version can be found at https://github.com/neocl/speach

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import io
from setuptools import setup


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


readme_file = 'README.md'
long_description = read(readme_file)
pkg_info = {}
exec(read('speach/__version__.py'), pkg_info)

with open('requirements.txt', 'r') as infile:
    requirements = infile.read().splitlines()

setup(
    name='speach',
    version=pkg_info['__version__'],
    tests_require=requirements + ['coverage'],
    install_requires=requirements,
    python_requires=">=3.6",
    license=pkg_info['__license__'],
    author=pkg_info['__author__'],
    author_email=pkg_info['__email__'],
    description=pkg_info['__description__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['speach',
              'speach.data'],
    package_data={'speach': ['data/*.sql', 'data/*.gz']},
    include_package_data=True,
    url=pkg_info['__url__'],
    project_urls={
        "Bug Tracker": "https://github.com/neocl/speach/issues",
        "Source Code": "https://github.com/neocl/speach/"
    },
    keywords=["nlp", "annotation", "text", "corpus", "linguistics", "ELAN", "transcription"],
    platforms='any',
    test_suite='test',
    # Reference: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=['Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9',
                 'Development Status :: {}'.format(pkg_info['__status__']),
                 'License :: OSI Approved :: {}'.format(pkg_info['__license__']),
                 'Environment :: Plugins',
                 'Intended Audience :: Education',
                 'Intended Audience :: Science/Research',
                 'Intended Audience :: Information Technology',
                 'Intended Audience :: Developers',
                 'Operating System :: OS Independent',
                 'Topic :: Text Processing',
                 'Topic :: Text Processing :: Linguistic',
                 'Topic :: Software Development :: Libraries :: Python Modules']
)
