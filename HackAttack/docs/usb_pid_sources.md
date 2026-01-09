# USB PID source references

## Authoritative PID source

The project uses the Linux USB ID repository (`usb.ids`) as the authoritative
reference for vendor/product IDs when expanding `HackAttack/modules/device_database.json`.
This list is maintained by the usbutils project and mirrors the data published on
linux-usb.org.

## Update notes

* This update could not automatically pull `usb.ids` due to restricted network access
  in the execution environment, so no new PID entries were added. Future updates should
  re-run the PID comparison using a locally cached copy of `usb.ids` and record the
  retrieval date in this file.
