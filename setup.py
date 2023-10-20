import io
import setuptools
# import distutils.core


setuptools.setup(
    name="sparklines",
    version="0.4.2",
    author="Dinu Gherman",
    author_email="gherman@darwin.in-berlin.de",
    description="Generate sparklines for numbers using Unicode characters only.",
    license="GPL",
    keywords="visualization, chart, tool",
    url="https://github.com/deeplook/sparklines",
    packages=setuptools.find_packages(exclude="test"),
    long_description=io.open("README.rst", encoding="utf-8").read(),
    install_requires=[],
    entry_points={"console_scripts": ["sparklines=sparklines.__main__:main"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Other Audience",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: PyPy",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    # cmdclass={"test": PyTest},
    package_data={
        # 'sparklines': ['foo.csv'],
    },
)
