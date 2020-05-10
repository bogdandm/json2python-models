# Changelog

## [v0.2.1](https://github.com/bogdandm/json2python-models/tree/v0.2.1) (2020-05-10)

[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.2.0...v0.2.1)

* Update PyPi package description

## [v0.2.0](https://github.com/bogdandm/json2python-models/tree/v0.2.0) (2020-05-10)

[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.1.2...v0.2.0)

**Merged pull requests:**

- Change default classes structure type to FLAT [\#32](https://github.com/bogdandm/json2python-models/pull/32) ([bogdandm](https://github.com/bogdandm))
- Add python3.8 and 3.9-dev to test matrix [\#31](https://github.com/bogdandm/json2python-models/pull/31) ([bogdandm](https://github.com/bogdandm))
- Pydantic models generation [\#29](https://github.com/bogdandm/json2python-models/pull/29) ([bogdandm](https://github.com/bogdandm))
- Add more reserved words [\#28](https://github.com/bogdandm/json2python-models/pull/28) ([bogdandm](https://github.com/bogdandm))
- Update ordered-set requirement from ==3.\* to ==4.\* [\#27](https://github.com/bogdandm/json2python-models/pull/27) ([dependabot-preview[bot]](https://github.com/apps/dependabot-preview))

## [v0.1.2](https://github.com/bogdandm/json2python-models/tree/v0.1.2) (2019-06-17)

[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.1.1...v0.1.2)

* Fix models merging
* Fix Union optimization in merged models
* Fix optimizing Union\[Unknown\] or Union\[None\]

**Merged pull requests:**

- Bug fixes [\#25](https://github.com/bogdandm/json2python-models/pull/25) ([bogdandm](https://github.com/bogdandm))

## [v0.1.1](https://github.com/bogdandm/json2python-models/tree/v0.1.1) (2019-06-13)
[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.1.0.post2...v0.1.1)

**Merged pull requests:**

- Disable unicode conversion flag [\#24](https://github.com/bogdandm/json2python-models/pull/24) ([bogdandm](https://github.com/bogdandm))

## [v0.1.0.post2](https://github.com/bogdandm/json2python-models/tree/v0.1.0.post2) (2019-05-02)
[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.1.0.post1...v0.1.0.post2)

## [v0.1.0.post1](https://github.com/bogdandm/json2python-models/tree/v0.1.0.post1) (2019-04-24)
[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.1.0...v0.1.0.post1)

## [v0.1.0](https://github.com/bogdandm/json2python-models/tree/v0.1.0) (2019-04-24)
[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.1b2...v0.1.0)

**Merged pull requests:**

- Adding readme [\#22](https://github.com/bogdandm/json2python-models/pull/22) ([bogdandm](https://github.com/bogdandm))
- Post init converters for string types [\#21](https://github.com/bogdandm/json2python-models/pull/21) ([bogdandm](https://github.com/bogdandm))
- No ordereddict [\#20](https://github.com/bogdandm/json2python-models/pull/20) ([bogdandm](https://github.com/bogdandm))
- Process empty dict as Dict type [\#19](https://github.com/bogdandm/json2python-models/pull/19) ([bogdandm](https://github.com/bogdandm))
- Fix pytest version conflict [\#18](https://github.com/bogdandm/json2python-models/pull/18) ([bogdandm](https://github.com/bogdandm))
- Decode unicode and remove non-words characters in models fields names [\#17](https://github.com/bogdandm/json2python-models/pull/17) ([bogdandm](https://github.com/bogdandm))
- Does not add METADATA\_FIELD\_NAME to metadata if original fields name is a same as generated one [\#16](https://github.com/bogdandm/json2python-models/pull/16) ([bogdandm](https://github.com/bogdandm))

## [v0.1b2](https://github.com/bogdandm/json2python-models/tree/v0.1b2) (2018-11-30)
[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.1b1...v0.1b2)

**Merged pull requests:**

- Flat models structure generation [\#15](https://github.com/bogdandm/json2python-models/pull/15) ([bogdandm](https://github.com/bogdandm))
- Dataclasses code generation [\#14](https://github.com/bogdandm/json2python-models/pull/14) ([bogdandm](https://github.com/bogdandm))
- Evaluate generated code in tests [\#13](https://github.com/bogdandm/json2python-models/pull/13) ([bogdandm](https://github.com/bogdandm))
- NoneType -\> Null refactoring \(fix wrong NoneType annotation\) [\#12](https://github.com/bogdandm/json2python-models/pull/12) ([bogdandm](https://github.com/bogdandm))

## [v0.1b1](https://github.com/bogdandm/json2python-models/tree/v0.1b1) (2018-11-27)
[Full Changelog](https://github.com/bogdandm/json2python-models/compare/v0.1a1...v0.1b1)

**Merged pull requests:**

- Add --dict-keys-regex and --dict-keys-fields arguments; [\#11](https://github.com/bogdandm/json2python-models/pull/11) ([bogdandm](https://github.com/bogdandm))

## [v0.1a1](https://github.com/bogdandm/json2python-models/tree/v0.1a1) (2018-11-27)
**Merged pull requests:**

- Cli [\#10](https://github.com/bogdandm/json2python-models/pull/10) ([bogdandm](https://github.com/bogdandm))
- Dict key as data [\#9](https://github.com/bogdandm/json2python-models/pull/9) ([bogdandm](https://github.com/bogdandm))
- Datetime parsing [\#7](https://github.com/bogdandm/json2python-models/pull/7) ([bogdandm](https://github.com/bogdandm))
- Optimization [\#5](https://github.com/bogdandm/json2python-models/pull/5) ([bogdandm](https://github.com/bogdandm))
- Attrs [\#4](https://github.com/bogdandm/json2python-models/pull/4) ([bogdandm](https://github.com/bogdandm))
- Absolute forward ref [\#3](https://github.com/bogdandm/json2python-models/pull/3) ([bogdandm](https://github.com/bogdandm))
- Models code generation [\#2](https://github.com/bogdandm/json2python-models/pull/2) ([bogdandm](https://github.com/bogdandm))
- Travis [\#1](https://github.com/bogdandm/json2python-models/pull/1) ([bogdandm](https://github.com/bogdandm))



\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*

\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*


\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*


\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
