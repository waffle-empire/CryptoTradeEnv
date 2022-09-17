from setuptools import find_packages, setup

setup(
    name='gym_crypto',
    version='0.0.1',
    packages=find_packages(),
    author='Joren-vanGoethem',
    author_email='jorenvangoethem@hotmail.com',
    install_requires=['gym>=0.26.0', 'numpy>=1.22.4', 'pandas>=1.4.3', 'matplotlib>=3.5.3', 'TA-lib>=0.4.0', 'numba>=0.56.2'],
    package_data={'gym_crypto': ['datasets/data/*']},
)
