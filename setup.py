import io
import setuptools
import distutils.core


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
    version='0.4.2',
    author='Dinu Gherman',
    author_email='gherman@darwin.in-berlin.de',
    description='Generate sparklines for numbers using Unicode characters only.',
    license='GPL',
    keywords='visualization, chart, tool',
    url='https://github.com/deeplook/sparklines',
    packages=setuptools.find_packages(exclude='test'),
    long_description=io.open('README.rst', encoding='utf-8').read(),
    install_requires=[
        # 'termcolor',
        'future',
    ],
    entry_points={
        'console_scripts': ['sparklines=sparklines.__main__:main']
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: GNU General Public License (GPL)'
    ],
    cmdclass={'test': PyTest},
    package_data={
        # 'sparklines': ['foo.csv'],
    },
)
