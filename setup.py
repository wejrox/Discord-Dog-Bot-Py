from typing import List

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE.md') as f:
    project_license = f.read()


def get_deps_from_file(file: str) -> List[str]:
    deps = []
    with open(file) as fh:
        for dep in fh.read().splitlines():
            if dep.startswith("-r"):
                deps.extend(get_deps_from_file(dep.split(" ")[1]))
            else:
                deps.append(dep)
    return deps


REQUIRED_DEPENDENCIES = get_deps_from_file('requirements.txt')
setup(
    name='dogbot',
    version='0.1.0',
    description='Python bot for putting an alleged "dog" user through the judiciary system '
                'to determine guilt or innocence.',
    long_description=readme,
    author='James McDowell',
    url='https://github.com/wejrox/Discord-Dog-Bot-Py',
    license=project_license,
    packages=find_packages(),
    install_requires=REQUIRED_DEPENDENCIES,
    entry_points={
        'console_scripts': ['dogbot = dogbot.__main__:console_entry']
    }
)
