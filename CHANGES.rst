Changelog
=========

<<<<<<< HEAD
Version 0.11 (Not yet released)
=======
Version 0.11 (not yet released)
>>>>>>> develop
-------------------------------------------

- Update dependencies (old GitPython was broken).
- Fix up documentation.
- JIRA issue fetching normalizes ticket IDs to be uppercase. See #84.
- Update config file styler format to allow better grouping and ordering.
- Add support for docformatter styler. See #106.
- Add support for esformatter styler. See #110.
- Add support for goimports styler. See #108.
- Add support for generic stdin styler. See #112.
- Skip ticket verification when making a new ticket. See #114.
- Support ``zazu config`` subcommand to edit ~/.zazuconfig.yaml file. See #100.
- Enable SCM hosting shortcuts for ``zazu repo clone``.

Version 0.10.0 (Released Jul 2, 2017)
-------------------------------------

- ReadTheDocs support.
- Increase code coverage to 92%.
- Styling now automatic via git hook.

Version 0.9.2
-------------

- Stylers are now plugins.
- Support clang-format styler.
- CodeReviewers are now plugins.
- Support for GitHub code review creation.
- Support GitHub for ticket creation.

Version 0.8.2
-------------

- Initial version released to PyPi.
