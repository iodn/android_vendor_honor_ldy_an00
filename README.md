# HONOR LDY-AN00 vendor configuration

Vendor build definitions and proprietary-input inventories for unofficial
LineageOS 24.0 / Android 17. Android source path: `vendor/honor/ldy_an00`.
Branch: `lineage-24.0`. Tested input baseline: `10.0.0.113(C00E100R101P1)`. Matching inputs are required.

Official downloads and GhostLock status are listed in the
[firmware table](https://github.com/iodn/honor-ldy-an00-ghostlock#firmware-downloads-and-ghostlock-status).
Exploit vulnerability does not make vendor inputs interchangeable.

## Contents

- `Android.bp` and makefiles: retained framework-side vendor integration.
- `proprietary-files.txt`: required firmware paths.
- `proprietary-inputs.json` and component inventories: expected files and hashes.
- `stock-images.json` and `stock-modules.json`: retained boot/kernel inputs.
- `EXPORT-PROVENANCE.json`: original source identity and excluded inputs.

Proprietary blobs, private signing material, device-unique data and personal ADB
keys are excluded. Supply the matching stock/derived inputs before building. Some
components require the reconstruction steps in the device tree's IMS tools.
This configuration retains the qualified kernel/vendor baseline; updating Android
userspace alone does not update those components or their security patch coverage.

Use the pinned [manifest](https://github.com/iodn/android_manifest_ldy_an00) and
[device tree](https://github.com/iodn/android_device_honor_ldy_an00) together.
Preserve existing file-level licensing and review binary redistribution terms.

## Stock audio inputs

Prepare the pinned engine and tuning from extracted matching firmware partitions:

```sh
python3 tools/prepare_audio_sws.py --product-root /path/to/product --odm-root /path/to/odm
python3 tools/verify_audio_sws_inputs.py
```

The generator verifies all inputs and the resulting tuning bundle.
`audio-sws-framework.mk` defines the optional engine and tuning packages;
framework processing is controlled separately.
