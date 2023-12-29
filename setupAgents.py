#!/usr/bin/env python

from distutils.core import setup
import sys
import subprocess

setup(name='Constrained Cooperative Agents',
      version='0.1.0',
      description='AI Agents program to play The Crew',
      author='Agents4',
      url='https://github.cs.adelaide.edu.au/a1709619/agents4',
      py_modules=['agents', 'engine'],
     )

subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 
'./requirements.txt'])