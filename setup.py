from setuptools import setup

setup(
    name='sshclick',
    version='0.1.0',
    py_modules=['sshclick'],
    install_requires=[
        'click',
        'prettytable',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'sshclick = sshclick:cli',
            'sshc = sshclick:cli',
        ],
    },
)
