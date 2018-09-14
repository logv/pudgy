from setuptools import setup

try:
    # python2
    execfile('pudgy/version.py')
except NameError as e:
    # python3
    eval('exec(open("./pudgy/version.py").read())')

setup(
    name='pudgy',
    version=__version__,
    author='okay',
    author_email='okayzed+pudgy@gmail.com',
    include_package_data=True,
    packages=['pudgy', 'pudgy.components'],
    url='http://github.com/raisjn/pudgy',
    license='MIT',
    description='a component library for flask',
    long_description=open('README.md').read(),
    install_requires=[
        "flask",
        "pystache",
        "libsass",
        "dotmap",
        "diskcache"
    ],
    )

