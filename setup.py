from setuptools import setup

setup(
    name='sshclick',
    version='0.2.0',
    py_modules=['sshclick'],
    install_requires=[
        # 'typer',            #currently refactoring for typer/rich (uses click in backgroud)
        # 'rich',             #currently refactoring for typer/rich
        'click',            #TODO: remove when typer fully integrated
        'prettytable',      #TODO: remove when rich fully integrated
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            # 'sshclick = sshclick:cli',
            # 'sshc = sshclick:cli',
            'sshc = main:cli',
        ],
    },
)
