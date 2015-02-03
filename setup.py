import os
from setuptools import setup


def get_packages():
    # setuptools can't do the job :(
    packages = []
    for root, dirnames, filenames in os.walk('pysm'):
        if '__init__.py' in filenames:
            packages.append(".".join(os.path.split(root)).strip("."))

    return packages

required_modules = []

setup(name='pysm',
      version='0.0.9',
      description='Python State Machines for Humans',
      url='http://github.com/Catstyle/pysm',
      author='Catstyle Lee',
      author_email='catstyle.lee@gmail.com',
      install_requires=required_modules,
      license='MIT',
      packages=get_packages(),
      zip_safe=False,
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          ]
      )
