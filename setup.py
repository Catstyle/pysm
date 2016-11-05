import os
import re
import shutil
from setuptools import setup

from distutils.command.clean import clean as _clean


__version__ = re.search(
    "__version__\s*=\s*'(.*)'", open('pysm/__init__.py').read(), re.M
).group(1)
assert __version__


def get_packages():
    # setuptools can't do the job :(
    packages = []
    for root, dirnames, filenames in os.walk('pysm'):
        if '__init__.py' in filenames:
            packages.append(".".join(os.path.split(root)).strip("."))
    return packages


class clean(_clean):

    def run(self):
        # Delete generated files in the code tree.
        for (dirpath, dirnames, filenames) in os.walk("."):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if (filepath.endswith(".pyc") or
                        filepath.endswith(".so") or
                        filepath.endswith(".o")):
                    os.remove(filepath)
            for dirname in dirnames:
                if dirname in ('build', 'dist', 'pysm.egg-info'):
                    shutil.rmtree(os.path.join(dirpath, dirname))
        # _clean is an old-style class, so super() doesn't work.
        _clean.run(self)


setup(
    name='pysm',
    version=__version__,
    description='Python State Machines for Humans',
    url='http://github.com/Catstyle/pysm',
    author='Catstyle Lee',
    author_email='catstyle.lee@gmail.com',
    license='MIT',
    packages=get_packages(),
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    cmdclass={'clean': clean}
)
