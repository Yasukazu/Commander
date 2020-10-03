from setuptools import setup
from os import path

import ycommander

here = path.abspath(path.dirname(__file__))

# Get the long description from the README.md file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

install_requires = [
    'colorama',
    'pycryptodomex>=3.7.2',
    'libkeepass',
    'requests',
    'tabulate',
    'prompt_toolkit>=2.0.4',
    'asciitree',
    'protobuf>=3.6.0',
    'pyperclip',
    'pypager',
    'pyicu'
]

setup(name='ycommander',
      version=ycommander.__version__,
      description='Keeper Commander for Python 3',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Craig Lurey / (modified by)MAKINO Yasukazu ',
      author_email='craig@keepersecurity.com',
      url='https://github.com/Yasukazu/YCommander',
      license='MIT',
      classifiers=["Development Status :: 4 - Beta",
                   "License :: OSI Approved :: MIT License",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3.8",
                   "Topic :: Security"],
      keywords='security password',

      packages=['ycommander',
                'ycommander.commands',
                'ycommander.commands.record',
                'ycommander.importer',
                'ycommander.importer.json',
                'ycommander.importer.csv',
                'ycommander.importer.keepass',
                'ycommander.plugins',
                'ycommander.plugins.adpasswd',
                'ycommander.plugins.awskey',
                'ycommander.plugins.mssql',
                'ycommander.plugins.mysql',
                'ycommander.plugins.oracle',
                'ycommander.plugins.postgresql',
                'ycommander.plugins.ssh',
                'ycommander.plugins.sshkey',
                'ycommander.plugins.unixpasswd',
                'ycommander.plugins.windows',
                'ycommander.plugins.pspasswd',
                'ycommander.yubikey',
                ],
      include_package_data=True,
      python_requires='>=3.8',
      entry_points={
          "console_scripts": [
              "keeper=ycommander.__main__:main",
          ],
      },
      install_requires=install_requires
      )
