from setuptools import setup
from ssh_globals import VERSION

setup(
    name='sshclick',
    version=VERSION,
    py_modules=['sshclick'],
    install_requires=[
        'rich',             #currently refactoring for rich
        'click',
        'prettytable',      #TODO: remove when rich fully integrated
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'sshc = main:cli',
        ],
    },
)
