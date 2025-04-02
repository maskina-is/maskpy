from setuptools import setup, find_packages

setup(
  author = "Maskína",
  description="Helper functions for Maskína",
  name = "maskpy",
  version="0.1.0",
  packages=find_packages(include=["maskpy", "maskpy.*"])
)

  
