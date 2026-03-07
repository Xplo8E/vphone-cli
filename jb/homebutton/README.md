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

Single press:

```bash
./fake_button
```

Custom delay/repeat:

```bash
./fake_button --delay-ms 90 --repeat 3
```
