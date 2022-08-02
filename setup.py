from setuptools import setup
from ssh_globals import VERSION

setup(
    name="sshclick",
    version=VERSION,
    description="SSH Config manager",
    author="Karlo Tisaj",
    author_email="karlot@gmail.com",
    url="https://github.com/karlot/sshclick",
    py_modules=["sshclick"],
    install_requires=[
        "click>=8.1.3",
        "prettytable>=3.2.0",
        "rich>=12.5.1",
    ],
    entry_points={
        "console_scripts": [
            "sshc = main:cli",
        ],
    },
)
