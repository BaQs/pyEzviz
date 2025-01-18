import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pyezvizapi',
    version="1.0.0.6",
    license='Apache Software License 2.0',
    author='Renier Moorcroft',
    author_email='RenierM26@users.github.com',
    description='Pilot your Ezviz cameras',
    long_description="Pilot your Ezviz cameras with this module. Please view readme on github",
    url='https://github.com/RenierM26/pyEzvizApi/',
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
    'console_scripts': ['pyezvizapi = pyezvizapi.__main__:main']
    },
    python_requires = '>=3.6'
)
