# Getting the COM port to show up to flash the TigerScale V3

The TigerScale V3 uses an **ESP32-S3** chip. To flash the firmware, your computer needs to see the board as a **COM port / serial port**.

On most recent computers this port shows up **on its own** when you plug the board in.
If no port appears in the flasher, a small driver is missing: follow the section for your system below.

> **Before you start**
> - Use a real **USB data cable** (some cables only charge and carry no data).

---

## macOS — nothing to install

No driver needed.
Plug in the board, open the flasher, and the board shows up directly in the list. Select it and start the flash.

If it doesn't appear: swap the USB cable and try again.

---

## Windows — install the driver (if no COM port appears)

If the flasher shows no port, the Espressif USB driver is missing. Install it
from Espressif's own tooling page:

**[dl.espressif.com/dl/idf-installer](https://dl.espressif.com/dl/idf-installer/)**

Download `idf-env` from there, then run it as administrator with:

```powershell
.\idf-env.exe driver install --espressif
```

Then:

1. Wait for it to finish (a few seconds).
2. **Unplug and plug the board back in.**
3. Reopen the flasher: the port (e.g. `USB JTAG/serial debug unit (COM3)`) should now appear.

> Downloading the tool yourself, rather than pasting a one-line command that
> fetches and runs an executable with administrator rights, means you can see
> what you are about to run and where it came from. It is one extra click.

✓ Select this port and start the flash.

---

## Linux — grant access to the serial port

The port usually shows up on its own (`/dev/ttyACM0`), but your user needs permission to access it.

1. Open a **terminal**.
2. Add yourself to the group that manages serial ports:

   ```bash
   sudo usermod -aG dialout $USER
   ```

3. **Log out and log back in** (or reboot) for it to take effect.
4. Plug the board back in and reopen the flasher.

> Tip: if you use the flasher **in a browser** (Web Serial), use **Google Chrome** or **Microsoft Edge**; Firefox does not support this feature.

---

## Still not working

- **Swap the USB cable** (problem #1: a "charge-only" cable).
- Try **another USB port** on the computer (preferably a direct port, not a hub).
- On Windows, open **Device Manager**: if you see a device with a yellow exclamation mark, the driver is missing → redo the Windows section above.
- To force flash mode: hold the **BOOT** button, press **RESET** once, then release **BOOT**, and try again.
