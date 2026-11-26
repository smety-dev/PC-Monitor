
import psutil
from version import __version__
import subprocess

def get_gpu_usage():
    command = r"""
    (Get-Counter '\GPU Engine(*engtype_3D)\Utilization Percentage').CounterSamples |
    Group-Object { $_.InstanceName -replace '^pid_\d+_', '' } |
    ForEach-Object {
        ($_.Group | Measure-Object -Property CookedValue -Sum).Sum
    } |
    Measure-Object -Maximum |
    Select-Object -ExpandProperty Maximum
    """

    try:
        result = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", command],
            text=True
        )

        return round(float(result.strip().replace(",", ".")), 1)

    except (ValueError, subprocess.CalledProcessError):
        return None


while True:
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    gpu = get_gpu_usage()

    subprocess.run("cls", shell=True)

    print("PC Monitor")
    print(f"Verze {__version__} (legacy CLI)")
    print("-------------------")

    print("Vytizeni CPU:", cpu, "%")
    print("Vytizeni RAM:", ram.percent, "%")
    print("Volna RAM:", round(ram.available / 1024**3, 2), "GB")
    print("Pocet logickych jader:", psutil.cpu_count())

    if gpu is not None:
        print("Vytizeni GPU 3D:", gpu, "%")
    else:
        print("GPU: Data nedostupna")
