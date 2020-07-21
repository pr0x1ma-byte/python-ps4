import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-ps4", # Replace with your own username
    version="0.0.1",
    author="grant100",
    description="Make your PS4 an IOT device",
    #long_description=long_description,
    #long_description_content_type="text/markdown",
    url="https://github.com/grant100/python-ps4",
    packages=setuptools.find_packages(),
    install_requires=['Flask', 'Flask-Cors', 'pycryptodome'],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)