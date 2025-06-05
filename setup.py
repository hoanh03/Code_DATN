from setuptools import setup, find_packages

setup(
    name="python-test-generator",
    version="0.1.0",
    description="A tool for generating test cases for Python modules",
    author="Python Test Generator Team",
    author_email="example@example.com",
    url="",  # Internal project, not publicly available
    packages=find_packages(where="src") + ["source_files"],
    package_dir={"": "src", "source_files": "source_files"},
    python_requires=">=3.7",
    install_requires=[
        'click',
        'jinja2',
        'numpy',
        'pillow',
        'pytest',
        'requests',
        'coverage',
        'pytest-cov'
    ],
    entry_points={
        "gui_scripts": [
            "test-generator-gui=test_generator_app:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="testing, pytest, test generation",
)