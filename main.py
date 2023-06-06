import subprocess
import time
from multiprocessing import Process
import os
import re
import matplotlib.pylab as plt
import pandas as pd
import matplotlib.ticker as mtick
from matplotlib.ticker import FuncFormatter
import numpy as np 

ROOT_PATH = os.getcwd()


def CollectEvery1Second(TestName):
    f = open(f"{os.getcwd()}\\data\\{TestName}.csv", "w")
    while True:
        localtime = time.localtime()
        result = time.strftime("%I:%M:%S %p", localtime)
        subprocess.Popen('docker stats --no-stream', stdout=f)
        print(result)
        time.sleep(1)


def runContainer(image_name, env_var, container_name):
    string = f"docker run --name {container_name} -e \"my_env_var={env_var}\" {image_name}"
    os.system(string)


def CollectTestData1(image_name, container_name, test_name):
    t1 = Process(target=runContainer, args=(image_name, test_name, container_name))
    t1.start()
    t2 = Process(target=CollectEvery1Second, args=(container_name,))
    t2.start()
    t1.join()
    t2.terminate()


def GetDataFrame(path):
    df = pd.read_csv(os.path.join(ROOT_PATH, f"Formatted\\{path}.csv"), on_bad_lines="skip", sep=r"\s\s+",
                     engine="python")  # todo fix path
    df = df[df.NAME != "NAME"]  # remove repeating header
    df = df[df.NAME != "0.00%"]  # remove first error

    # Parse the data
    def percentage_to_float(df_col):
        return df_col.apply(lambda x: float(x[0:-1]))

    def split_on_slash(df_col, split_index):
        return df_col.apply(lambda x: x.split(" / ")[split_index])

    def get_only_characters(string):
        return re.sub('[^a-zA-Z]+', '', string)

    def get_only_numbers(string):
        return float(re.sub('[^\d\.]', '', string))

    def to_bit(value):
        return int({
                       "b": get_only_numbers(value) * 1,
                       "kib": get_only_numbers(value) * 10e3,
                       "kb": get_only_numbers(value) * 10e3,
                       "mib": get_only_numbers(value) * 10e6,
                       "mb": get_only_numbers(value) * 10e6,
                       "gib": get_only_numbers(value) * 10e9,
                       "gb": get_only_numbers(value) * 10e9,
                   }.get(get_only_characters(value).lower(), 0))

    df["mem_usage"] = split_on_slash(df["MEM USAGE / LIMIT"], 0).apply(to_bit)
    df["mem_limit"] = split_on_slash(df["MEM USAGE / LIMIT"], 1).apply(to_bit)
    df["mem_percentage"] = percentage_to_float(df["MEM %"])
    df["cpu_percentage"] = percentage_to_float(df["CPU %"])
    df["PIDS"] = df["PIDS"].apply(int)
    df["net_in"] = split_on_slash(df["NET I/O"], 0).apply(to_bit)
    df["net_out"] = split_on_slash(df["NET I/O"], 1).apply(to_bit)
    df["block_in"] = split_on_slash(df["BLOCK I/O"], 0).apply(to_bit)
    df["block_out"] = split_on_slash(df["BLOCK I/O"], 1).apply(to_bit)
    return df


def runTests(image_name, test_name, iterations, ):
    for i in range(iterations):
        container_name = f"{test_name}{i}"
        print(container_name)
        CollectTestData1(image_name, container_name, test_name)


def gb(x, pos):
    'The two args are the value and tick position'
    return '%1.1fGB' % (x * 1.25 * 1e-10)


def createPlots(dataSetPaths):
    figure, axis = plt.subplots(2, 1, figsize=(20, 15))
    for i in dataSetPaths:
        data = GetDataFrame(i)

        # For Cosine Function
        formatterGB = FuncFormatter(gb)

        axis[0].plot(data.index / 2, "mem_usage", data=data, drawstyle="steps", linewidth='4.5', label=f"{i}")
        axis[0].yaxis.set_major_formatter(formatterGB)
        axis[0].set_title("Memory Usage", fontdict={'fontsize': '22', 'weight': '1000'})
        axis[0].set_xlabel('time [s]', fontdict={'fontsize': '22', 'weight': '1000'})
        axis[0].set_ylabel("Memory", fontdict={'fontsize': '22', 'weight': '1000'})
        axis[0].legend(loc="lower right", prop = { "size": 20 })
        axis[0].set_ylim([0,0.2* 1.25 * 1e10])
        # axis[0].set_ylim([0,20* 1.25 * 1e10])
        
        # axis[0].set_ylim([0,20* 0.8 * 1e10])
        # axis[0].set_yticks(tuple(i * 0.8 * 1e10 for i in range(0, 21, 5)))
        
        axis[0].set_yticks((0, 0.08*1e10, 0.16*1e10, 0.24*1e10))

        axis[1].set_ylim([0,1000])
        axis[1].set_xlim([0,800])
        axis[1].set_yticks([0, 200, 400, 600, 800, 1000])
        # axis[1].set_yticks([i * 100 for i in range(11)])
        axis[1].plot(data.index / 2, "cpu_percentage", data=data, drawstyle="steps", linewidth='4.5', label=f"{i}")
        axis[1].yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))
        axis[1].set_title("CPU %", fontdict={'fontsize': '22', 'weight': '1000'})
        axis[1].set_xlabel('time [s]', fontdict={'fontsize': '22', 'weight': '1000'})
        axis[1].set_ylabel("CPU", fontdict={'fontsize': '22', 'weight': '1000'})
        axis[1].legend(loc="upper right", prop = { "size": 20 })

    axis[0].grid(axis='x')
    axis[0].grid(axis='y')
    axis[1].grid(axis='x')
    axis[1].grid(axis='y')

    axis[0].tick_params(axis='both', which='major', labelsize=24)
    axis[1].tick_params(axis='both', which='major', labelsize=24)

    plt.subplots_adjust(hspace=1)
    plt.tight_layout(pad=5.0)
    # plt.xticks(np.arange(min(x), max(x) + 1, 2))
    # plt.yticks(np.arange(0, 2500000000000, 4))
    plt.show()


def buildImage(imageName):
    os.system(f'docker build -t {imageName} C:\\Users\\Oskar\\GolandProjects\\BachelorProject')


if __name__ == '__main__':
    # ---------------------- For generating data uncomment below
    # imageName = "performance_testing"
    # tests=['TestSlow8PeerPoSFixedGraph','TestBiggerSlow8PeerPoS','TestSlow4PeerPoS','TestSlow8PeerPoS','TestSlow8PeerPoW']
    # buildImage(imageName)
    # for i in range(len(tests)):
    #     print(tests[i])
    #     runTests(imageName, tests[i], 3)
    # ---------------------- For generating data uncomment above

    # ---------------------- For generating plots uncomment below
    dataSetPaths1 = ['TestSlow8PeerPoSFixedGraph0', 'TestSlow8PeerPoSFixedGraph1', 'TestSlow8PeerPoSFixedGraph2']
    dataSetPaths2 = ['TestBiggerSlow8PeerPoS0', 'TestBiggerSlow8PeerPoS1', 'TestBiggerSlow8PeerPoS2']
    dataSetPaths3 = ['TestSlow4PeerPoS0', 'TestSlow4PeerPoS1', 'TestSlow4PeerPoS2']
    dataSetPaths4 = ['TestSlow8PeerPoS0', 'TestSlow8PeerPoS1', 'TestSlow8PeerPoS2']
    dataSetPaths5 = ['TestSlow8PeerPoW0', 'TestSlow8PeerPoW1', 'TestSlow8PeerPoW2']
    # createPlots(dataSetPaths1)
    # createPlots(dataSetPaths2)
    # createPlots(dataSetPaths3)
    # createPlots(dataSetPaths4)
    createPlots(dataSetPaths5)
# ---------------------- For generating plots uncomment above
