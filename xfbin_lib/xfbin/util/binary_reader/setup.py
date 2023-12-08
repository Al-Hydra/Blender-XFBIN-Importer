from setuptools import setup

with open('README.md', encoding='utf-8') as f:
  long_description = f.read()

setup(
  name = 'binary_reader',
  packages = ['binary_reader'],
  version = '1.4.3',
  license='MIT',
  description = 'A python module for basic binary file IO.',
  long_description=long_description,
  long_description_content_type='text/markdown',
  author = 'SutandoTsukai181',
  author_email = 'mosamaeldeeb@gmail.com',
  url = 'https://github.com/SutandoTsukai181/PyBinaryReader',
  download_url = 'https://github.com/SutandoTsukai181/PyBinaryReader/archive/refs/tags/v1.4.3.tar.gz',
  keywords = ['BINARY', 'IO', 'STRUCT'],
  install_requires=[],
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.8',
  ],
)
