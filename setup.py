import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()

setuptools.setup(
    name='pyEzviz',
    version="0.1.5.6",
    license='Apache Software License',
    author='Pierre Ourdouille',
    author_email='baqs@users.github.com',
    description='Pilot your Ezviz cameras',
    long_description="Pilot your Ezviz cameras with this module. Please view readme on github",
    url='http://github.com/baqs/pyEzviz/',
    packages=setuptools.find_packages(include=['pyezviz']),
    setup_requires=[
        'requests',
        'setuptools'
    ],
    install_requires=[
        'requests',
        'fake_useragent',
        'pandas'
    ],
    entry_points={
    'console_scripts': [
        'pyezviz = pyezviz.__main__:main'
    ]
    }
)
