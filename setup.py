import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-ps4",
    version="1.0.0",
    author="Grant Sowards",
    description="Make your PS4 an IOT device",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/grant100/python-ps4",
    packages=setuptools.find_packages(),
    install_requires=['Flask', 'Flask-Cors', 'pycryptodome', 'setproctitle'],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Home Automation",
        ""
    ],
    python_requires='>=3.6',
)
