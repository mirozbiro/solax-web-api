# Solax Export Control (Home Assistant Custom Integration)

Custom integration for controlling Solax export limit via the same encrypted web API flow used by the Solax web UI.

## Features (v1)

- Set export limit from Home Assistant using a Number entity
- Configure export range (min/max watts)
- Read current export status from API every hour
- Optional PIN handling (masked in config flow)
- A preset switch to jump directly between the configured minimum and maximum export values

## Install via HACS (Custom Repository)

1. In HACS, add this repository as a custom integration.
2. Install `Solax Export Control`.
3. Restart Home Assistant.
4. Add integration from Settings -> Devices & Services.

## Configuration fields

- `sn`: WiFi/dongle SN (example: `SYAAD8TXXXXX`)
- `inverter_sn`: Inverter serial number (example: `H34A10J36XXXX`)
- `token_id`: Solax web token ID
- `pin`: Installer PIN (optional, masked)
- `min_export_w`: Minimum allowed export setting in watts
- `max_export_w`: Maximum allowed export setting in watts

### Where to find `token_id`

`token_id` is taken from your active Solax web session and can rotate/expire.

1. Log in at `https://global.solaxcloud.com`.
2. Open browser DevTools.
3. Go to `Application` (or `Storage`) -> `Local Storage`.
4. Select the Solax domain and find `tokenId`.
5. Copy that value into the integration config.

If requests start failing after a while, refresh this value from a new login session.

## Security note

The PIN is stored in Home Assistant config entry storage and masked in the UI, but not strongly encrypted by this integration itself. For stronger protection, use host-level disk encryption and limit HA host access.
