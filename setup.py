from setuptools import setup, find_packages

setup(
    name="echoed",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pydantic",  # Add your dependencies here
        "jinja2",
    ],
    extras_require={
        "dev": ["pytest", "black", "mypy"],  # Development dependencies
    },
    entry_points={
        "console_scripts": [
            "generate_models=cold.scripts.regenerate_models:main",
        ],
    },
    python_requires=">=3.7",
    description="A battery digital twin framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/DigiBatt/echoed",  # Replace with your repository URL
    author="Simon Clark",
    author_email="your-email@example.com",
)
