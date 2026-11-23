---
description: Read-only fan RPM, temperatures and PWM for Uniwill/Tongfang laptops whose BIOS does not expose the INOU0000 ACPI device (uses the ACPI-WMI EC bridge). Installs or removes the uniwill-ec-hwmon-dkms package.
---

# /fan-sensor

Exposes the physical fan tachometers of Uniwill/Tongfang notebooks to `sensors` and any hwmon consumer:

```bash
./bin/linux-wayland-config fan-sensor status
```

---

## Why this exists

Many Tongfang/Avell BIOSes never create the `INOU0000` ACPI device that the in-tree `uniwill-laptop` driver requires, so `sensors` shows CPU/GPU temperatures but **no fan RPM**. The EC is still reachable through the `AcpiTest_MULong` WMI method (`ABBC0F6F-8EA1-11D1-00A0-C90629100000`, method 4).

The `uniwill-ec-hwmon-dkms` package provides a **read-only** hwmon driver for that path:

| Attribute | Source |
| :--- | :--- |
| `temp1_input` / `temp2_input` | EC `0x043E` / `0x044F` (CPU/GPU °C) |
| `fan1_input` / `fan2_input` | EC `0x0464..0x0465` / `0x046C..0x046D` (big-endian RPM) |
| `pwm1` / `pwm2` | EC `0x075B` / `0x075C` (0–255) |

It never writes to the EC and can be removed at any time.

---

## Mandatory AI Agent Workflow

1. Run the read-only check first:

```bash
./bin/linux-wayland-config fan-sensor status
```

2. Report the findings:
   - WMI EC bridge present/absent;
   - `INOU0000` present/absent (if present, the in-tree driver is the right path — do not install);
   - package/module/hwmon state;
   - current RPM/temps when active.
3. Ask the user before installing:
   - **Install** (DKMS, requires sudo and an AUR helper) [Recommended when supported and inactive];
   - **Keep as is**;
   - **Uninstall** (read-only driver, no side effects).
4. Execute:

```bash
./bin/linux-wayland-config fan-sensor install
./bin/linux-wayland-config fan-sensor uninstall
```

5. Verify with `sensors | grep -A8 uniwill_ec` and follow the Evidence-First output contract.

---

## Safety and conflicts

* **Read-only:** no EC writes, no fan curves, no TDP changes.
* Do **not** install together with `clevo-drivers-dkms-git` / `tuxedo-drivers`: their `uniwill_wmi` driver binds the same WMI GUID and performs EC writes.
* If `INOU0000` exists, the in-tree `uniwill-laptop` driver already handles the EC; this package refuses to install.

---

## Standard Output Format (Evidence-First Verdict)

### 🎯 Verdict: [ ✅ SUCCESS | ❌ FAILURE | ⚠️ PARTIAL SUCCESS ]
*One sentence summarizing the observable outcome.*

#### 🔬 Technical Evidence & Ground Truth:
| Component | Verified State | Proof |
| :--- | :--- | :--- |
| WMI EC bridge | present/absent | `ls /sys/bus/wmi/devices \| grep ABBC0F6F` |
| In-tree path | `INOU0000` present/absent | `ls /sys/bus/acpi/devices \| grep INOU0000` |
| Package | installed/not installed | `pacman -Q uniwill-ec-hwmon-dkms` |
| hwmon | `uniwill_ec` present/absent | `sensors \| grep -A8 uniwill_ec` |

#### 👉 Action Required:
```bash
./bin/linux-wayland-config fan-sensor status
```
