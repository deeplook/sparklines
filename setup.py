import setuptools
import distutils.core

from sparklines.sparklines import __version__


class PyTest(distutils.core.Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        errno = subprocess.call([sys.executable, 'test/runtests.py'])
        raise SystemExit(errno)


setuptools.setup(
    name='sparklines',
    version=__version__,
    author='Dinu Gherman',
    author_email='gherman@darwin.in-berlin.de',
    description='Generate sparklines for numbers using Unicode characters only.',
    license='GPL',
    keywords='visualization, tool',
    url='https://github.com/deeplook/sparklines',
    packages=setuptools.find_packages(exclude='test'),
    long_description=open('README.rst').read(),
    install_requires=[
        # 'termcolor',
    ],
    entry_points={
        'console_scripts': ['sparklines=sparklines.__main__:main']
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU General Public License (GPL)'
    ],
    cmdclass={'test': PyTest},
    package_data={
        # 'sparklines': ['foo.csv'],
    },
)
