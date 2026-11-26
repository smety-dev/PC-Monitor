import unittest
from temperatures import select_temperatures


class TemperatureTests(unittest.TestCase):
    def test_preferred_sensors(self):
        rows = [
            {"Identifier": "/amdcpu/0/temperature/0", "Name": "Core (Tctl/Tdie)", "Value": 62},
            {"Identifier": "/amdcpu/0/temperature/1", "Name": "Core #1", "Value": 70},
            {"Identifier": "/amdgpu/0/temperature/0", "Name": "GPU Core", "Value": 55},
            {"Identifier": "/amdgpu/0/temperature/1", "Name": "GPU Hot Spot", "Value": 90},
        ]
        self.assertEqual(select_temperatures(rows), (62, 55))

    def test_missing_and_invalid(self):
        self.assertEqual(select_temperatures([
            {"Identifier": "/intelcpu/0/temperature/0", "Name": "CPU Package", "Value": None},
            {"Identifier": "/nvidiagpu/0/temperature/0", "Name": "GPU Core", "Value": "nan"},
        ]), (None, None))

    def test_cpu_fallback(self):
        self.assertEqual(select_temperatures([
            {"Identifier": "/intelcpu/0/temperature/0", "Name": "Core #1", "Value": 50},
            {"Identifier": "/intelcpu/0/temperature/1", "Name": "Core #2", "Value": 52},
        ]), (52, None))


if __name__ == "__main__":
    unittest.main()
