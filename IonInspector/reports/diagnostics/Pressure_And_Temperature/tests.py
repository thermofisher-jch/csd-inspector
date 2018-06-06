from django.test import SimpleTestCase

from main import get_pressure_and_temp, INFO, WARN, ALARM
from reports.diagnostics.common.inspector_utils import TemporaryDirectory


class PressureAndTemperatureOkayTestCase(SimpleTestCase):
    def test_get_pressure_and_temp_pgm(self):
        files = {
            "explog_final.txt":
                "PGMTemperature: 30.42 - 31.14\n"
                "PGMPressure: 10.41 - 10.41\n"
                "PGM HW: 1.0\n"
                "Flow # Pressure (PSI) Internal T (C) Chip T (C) DAC0 DAC1 DAC2 DAC3\n"
                "4) 10.45 31.14 51.04 (0x5b67 0x5abc 0x5a48 0x5a9e)\n"
                "3) 10.45 31.14 51.04 (0x5b67 0x5abc 0x5a48 0x5a9e)\n"
                "2) 10.45 30.99 51.04 (0x5b67 0x5abc 0x5a48 0x5a9e)\n"
                "1) 10.45 31.14 51.04 (0x5b67 0x5abc 0x5a59 0x5a9e)\n"
                "0) 10.45 31.14 51.04 (0x5b77 0x5abc 0x5a59 0x5a9e)\n"
        }
        with TemporaryDirectory(files) as archive_path:
            pressure_message, temperature_message, level, flow_data = get_pressure_and_temp(archive_path,
                                                                                            "PGM_Run")
            self.assertEquals(level, INFO)

            # pressure
            self.assertEquals(pressure_message, None)
            self.assertEquals(flow_data["pressure"][0]["data"][0], [0, 10.45])
            self.assertEquals(flow_data["pressure"][0]["data"][1], [1, 10.45])

            # temp
            self.assertEquals(temperature_message, None)
            self.assertEquals(flow_data["temperature"][0]["data"][0], [0, 31.14])

    def test_get_pressure_and_temp_proton(self):
        files = {
            "explog_final.txt":
                "ProtonTemperature:29.408384 30.336662\n"
                "ProtonPressure:10.463466 10.490935\n"
                "ExperimentInfoLog:\n"
                "	beadfind_pre_0000.dat: Pressure=10.48 10.63 Temp=29.41 27.79 -13.44 27.39 dac_start_sig=1171 avg=9170 time=12:17:22 fpgaTemp=111.20 107.60 chipTemp=31.28 32.86 33.88 41.47 16.91 a1a2=ffffff 0 0 0 0 cpuTemp=37.00 47.00 heater=0.79 cooler=0.00 gpuTemp=47 diskPerFree=1 FACC_Offset=0.00, FACC=1.79\n"
                "   acq_0000.dat: Pressure=10.48 10.62 Temp=30.21 27.51 -13.44 26.84 dac_start_sig=1728 avg=8578 time=12:24:05 fpgaTemp=111.20 107.60 chipTemp=32.77 34.29 35.44 43.07 18.28 a1a2=ffffff 0 0 0 0 cpuTemp=37.00 50.00 heater=0.62 cooler=0.00 gpuTemp=47 diskPerFree=1 FACC_Offset=0.00, FACC=1.79\n"
                "ExperimentErrorLog:\n"
        }
        with TemporaryDirectory(files) as archive_path:
            pressure_message, temperature_message, level, flow_data = get_pressure_and_temp(archive_path,
                                                                                            "Proton")
            self.assertEquals(level, INFO)

            # pressure
            self.assertEquals(pressure_message, None)
            self.assertEquals(flow_data["pressure"][0]["data"][0], [0, 10.48])
            self.assertEquals(flow_data["pressure"][0]["data"][1], [1, 10.48])

            # temp
            self.assertEquals(temperature_message, None)
            self.assertEquals(flow_data["temperature"][0]["data"][0], [0, 31.28])

    def test_get_pressure_and_temp_s5(self):
        files = {
            "explog_final.txt":
                "PGMPressure:0.309028 7.883653\n"
                "ExperimentInfoLog:\n"
                "beadfind_pre_0000.dat: Pressure=7.88 7.96 Temp=32.93 25.74 30.03 22.84 dac_start_sig=1555 avg=9568 time=08:21:55 fpgaTemp=114.80 107.60 chipTemp=31.54 39.77 49.39 36.52 40.46 a1a2=ffffff 0 0 0 0 cpuTemp=51.00 0.00 heater=0.22 cooler=0.16 gpuTemp=29 diskPerFree=11 FACC_Offset=0.00, FACC=1.27 Pinch=2.26 3.69 ManTemp=109\n"
                "beadfind_pre_0001.dat: Pressure=2.04 2.19 Temp=32.96 26.03 30.02 22.84 dac_start_sig=1496 avg=4776 time=08:22:18 fpgaTemp=114.80 107.60 chipTemp=30.91 39.36 48.88 35.95 39.45 a1a2=ffffff 0 0 0 0 cpuTemp=51.00 0.00 heater=0.21 cooler=0.17 gpuTemp=29 diskPerFree=11 FACC_Offset=0.00, FACC=1.27 Pinch=2.26 3.69 ManTemp=27\n"
                "prerun_0000.dat: Pressure=1.98 2.11 Temp=32.86 26.34 30.01 22.89 dac_start_sig=1572 avg=3718 time=08:23:58 fpgaTemp=114.80 107.60 chipTemp=30.64 32.34 48.54 35.41 39.26 a1a2=ffffff 0 0 0 0 cpuTemp=50.00 0.00 heater=0.24 cooler=0.16 gpuTemp=29 diskPerFree=11 FACC_Offset=0.00, FACC=1.27 Pinch=2.26 3.69 ManTemp=28\n"
                "prerun_0001.dat: Pressure=1.15 1.30 Temp=32.94 26.26 30.00 22.87 dac_start_sig=1514 avg=4793 time=08:24:17 fpgaTemp=114.80 109.40 chipTemp=30.76 32.38 48.56 35.82 39.26 a1a2=ffffff 0 0 0 0 cpuTemp=48.00 0.00 heater=0.21 cooler=0.17 gpuTemp=29 diskPerFree=11 FACC_Offset=0.00, FACC=1.27 Pinch=2.19 3.69 ManTemp=28\n"
                "extraG_0000.dat: Pressure=1.84 1.98 Temp=32.97 26.43 30.00 22.74 dac_start_sig=1636 avg=5701 time=08:26:33 fpgaTemp=116.60 109.40 chipTemp=30.10 32.91 47.67 35.00 38.84 a1a2=ffffff 0 0 0 0 cpuTemp=52.00 0.00 heater=0.21 cooler=0.18 gpuTemp=29 diskPerFree=11 FACC_Offset=0.00, FACC=1.27 Pinch=2.17 3.27 ManTemp=28\n"
                "acq_0000.dat: Pressure=7.88 7.66 Temp=32.99 26.47 30.00 22.73 dac_start_sig=1645 avg=8494 time=08:26:52 fpgaTemp=116.60 109.40 chipTemp=32.92 32.60 47.43 34.99 38.65 a1a2=ffffff 0 0 0 0 cpuTemp=52.00 0.00 heater=0.20 cooler=0.18 gpuTemp=29 diskPerFree=11 FACC_Offset=0.00, FACC=1.27 Pinch=2.17 3.27 ManTemp=28\n"
                "acq_0001.dat: Pressure=7.88 7.66 Temp=32.97 26.50 30.00 22.68 dac_start_sig=1647 avg=8262 time=08:27:09 fpgaTemp=118.40 109.40 chipTemp=32.74 32.32 47.25 35.06 38.32 a1a2=ffffff 0 0 0 0 cpuTemp=52.00 0.00 heater=0.20 cooler=0.18 gpuTemp=29 diskPerFree=11 FACC_Offset=0.00, FACC=1.27 Pinch=2.17 3.26 ManTemp=28\n"
                "ExperimentErrorLog:\n"
        }
        with TemporaryDirectory(files) as archive_path:
            pressure_message, temperature_message, level, flow_data = get_pressure_and_temp(archive_path, "S5")

            # ignore temp and pressure before acq flows
            # manTemp is way to high in flow 0 but this still should be INFO
            self.assertEquals(level, INFO)

            # pressure
            self.assertEquals(pressure_message, None)
            self.assertEquals(flow_data["pressure"][0]["data"][0], [0, 7.88])
            self.assertEquals(flow_data["pressure"][0]["data"][1], [1, 2.04])

            # temp
            self.assertEquals(temperature_message, None)
            self.assertEquals(flow_data["temperature"][0]["data"][0], [0, 25.74])


class PressureAndTemperatureWarnCase(SimpleTestCase):
    def test_get_pressure_and_temp_proton_warn(self):
        files = {
            "explog_final.txt":
                "ProtonTemperature:29.408384 30.336662\n"
                "ProtonPressure:10.463466 10.490935\n"
                "ExperimentInfoLog:\n"
                "	beadfind_pre_0000.dat: Pressure=10.48 10.63 Temp=29.41 27.79 -13.44 27.39 dac_start_sig=1171 avg=9170 time=12:17:22 fpgaTemp=111.20 107.60 chipTemp=31.28 32.86 33.88 41.47 16.91 a1a2=ffffff 0 0 0 0 cpuTemp=37.00 47.00 heater=0.79 cooler=0.00 gpuTemp=47 diskPerFree=1 FACC_Offset=0.00, FACC=1.79\n"
                "   acq_0000.dat: Pressure=10.1 10.62 Temp=30.21 27.51 -13.44 26.84 dac_start_sig=1728 avg=8578 time=12:24:05 fpgaTemp=111.20 107.60 chipTemp=32.77 34.29 35.44 43.07 18.28 a1a2=ffffff 0 0 0 0 cpuTemp=37.00 50.00 heater=0.62 cooler=0.00 gpuTemp=47 diskPerFree=1 FACC_Offset=0.00, FACC=1.79\n"
                "ExperimentErrorLog:\n"
        }
        with TemporaryDirectory(files) as archive_path:
            pressure_message, temperature_message, level, flow_data = get_pressure_and_temp(archive_path,
                                                                                            "Proton")
            self.assertEquals(level, WARN)

            # pressure
            self.assertEquals(pressure_message, "Pressure is low (10.10) at flow 1")
            self.assertEquals(flow_data["pressure"][0]["data"][0], [0, 10.48])
            self.assertEquals(flow_data["pressure"][0]["data"][1], [1, 10.1])

            # temp
            self.assertEquals(temperature_message, None)
            self.assertEquals(flow_data["temperature"][0]["data"][0], [0, 31.28])


class PressureAndTemperatureAlarmCase(SimpleTestCase):
    def test_get_pressure_and_temp_proton_alert_pressure(self):
        files = {
            "explog_final.txt":
                "ProtonTemperature:29.408384 30.336662\n"
                "ProtonPressure:10.463466 10.490935\n"
                "ExperimentInfoLog:\n"
                "	beadfind_pre_0000.dat: Pressure=10.48 10.63 Temp=29.41 27.79 -13.44 27.39 dac_start_sig=1171 avg=9170 time=12:17:22 fpgaTemp=111.20 107.60 chipTemp=31.28 32.86 33.88 41.47 16.91 a1a2=ffffff 0 0 0 0 cpuTemp=37.00 47.00 heater=0.79 cooler=0.00 gpuTemp=47 diskPerFree=1 FACC_Offset=0.00, FACC=1.79\n"
                "   acq_0000.dat: Pressure=9.20 10.62 Temp=30.21 27.51 -13.44 26.84 dac_start_sig=1728 avg=8578 time=12:24:05 fpgaTemp=111.20 107.60 chipTemp=32.77 34.29 35.44 43.07 18.28 a1a2=ffffff 0 0 0 0 cpuTemp=37.00 50.00 heater=0.62 cooler=0.00 gpuTemp=47 diskPerFree=1 FACC_Offset=0.00, FACC=1.79\n"
                "ExperimentErrorLog:\n"
        }
        with TemporaryDirectory(files) as archive_path:
            pressure_message, temperature_message, level, flow_data = get_pressure_and_temp(archive_path,
                                                                                            "Proton")
            self.assertEquals(level, ALARM)

            # pressure
            self.assertEquals(pressure_message, "Pressure is very low (9.20) at flow 1")
            self.assertEquals(flow_data["pressure"][0]["data"][0], [0, 10.48])
            self.assertEquals(flow_data["pressure"][0]["data"][1], [1, 9.20])

            # temp
            self.assertEquals(temperature_message, None)
            self.assertEquals(flow_data["temperature"][0]["data"][0], [0, 31.28])

    def test_get_pressure_and_temp_proton_alert_temp(self):
        files = {
            "explog_final.txt":
                "ProtonTemperature:29.408384 30.336662\n"
                "ProtonPressure:10.463466 10.490935\n"
                "ExperimentInfoLog:\n"
                "	beadfind_pre_0000.dat: Pressure=10.48 10.63 Temp=29.41 27.79 -13.44 27.39 dac_start_sig=1171 avg=9170 time=12:17:22 fpgaTemp=111.20 107.60 chipTemp=26.28 32.86 33.88 41.47 16.91 a1a2=ffffff 0 0 0 0 cpuTemp=37.00 47.00 heater=0.79 cooler=0.00 gpuTemp=47 diskPerFree=1 FACC_Offset=0.00, FACC=1.79\n"
                "   acq_0000.dat: Pressure=10.48 10.62 Temp=18.21 27.51 -13.44 26.84 dac_start_sig=1728 avg=8578 time=12:24:05 fpgaTemp=111.20 107.60 chipTemp=32.77 34.29 35.44 43.07 18.28 a1a2=ffffff 0 0 0 0 cpuTemp=37.00 50.00 heater=0.62 cooler=0.00 gpuTemp=47 diskPerFree=1 FACC_Offset=0.00, FACC=1.79\n"
                "ExperimentErrorLog:\n"
        }
        with TemporaryDirectory(files) as archive_path:
            pressure_message, temperature_message, level, flow_data = get_pressure_and_temp(archive_path,
                                                                                            "Proton")
            self.assertEquals(level, ALARM)

            # pressure
            self.assertEquals(pressure_message, None)
            self.assertEquals(flow_data["pressure"][0]["data"][0], [0, 10.48])
            self.assertEquals(flow_data["pressure"][0]["data"][1], [1, 10.48])

            # temp
            self.assertEquals(temperature_message, "Temperature is cold (18.21) at flow 1")
            self.assertEquals(flow_data["temperature"][0]["data"][0], [0, 26.28])
