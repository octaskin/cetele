from setuptools import setup

setup(
    name="cetele",
    version="0.1",
    description="a simple script to ditch gsheets for budgeting",
    url="https://github.com/cenktaskin/cetele",
    author="C. Taskin",
    author_email="orhuncenktaskin@gmail.com",
    entry_points={"console_scripts": ["cetele=cetele.command_line:main"]},
    install_requires=["pyfzf", "termcolor"],
)
