# Solax Export Control (Home Assistant Custom Integration)

Custom integration for controlling Solax export limit via the same encrypted web API flow used by the Solax web UI.

## Features (v1)

- Set export limit from Home Assistant using a Number entity
- Configure export range (min/max watts)
- Read current export status from API every hour
- Optional PIN handling (masked in config flow)

## Install via HACS (Custom Repository)

1. In HACS, add this repository as a custom integration.
2. Install `Solax Export Control`.
3. Restart Home Assistant.
4. Add integration from Settings -> Devices & Services.

## Configuration fields

- `sn`: WiFi/dongle SN (e.g. `SYAAD8TBMH`)
- `inverter_sn`: Inverter serial number
- `token_id`: Solax web token ID
- `pin`: Installer PIN (optional, masked)
- `min_export_w`: Minimum allowed export setting in watts
- `max_export_w`: Maximum allowed export setting in watts

## Security note

The PIN is stored in Home Assistant config entry storage and masked in the UI, but not strongly encrypted by this integration itself. For stronger protection, use host-level disk encryption and limit HA host access.
