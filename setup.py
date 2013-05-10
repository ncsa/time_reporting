from setuptools import setup
setup(
    name = "time_reporting",
    version = "0.1-r1",
    packages = ["time_reporting"],
    install_requires = ["requests==0.13.6", "docopt"],
    entry_points = {
        'console_scripts': [
            'time_reporting = time_reporting.time_reporting:main',
            ]
    }
)
