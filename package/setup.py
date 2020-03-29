import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="covid19sim",
    version="0.1.1",
    author="Dr. Tobias Sproll, Simon Hommel, Dr. Peter Borrmann",
    author_email="covid19@the-quants.com",
    description="Simulation of Covid-19 with individal reproduction and communities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PeterBorrmann1965/Covid-19-simulation",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['plotly', 'pandas', 'numpy', 'scipy'],
    packages=setuptools.find_packages(),
    package_dir={'covid19sim': 'covid19sim'},
    package_data={'covid19sim': ['*.csv']},
)
