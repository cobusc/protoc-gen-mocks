from setuptools import setup, find_packages

with open("version", "r") as f:
    version = f.read().strip()

ENTRY_POINTS = {
    "console_scripts": [
        "protoc-gen-mocks=protoc_gen_mocks.protoc_gen_mocks:main",
    ]
}

setup(
    name="protoc-gen-mocks",
    maintainer="Cobus Carstens",
    maintainer_email="cobus.carstens@gmail.com",
    version=version,
    url="https://github.com/cobusc/protoc-gen-mocks",
    packages=find_packages(),
    package_data={
        "": ["version"]
    },
    entry_points=ENTRY_POINTS
)
