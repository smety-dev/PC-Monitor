"""Read-only diagnostic for the Intel Graphics Control Library.

ABI reference: https://github.com/intel/drivers.gpu.control-library/blob/master/include/igcl_api.h
No driver installation or elevated privileges are requested.
"""
import ctypes as c
import math
import sys


class InitArgs(c.Structure):
    _fields_ = [
        ("Size", c.c_uint32), ("Version", c.c_uint8),
        ("AppVersion", c.c_uint32), ("flags", c.c_uint32),
        ("SupportedVersion", c.c_uint32), ("ApplicationUID", c.c_uint8 * 16),
    ]


class TempProperties(c.Structure):
    _fields_ = [
        ("Size", c.c_uint32), ("Version", c.c_uint8),
        ("type", c.c_uint32), ("maxTemperature", c.c_double),
    ]


def probe():
    if sys.platform != "win32" or c.sizeof(c.c_void_p) != 8:
        print("Requires 64-bit Python on Windows.")
        return
    dll = c.CDLL("ControlLib.dll", winmode=0x00000800)
    handle = c.c_void_p
    signatures = {
        "ctlInit": [c.POINTER(InitArgs), c.POINTER(handle)],
        "ctlClose": [handle],
        "ctlEnumerateDevices": [handle, c.POINTER(c.c_uint32), c.POINTER(handle)],
        "ctlEnumTemperatureSensors": [handle, c.POINTER(c.c_uint32), c.POINTER(handle)],
        "ctlTemperatureGetProperties": [handle, c.POINTER(TempProperties)],
        "ctlTemperatureGetState": [handle, c.POINTER(c.c_double)],
    }
    for name, args in signatures.items():
        fn = getattr(dll, name)
        fn.argtypes = args
        fn.restype = c.c_uint32

    def enumerate_handles(fn, parent):
        count = c.c_uint32()
        result = fn(parent, c.byref(count), None)
        print(f"{fn.__name__}: 0x{result:08X}, count={count.value}")
        if result != 0 or not 0 < count.value <= 256:
            return []
        capacity = count.value
        handles = (handle * capacity)()
        result = fn(parent, c.byref(count), handles)
        print(f"Fetch handles: 0x{result:08X}")
        return handles[:min(count.value, capacity)] if result == 0 else []

    args = InitArgs()
    args.Size = c.sizeof(args)
    args.AppVersion = 0x00010000
    args.flags = 1
    api = handle()
    result = dll.ctlInit(c.byref(args), c.byref(api))
    print(f"ctlInit: 0x{result:08X}, supported version=0x{args.SupportedVersion:08X}")
    if result != 0 or not api.value:
        return
    try:
        for index, device in enumerate(enumerate_handles(dll.ctlEnumerateDevices, api)):
            if not device:
                continue
            print(f"Adapter {index}")
            for sensor in enumerate_handles(dll.ctlEnumTemperatureSensors, device):
                if not sensor:
                    continue
                props = TempProperties()
                props.Size = c.sizeof(props)
                prop_result = dll.ctlTemperatureGetProperties(sensor, c.byref(props))
                temp = c.c_double(float("nan"))
                result = dll.ctlTemperatureGetState(sensor, c.byref(temp))
                kind = {0: "global", 1: "GPU", 2: "memory", 3: "global min", 4: "GPU min", 5: "memory min"}.get(props.type, str(props.type)) if prop_result == 0 else "unknown"
                print(f"Sensor {kind}: status=0x{result:08X}, properties=0x{prop_result:08X}")
                if result == 0 and math.isfinite(temp.value):
                    print(f"Temperature: {temp.value:.1f} C")
    finally:
        print(f"ctlClose: 0x{dll.ctlClose(api):08X}")


if __name__ == "__main__":
    try:
        probe()
    except (OSError, AttributeError, ValueError) as exc:
        print(f"IGCL unavailable: {exc}")
