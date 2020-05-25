from setuptools import setup, find_packages


setup(
    name='pubsub.py',
    author='Superbalist Engineering',
    author_email='tech@superbalist.com',
    version='1.0.1',
    description='Python PubSub Adapter for gcloud',
    long_description='Python PubSub Adapter for gcloud',
    url='https://github.com/Superbalist/python-pubsub',
    install_requires=[
        'google-cloud-pubsub==1.5.0',
        'jsonschema',
        'requests',
    ],
    packages=find_packages(),
    zip_safe=False)
