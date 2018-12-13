# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2018-12-04
- Remove `HTTPAdapter` 
- Add optional pubsub rest proxy to `GooglePubSub` 
adapter - see [js-pubsub-rest-proxy](https://github.com/Superbalist/js-pubsub-rest-proxy)
- Add missing methods to `BaseAdapter` interface

## [1.0.0] - 2018-11-21
- [BREAKING] No longer supports python 2
- Cache the results of get_topic

## [0.3.9] - 2018-04-25
- Catch new exception types after google.cloud.pubsub dependency update

## [0.3.8] - 2018-04-25
- Updated google.cloud.pubsub dependency to 0.33.1

## [0.3.7] - 2018-02-12
- Added CachedRefResolver to allow use of external cache service

## [0.3.6] - 2015-12-03

[Unreleased]: https://github.com/Superbalist/python-pubsub/compare/2.0.0...HEAD
[2.0.0]: https://github.com/Superbalist/python-pubsub/compare/1.0.0...2.0.0
[1.0.0]: https://github.com/Superbalist/python-pubsub/compare/0.3.9...1.0.0
[0.3.9]: https://github.com/Superbalist/python-pubsub/compare/0.3.8...0.3.9
[0.3.8]: https://github.com/Superbalist/python-pubsub/compare/0.3.7...0.3.8
[0.3.7]: https://github.com/Superbalist/python-pubsub/compare/0.3.6...0.3.7
[0.3.6]: https://github.com/Superbalist/python-pubsub/compare/0.0.1...0.3.6
