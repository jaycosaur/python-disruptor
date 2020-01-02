#  type: ignore
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="disruptor",
    version="0.0.1",
    author="Jacob Richter",
    author_email="jaycorichter@gmail.com",
    description="Python implementation of a disruptor: a multi-subscriber, multi-producer, blocking ring buffer.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaycosaur/disruptor",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)