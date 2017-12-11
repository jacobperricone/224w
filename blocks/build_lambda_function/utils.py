# -*- coding: utf-8 -*-
import datetime as dt
import os
import zipfile
import subprocess

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def read(path, loader=None):
    with open(path) as fh:
        if not loader:
            return fh.read()
        return loader(fh.read())


def archive(src, dest, filename):
    print os.getcwd()
    print os.listdir(src)
    output = os.path.join(dest, filename)
    bash_command = 'sudo zip  {} -r -9 {}'.format(output, src)
    print "bash_command {}".format(bash_command)
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output_process, error = process.communicate()
    print error
    return output


def timestamp(fmt='%Y-%m-%d-%H%M%S'):
    now = dt.datetime.utcnow()
    return now.strftime(fmt)



