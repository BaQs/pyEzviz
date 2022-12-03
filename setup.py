import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pyezviz',
    version="0.2.0.10",
    license='Apache Software License 2.0',
    author='Pierre Ourdouille',
    author_email='baqs@users.github.com',
    description='Pilot your Ezviz cameras',
    long_description="Pilot your Ezviz cameras with this module. Please view readme on github",
    url='http://github.com/baqs/pyEzviz/',
    packages=setuptools.find_packages(),
    setup_requires=[
        'requests',
        'setuptools'
    ],
    install_requires=[
        'requests',
        'pandas',
        'paho-mqtt',
        'xmltodict',
        'pycryptodome'
    ],
    entry_points={
    'console_scripts': ['pyezviz = pyezviz.__main__:main']
    },
    python_requires = '>=3.6'
)
