# Home Button Helper (No Frida Runtime)

This helper uses the proven working path directly:
- `IOHIDEventSystemClientCreateSimpleClient`
- `IOHIDEventCreateKeyboardEvent(usagePage=0x0C, usage=0x40)`
- `IOHIDEventSystemClientDispatchEvent`

## Build

```bash
cd jb/homebutton
make
```

## Run In Guest

Default behavior (single run):
- Press Home once
- Press Enter once

```bash
./fake_button
```

This helper no longer accepts CLI args (no repeat/delay flags).
