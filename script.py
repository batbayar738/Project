import tarfile
import glob
import sys
import fnmatch
import subprocess
import os, os.path
import json
from urllib import request
import zipfile
from pkg_resources import parse_version
import csv
from csv import DictWriter
from urllib.request import urlopen

cwd = os.path.dirname(__file__)
INPUT_FILE = os.path.join(cwd, "input.txt")
ERROR_FILE = os.path.join(cwd, "error.txt")


def versions(pkg_name):
    url = f"https://pypi.python.org/pypi/{pkg_name}/json"
    releases = json.loads(request.urlopen(url).read())["releases"]
    return sorted(releases, key=parse_version, reverse=True)


def file_len(fname):
    i = 0
    with open(fname, "r") as f:
        for line in f:
            i += 1
    # print(fname)
    # print(i)
    return i


def get_extensions(path, excl):
    extensions = []
    for root, dir, files in os.walk(path):
        for items in fnmatch.filter(files, "*.py"):
            temp_extensions = items.rfind(".")
            ext = items[temp_extensions + 1 :]

            # If the file is not in the exclude list, add it into the array
            if ext not in extensions:
                if ext not in excl:
                    extensions.append(ext)
                    pass
    return extensions


def count_per_ext(path, extension):
    temp = 0
    for root, dir, files in os.walk(path):
        for items in fnmatch.filter(files, extension):
            value = root + "/" + items
            temp += file_len(value)
    return temp


# creating csv file
header = ["pkg_name", "pkg_version", "own_size", "dep_size", "tech_leverage"]
with open("tech.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    f.close()


def compute_duration(pkg_name, pkg_version):

    package_name = pkg_name + "==" + pkg_version

    def install(package):
        try:
            # with open(ERROR_FILE, "a") as f_out:
            subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "download",
                    package,
                    "--no-cache-dir",
                    "--disable-pip-version-check",
                    "--no-binary",
                    ":all:",
                    "-d",
                    DOWNLOAD_FOLDER,
                ],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            print(e.output)
            raise e

        for d in glob.glob(DOWNLOAD_FOLDER + "/*.tar.gz"):
            with tarfile.open(d) as tar:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, path=APP_FOLDER)
        # in case of executing for python-dateutil and setuptools packages
        # for d in glob.glob(DOWNLOAD_FOLDER + '/*.zip'):
        #   with zipfile.ZipFile(d, 'r') as zip_ref:
        #      zip_ref.extractall(path=APP_FOLDER)
        # for d in glob.glob(DOWNLOAD_FOLDER + '/*.tar.bz2'):
        #   with tarfile.open(d, "r:bz2") as tarbz2:
        #      tarbz2.extractall(path=APP_FOLDER)

    parentdir = os.path.join(cwd, "downloadedpackages")
    subdir = package_name

    DOWNLOAD_FOLDER = os.path.join(parentdir, subdir)

    parentdir_ext = os.path.join(cwd, "extractedpackages")
    APP_FOLDER = os.path.join(parentdir_ext, subdir)

    try:
        install(package_name)  # install packages
    except Exception as e1:
        raise e1

    extensions = []
    code_count = []
    exclude = []

    extensions = get_extensions(APP_FOLDER, exclude)

    value_dict = dict()
    newDict = dict()
    for run in extensions:
        dirs = next(os.walk(APP_FOLDER))[
            1
        ]  # returns all the dirs in 'C:\dir1\dir2\startdir'
        for dir in dirs:
            if not dir in value_dict:
                p = os.path.join(APP_FOLDER, dir)  # ./extractedpackages/requests-2.24.0
                temp = count_per_ext(p, "*" + run)
                value_dict[dir] = temp
                code_count.append(temp)
        pass

    print("\n")
    print(
        "\tDemo 1",
    )
    print("\t---------------------------")
    print("")
    print("\tPackages \t\t\tLoCs")
    print("\t--------- \t\t\t----------")

    matchfiles = []
    matchfiles.append(pkg_name + "-" + pkg_version)

    # newDict
    for k, v in value_dict.items():
        if k in matchfiles:
            newDict[k] = v
        pass

    for x, y in newDict.items():
        if len(x) > 10:
            t = "\t\t"
        elif len(x) > 7:
            t = "\t\t\t"
        else:
            t = "\t\t\t\t"
        print("\t" + x + ": " + t + str(y))
        pass

    dependencies_size = sum(value_dict.values()) - sum(newDict.values())
    technical_leverage = dependencies_size / sum(newDict.values())

    print("\t" + "Dependencies size" + ":" + "\t\t" + str(dependencies_size))
    print("\t" + "Technical leverage" + ":" + "\t\t" + str(technical_leverage))

    # appending csv file
    header = ["pkg_name", "pkg_version", "own_size", "dep_size", "tech_leverage"]
    datadict = {
        "pkg_name": pkg_name,
        "pkg_version": pkg_version,
        "own_size": sum(newDict.values()),
        "dep_size": dependencies_size,
        "tech_leverage": technical_leverage,
    }

    with open("tech.csv", "a") as f:
        dictwriter_object = DictWriter(f, fieldnames=header)
        dictwriter_object.writerow(datadict)
        f.close


# pkgs = [
#     # ("botocore", versions("botocore")),
#     # ("urllib3", versions("urllib3")),
#     # ("boto3", versions("boto3")),
#     # ("s3transfer", versions("s3transfer")),
#     # ("six", versions("six")),
#     # ("python-dateutil", versions("python-dateutil")),
#     # ("jmespath", versions("jmespath")),
#     # ("setuptools", versions("setuptools")),
#     # ("awscli", versions("awscli")),
#     ("requests", versions("requests")),
# ]

try:
    with open(INPUT_FILE, "r") as f:
        for line in f:
            if line.startswith("#"):
                continue

            pkg_rootname = line.strip()
            version_list = versions(pkg_rootname)

            for vers in version_list:
                try:
                    stats = compute_duration(pkg_rootname, vers)
                except Exception as e:
                    # TODO: capture the error e, the package+version and log it
                    with open(ERROR_FILE, "a") as f_out:
                        if isinstance(e, subprocess.CalledProcessError):
                            f_out.write(
                                "{}=={}\n {}\n".format(pkg_rootname, vers, e.output)
                            )
except OSError as e:
    print("I cannot open file with input list of packages: {}".format(e))
