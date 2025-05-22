from setuptools import setup

setup(
    name="water_quality",
    version="0.1",
    packages=[""],
    package_data={"": ["*.proto"]},
    install_requires=["grpcio", "pika"],
)