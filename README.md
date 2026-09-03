<div align="center">
  <a href="https://github.com/LMCache/LMCache">
    <img src="asset/logo.png" alt="LMCache logo" width="45%">
  </a>

  <h1>LMCache L2 Plugins</h1>
  <p><strong>The upstream-maintained community home for vendor L2 adapter plugins for LMCache.</strong></p>
</div>

This repository gives storage and infrastructure vendors a shared place to publish, document, and maintain L2 adapter integrations for [LMCache](https://github.com/LMCache/LMCache).

LMCache core defines the L2 adapter interface and loads external implementations. This companion repository hosts integrations built against that interface; it is not a fork of LMCache, and plugins hosted here are not bundled into the core `lmcache` package unless explicitly stated.

The repository is at an early stage. We plan to grow shared CI, compatibility testing, contribution templates, and integration documentation over time.

## Get started

- [Install and use an L2 plugin](docs/installation-and-integration.md)
- [Learn how to build an external L2 adapter](https://github.com/LMCache/LMCache/blob/dev/docs/source/developer_guide/extending_lmcache/storage_plugins.rst#mp-mode-l2-adapter-plugins-plugin)
- [LMCache documentation](https://docs.lmcache.ai/)
- [LMCache core repository](https://github.com/LMCache/LMCache)

## What belongs here

Vendors and community maintainers can contribute in either of two ways:

1. **Host the implementation here.** Contribute the plugin source, packaging metadata, tests, and documentation to this repository.
2. **Maintain the implementation elsewhere.** Keep the source and release process in a vendor-owned project, then contribute an integration document here that links to the package, source, support channel, and compatibility information.

Both models are welcome. In either case, an integration should clearly identify its maintainer, license, supported LMCache versions, installation steps, configuration, and validation status.

## Where should the plugin live?

| Consideration | Maintained in this repository | Maintained in a vendor repository |
| --- | --- | --- |
| Discoverability | Listed with other LMCache integrations in one upstream-maintained location | Discoverability depends on the vendor project; a documentation entry here can provide a common entry point |
| Review and standards | Benefits from shared LMCache community review and future common checks | Uses the vendor's own review, release, and support processes |
| Release cadence | May need to follow shared repository conventions and coordinated compatibility work | Can follow the vendor's product and driver release cadence |
| CI and hardware | Can participate in common CI as the repository adds it; vendor hardware may still be required | Vendor has full control of specialized hardware, credentials, and test infrastructure |
| Packaging and licensing | Must be suitable for an upstream open-source repository | Can accommodate vendor-specific packaging or distribution constraints |
| Maintenance responsibility | Shared visibility, with an explicitly identified vendor or community owner | Vendor retains primary responsibility for compatibility, releases, and support |

Choose the model that produces the most reliable integration for users. A documentation-only contribution is encouraged when the implementation needs vendor-specific infrastructure or an independent lifecycle.

## Contributing an integration

Before opening a pull request:

1. Read the upstream [external L2 adapter guide](https://github.com/LMCache/LMCache/blob/dev/docs/source/developer_guide/extending_lmcache/storage_plugins.rst#mp-mode-l2-adapter-plugins-plugin).
2. Decide whether the pull request will contain the implementation or an integration document that points to an external project.
3. Document supported LMCache versions, dependencies, configuration fields, operational limitations, and the responsible maintainer.
4. Include installation and `lmcache server --l2-adapter ...` examples that users can reproduce.
5. Describe the tests performed and any hardware or service required to run them.

Open an issue first when the interface or repository layout needs coordination with LMCache maintainers.

## License

Unless a subproject states otherwise, content in this repository is licensed under the [Apache License 2.0](LICENSE). External projects linked from this repository may use their own licenses.
