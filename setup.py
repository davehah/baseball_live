from setuptools import setup, find_packages

setup(
    name='baseball_live',
    version='0.1.0',
    description='A package to visualize live baseball data on the commandline.',
    packages=find_packages(),
    install_requires=['MLB-StatsAPI', 'arrow', 'tabulate'],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'baseball_live = baseball_live.baseball_term:main'
        ]
    },
)