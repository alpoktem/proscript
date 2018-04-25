#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='proscript',
      version='0.3',
      description='Proscript utilities',
      author='Alp Öktem',
      author_email='alp.oktem@upf.edu',
      packages=find_packages(),
      include_package_data=True,
      package_data = {'proscript': ['utilities/laic/*']}
     )