
import subprocess
import time
from multiprocessing import Process
import os
import re
import matplotlib.pylab as plt
import pandas as pd
import seaborn as sns
from glob import glob
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
    # string = f"docker run --name {container_name} -e \"my_env_var={env_var}\" {imageName}"
    # os.system(string)
    string = f"docker run --name {container_name} -e \"my_env_var={env_var}\" {image_name}"
    os.system(string)
    # os.system(f"docker run {imageName}")


def CollectTestData1(image_name, container_name, test_name):

    t1 = Process(target=runContainer, args=(image_name, test_name, container_name))
    t1.start()
    t2 = Process(target=CollectEvery1Second, args=(container_name,))
    t2.start()
    t1.join()
    t2.terminate()

def GetDataFrame(path):
    df = pd.read_csv(os.path.join(ROOT_PATH, f"Formatted\\{path}.csv"),on_bad_lines="skip", sep=r"\s\s+", engine="python")  # todo fix path
    df = df[df.NAME != "NAME"] #remove repeating header
    df = df[df.NAME != "0.00%"] #remove first error


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


def deleteFirstLastLine(param):

    lines = []
    # f = open(f"{os.getcwd()}\\data\\{param}.csv", "r+")
    with  open(f"{os.getcwd()}\\data\\{param}.csv", "r+") as fp:
        # read an store all lines into list
        lines = fp.readlines()
        # move file pointer to the beginning of a file
        fp.seek(0)
        # truncate the file
        fp.truncate()

        # start writing lines except the last line
        # lines[:-1] from line 0 to the second last line
        fp.writelines(lines[:-2])
def runTests(image_name,  test_name, iterations,):
    for i in range(iterations):
        container_name=f"{test_name}{i}"
        # string = f"docker run --name {container_name} -e \"my_env_var={test_name}\" {image_name}"
        # path=f"TestSlow8PeerPoW{i}"
        # image_name= f"{image_name}{i}"

        # dataSetPaths.append(path)
        print(container_name)
        CollectTestData1(image_name, container_name, test_name)
        # deleteFirstLastLine(path)
def gb(x, pos):
    'The two args are the value and tick position'
    return '%1.1fGB' % (x * 1.25*1e-10)
# def y_fmt(x, y):
#     return '{:2.2e}'.format(x).replace('e', 'x10^')

# def procent(x, pos):
#     'The two args are the value and tick position'
#     return '%1.1fprocent' % (x )
import matplotlib.ticker as mtick
from matplotlib.ticker import FuncFormatter
import matplotlib.ticker as ticker
def createPlots(dataSetPaths):
    # dataSetPaths = ['formattedPos0', 'formattedPos1', 'formattedPos2']
    figure, axis = plt.subplots(3, 1, figsize=(20, 15))
    for i in dataSetPaths:
        data = GetDataFrame(i)
        # formatterProcent = FuncFormatter(procent)
        axis[0].plot(data.index / 2, "mem_percentage", data=data, drawstyle="steps", linewidth='4.5')
        # axis[0].yaxis.set_major_formatter(ticker.PercentFormatter(xmax=5))
        axis[0].yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))
        axis[0].set_title("Mermory %", fontdict={'fontsize': '22', 'weight': '1000'})
        axis[0].set_xlabel('time [s]', fontdict={'fontsize': '22', 'weight': '1000'})
        axis[0].set_ylabel("Memory", fontdict={'fontsize': '22', 'weight': '1000'})
        # axis[0].grid()

        # For Cosine Function
        formatterGB = FuncFormatter(gb)
        axis[1].plot(data.index / 2, "mem_usage", data=data, drawstyle="steps", linewidth='4.5')
        axis[1].yaxis.set_major_formatter(formatterGB)
        axis[1].set_title("Memory Usage", fontdict={'fontsize': '22', 'weight': '1000'})
        axis[1].set_xlabel('time [s]', fontdict={'fontsize': '22', 'weight': '1000'})
        axis[1].set_ylabel("Memory", fontdict={'fontsize': '22', 'weight': '1000'})
        # axis[1].grid()

        axis[2].plot(data.index / 2, "cpu_percentage", data=data, drawstyle="steps", linewidth='4.5')
        axis[2].yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))
        axis[2].set_title("CPU %", fontdict={'fontsize': '22', 'weight': '1000'})
        axis[2].set_xlabel('time [s]', fontdict={'fontsize': '22', 'weight': '1000'})
        axis[2].set_ylabel("CPU", fontdict={'fontsize': '22', 'weight': '1000'})

    axis[0].grid(axis='x')
    axis[1].grid(axis='x')
    axis[2].grid(axis='x')

    axis[0].tick_params(axis='both',which='major', labelsize=24)
    axis[1].tick_params(axis='both', which='major', labelsize=24)
    axis[2].tick_params(axis='both', which='major', labelsize=24)
    # axis[0].set_ylim([0.2,0.4])
    #
    # axis[1].set_ylim([6.5e8, 8.5e8])
    # axis[2].set_ylim([0, 270])
    plt.subplots_adjust(hspace=1)
    plt.tight_layout(pad=5.0)

    plt.show()
def buildImage(imageName):
    # imageName = "performance"
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
    dataSetPaths1 =['TestSlow8PeerPoSFixedGraph0','TestSlow8PeerPoSFixedGraph1','TestSlow8PeerPoSFixedGraph2']
    dataSetPaths2 =[ 'TestBiggerSlow8PeerPoS0','TestBiggerSlow8PeerPoS1','TestBiggerSlow8PeerPoS2']
    dataSetPaths3 =[ 'TestSlow4PeerPoS0','TestSlow4PeerPoS1','TestSlow4PeerPoS2']
    dataSetPaths4 =[ 'TestSlow8PeerPoS0','TestSlow8PeerPoS1','TestSlow8PeerPoS2']
    dataSetPaths5 =[ 'TestSlow8PeerPoW0','TestSlow8PeerPoW1','TestSlow8PeerPoW2']
    createPlots(dataSetPaths1)
    # createPlots(dataSetPaths2)
    # createPlots(dataSetPaths3)
    # createPlots(dataSetPaths4)
    # createPlots(dataSetPaths5)
# ---------------------- For generating plots uncomment above

    # ----------------------------
    # TestSlow8PeerPoW
    # TestSlow8PeerPoS
    # TestFast8PeerPoW
    # TestFast8PeerPoS
    # TestSlow4PeerPoS
    # TestBiggerSlow8PeerPoS
    # TestSinglePeerPoS
    #
    # TestSlow8PeerPoSFixedGraph

    # imageName = "performance_testing"
    # # mageName = "performance_testing"
    # tests = ['TestSlow8PeerPoSFixedGraph', 'TestBiggerSlow8PeerPoS', 'TestSlow4PeerPoS', 'TestSlow8PeerPoS',
    #          'TestSlow8PeerPoW']
    # buildImage(imageName)
    # string = f"docker run --name {tests[1]} -e \"my_env_var=TestSlow8PeerPoSFixedGraph\" {imageName}"
    # os.system(string)
















    # container_name="hejhej"
    # env_var="TestSlow8PeerPoS"
    # string = f"docker run --name {env_var} -e \"my_env_var={env_var}\" {imageName}"
    # os.system(string)


    # runTests()










    # dataSetPaths=[] #"test0","test1","test2","test3","test4","test5"
    # dataSetPaths=["test0","test1","test2","test3","test4","test5"] #"test0","test1","test2","test3","test4","test5"
    # dataSetPaths = ['formattedPos0','formattedPos1','formattedPos2']
    # dataSetPaths = ['TestSlow8PeerPoW0Formatted', 'TestSlow8PeerPoW1Formatted', 'TestSlow8PeerPoW2Formatted']


    # deleteFirstLastLine("test0")
    # fig, ax = plt.subplots(figsize=(5, 5))
    # fig1, ax2 = plt.subplots(figsize=(5, 5))
    # deleteFirstLastLine(dataSetPaths[0])
    # deleteFirstLastLine(dataSetPaths[1])
    # deleteFirstLastLine(dataSetPaths[2])
    # deleteFirstLastLine(dataSetPaths[3])
    # deleteFirstLastLine(dataSetPaths[4])
    # deleteFirstLastLine(dataSetPaths[5])

    ###--------------------------------------------------------- usefull under
    # figure, axis = plt.subplots(3, 1, figsize=(20,15))
    # for i in dataSetPaths:
    #     data=GetDataFrame(i)
    #     axis[0].plot(data.index/2, "mem_percentage", data=data, drawstyle="steps",linewidth = '4.5')
    #     axis[0].set_title("Mermory %",fontdict={'fontsize': '22', 'weight': '1000'})
    #     axis[0].set_xlabel('time [s]',fontdict={'fontsize': '22', 'weight': '1000'})
    #     axis[0].set_ylabel("memory %",fontdict={'fontsize': '22', 'weight': '1000'})
    #     # axis[0].grid()
    #
    #     # For Cosine Function
    #     axis[1].plot(data.index / 2, "mem_usage", data=data, drawstyle="steps",linewidth = '4.5')
    #     axis[1].set_title("Memory Usage",fontdict={'fontsize': '22', 'weight': '1000'})
    #     axis[1].set_xlabel('time [s]',fontdict={'fontsize': '22', 'weight': '1000'})
    #     axis[1].set_ylabel("memory bit",fontdict={'fontsize': '22', 'weight': '1000'})
    #     # axis[1].grid()
    #
    #     axis[2].plot(data.index / 2, "cpu_percentage", data=data, drawstyle="steps",linewidth = '4.5')
    #     axis[2].set_title("CPU %",  fontdict={'fontsize': '22', 'weight': '1000'} )
    #     axis[2].set_xlabel('time [s]',fontdict={'fontsize': '22', 'weight': '1000'})
    #     axis[2].set_ylabel("cpu %",fontdict={'fontsize': '22', 'weight': '1000'})
    #
    #
    #
    # axis[0].grid(axis ='x')
    # axis[1].grid(axis ='x')
    # axis[2].grid(axis ='x')
    #
    #
    # # axis[0].set_ylim([0.2,0.4])
    # #
    # # axis[1].set_ylim([6.5e8, 8.5e8])
    # # axis[2].set_ylim([0, 270])
    #
    # plt.subplots_adjust(hspace=1)
    # plt.tight_layout(pad=5.0)
    #
    # plt.show()


