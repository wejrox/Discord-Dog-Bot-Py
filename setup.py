from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE.md') as f:
    project_license = f.read()

setup(
    name='dogbot',
    version='0.1.0',
    description='Python bot for putting an alleged "dog" user through the judiciary system '
                'to determine guilt or innocence.',
    long_description=readme,
    author='James McDowell',
    url='https://github.com/wejrox/Discord-Dog-Bot-Py',
    license=project_license,
    packages=find_packages(exclude=('tests', 'docs', 'venv', '.github'))
)
