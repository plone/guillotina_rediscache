# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


setup(
    name='guillotina_rediscache',
    version='1.0.12',
    description='guillotina cache implementation using redis + lru in-memory cache',
    long_description=(open('README.rst').read() + '\n' +
                      open('CHANGELOG.rst').read()),
    keywords=['asyncio', 'REST', 'guillotina', 'cache', 'redis'],
    author='Nathan Van Gheem',
    author_email='vangheem@gmail.com',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    url='https://github.com/guillotinaweb/guillotina_rediscache',
    license='BSD',
    setup_requires=[
        'pytest-runner',
    ],
    zip_safe=True,
    include_package_data=True,
    # ext_modules=ext_modules,
    packages=find_packages(),
    install_requires=[
        'guillotina>=2.0.0',
        'aioredis>=1.0.0b2',
        'lru-dict',
        'ujson'
    ],
    extras_require={
        'test': [
            'pytest',
            'docker',
            'backoff',
            'psycopg2',
            'pytest-asyncio<=0.5.0',
            'pytest-aiohttp',
            'pytest-cov'
        ]
    }
)
