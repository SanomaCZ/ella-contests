from setuptools import setup, find_packages
import ella_contests

install_requires = [
    'Django>=1.8',
    'ella>=3.0.3',
]

tests_require = [
    'nose',
    'coverage',
    'mock',
]

long_description = open('README.rst').read()

setup(
    name='ella-contests',
    version=ella_contests.__versionstr__,
    description='Contests for ella project',
    long_description=long_description,
    author='Sanoma Media',
    author_email='online-dev@sanoma.cz',
    license='BSD',
    url='https://github.com/SanomaCZ/ella-contests',

    packages=find_packages(
        where='.',
        exclude=('doc', 'test_ella_contests',)
    ),

    include_package_data=True,

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=install_requires,


    test_suite='test_ella_contests.run_tests.run_all',
    tests_require=tests_require,
)
