# USB PID source references

## Authoritative PID source

The project uses the Linux USB ID repository (`usb.ids`) as the authoritative
reference for vendor/product IDs when expanding `HackAttack/modules/device_database.json`.
This list is maintained by the usbutils project and mirrors the data published on
linux-usb.org.

## Update notes

* 2026-01-09: Added missing vendor IDs and product IDs using the locally cached
  `docs/usb.ids` file in this repository.
