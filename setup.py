from setuptools import setup

setup(
    name='pudgy',
    version='0.0.4',
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
        "dotmap"
    ],
    )

