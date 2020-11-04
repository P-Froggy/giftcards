# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in giftcards/__init__.py
from giftcards import __version__ as version

setup(
	name='giftcards',
	version=version,
	description='Management and selling of gift cards',
	author='Michael Weißer',
	author_email='michael.weisser@rindenmuehle.de',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
