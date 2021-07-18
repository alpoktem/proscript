#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='proscript',
      version='0.5',
      description='Proscript utilities',
      author='Alp Öktem',
      packages=find_packages(),
      include_package_data=True,
      install_requires=["praatio >= 4.3.0", "vosk >= 0.3.29"],
      package_data = {'proscript': ['utilities/praat/*']},
	  entry_points = {
        'console_scripts': ['proscripter=proscript.scripts:main'],
    	}
     )