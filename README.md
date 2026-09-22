# Rust RCON for Home Assistant

Control a Rust dedicated server over WebRCON and expose live stats.

**Entities:**
- `binary_sensor`: online (connectivity), restarting
- `sensor`: players (with a `player_names` attribute), queued, joining, server FPS, entities,
  uptime, max players, map, memory, network in/out, last save time, server version (disabled by default)
- `button`: save, restart server (60s warning)

**Services:** `rust_rcon.send_command` (returns the console output), `rust_rcon.say`.

## Install
1. HACS -> Custom repositories -> add this repo as *Integration* (or copy `custom_components/rust_rcon` into your HA config).
2. Restart Home Assistant.
3. Settings -> Devices & services -> Add integration -> **Rust RCON**.

If the RCON password (or host/port) changes later, use the integration's **Reconfigure** action
instead of removing and re-adding it. If a poll fails auth, HA will prompt you to reauthenticate
automatically.

## Server side
Launch args (or AMP's equivalent settings): `+rcon.web 1 +rcon.port 28016 +rcon.password "yourpass"`.
The RCON port is TCP, and is separate from the game port.

## Security
WebRCON sends the password in the connection URL, unencrypted. If HA is not on the same
network as the server, do NOT leave the RCON port open to the world. Firewall it to your home's
IP only, or reach it over a VPN (WireGuard/Tailscale).

## Example
```yaml
action: rust_rcon.send_command
data:
  command: "server.save"
response_variable: result
```
`{{ result.response }}` holds the output. Use `entry_id` only if you add more than one server.

## Development
```
pip install -r requirements_test.txt
pytest tests/
```
CI also runs `hassfest` and the HACS validation action on every push/PR.
