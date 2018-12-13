from setuptools import setup, find_packages


setup(
    name='pubsub.py',
    author='Superbalist Engineering',
    author_email='tech@superbalist.com',
    version='2.0.0',
    description='Python PubSub Adapter for gcloud',
    long_description='Python PubSub Adapter for gcloud',
    url='https://github.com/Superbalist/python-pubsub',
    install_requires=[
        'google.cloud.pubsub>=0.33.1',
        'jsonschema',
        'requests',
    ],
    packages=find_packages(),
    zip_safe=False)
