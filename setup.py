from setuptools import setup, find_packages

setup(
    name='gym_crypto',
    version='0.0.1',
    packages=find_packages(),

    author='Joren-vanGoethem',
    author_email='jorenvangoethem@hotmail.com',

    install_requires=[
        'gym>=0.12.5',
        'numpy>=1.16.4',
        'pandas>=0.24.2',
        'matplotlib>=3.1.1',
        'TA-lib>=0.4.0'
    ],

    package_data={
        'gym_crypto': ['datasets/data/*']
    }
)
