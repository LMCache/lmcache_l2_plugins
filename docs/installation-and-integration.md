# Installing and Using an L2 Plugin

An L2 plugin runs in the LMCache server process. Install the plugin package into the same Python environment as LMCache, then identify its module and adapter class in the server's `--l2-adapter` configuration.

For the implementation contract, see the LMCache core guide: [MP-mode L2 adapter plugins](https://github.com/LMCache/LMCache/blob/dev/docs/source/developer_guide/extending_lmcache/storage_plugins.rst#mp-mode-l2-adapter-plugins-plugin).

## 1. Install LMCache and the plugin

Install a released package:

```bash
python -m pip install lmcache
python -m pip install <vendor-l2-plugin-package>
```

For local development, install the plugin checkout in editable mode:

```bash
python -m pip install -e /path/to/vendor-l2-plugin
```

Use the LMCache version range documented by the plugin. Native plugins may also require vendor libraries, storage clients, credentials, or services.

## 2. Start the LMCache server

Pass a plugin descriptor as JSON to `--l2-adapter`:

```bash
lmcache server \
  --l1-size-gb 10 \
  --eviction-policy LRU \
  --port 5555 \
  --l2-adapter '{
    "type": "plugin",
    "module_path": "my_vendor_l2.adapter",
    "class_name": "MyVendorL2Adapter",
    "adapter_params": {
      "endpoint": "storage.example.com:9000",
      "namespace": "production"
    }
  }'
```

Replace the example module, class, and parameters with values from the plugin's documentation.

The fields have the following meanings:

| Field | Purpose |
| --- | --- |
| `type` | Must be `plugin` for a separately packaged Python L2 adapter |
| `module_path` | Import path containing the adapter class |
| `class_name` | Class implementing LMCache's `L2AdapterInterface` |
| `adapter_params` | Plugin-specific constructor configuration |
| `config_class_name` | Optional explicit configuration class; most plugins can use LMCache's automatic discovery |

Keep secrets out of shell history and process arguments. When a plugin accepts credentials through environment variables, files, or a secret manager, prefer that mechanism over embedding credentials in the JSON.

## 3. Connect the serving engine

Configure the serving engine to use the standard LMCache multiprocess connector and point it at the server address and port. The L2 plugin does not change the serving-engine connector contract; it is selected by the LMCache server through `--l2-adapter`.

See the upstream [LMCache multiprocess deployment guide](https://docs.lmcache.ai/mp/deployment.html) for the current serving-engine configuration.

## 4. Verify the integration

After startup:

1. Confirm the server imports the configured module and creates the adapter without errors.
2. Send a request that stores KV cache data, then repeat a compatible request.
3. Check plugin and LMCache metrics or logs for a non-zero store and retrieval result.
4. Restart the server after installing, upgrading, or reconfiguring the plugin.

For development, test failure handling, concurrent store and load activity, cleanup, capacity limits, and compatibility with every supported LMCache version.

## Troubleshooting

- **Module not found:** verify the plugin is installed in the exact environment that launches `lmcache server`.
- **Class not found:** check `module_path` and `class_name`, including capitalization.
- **Invalid adapter type:** verify `"type": "plugin"` and use a current LMCache release that supports external L2 adapters.
- **Connection or authentication failure:** validate the plugin-specific endpoint, credentials, client libraries, and network access.
- **No cache hits:** confirm that stores complete successfully and verify a positive retrieval count rather than relying only on a generic retrieval log message.
