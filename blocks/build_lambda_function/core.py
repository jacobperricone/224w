import os
from shutil import copyfile, copytree, rmtree
from tempfile import mkdtemp
import pip
import yaml

from data_utils import archive
from data_utils import mkdir
from data_utils import read
from data_utils import timestamp

import contextlib


@contextlib.contextmanager
def make_temp_directory(prefix = ''):
    temp_dir = mkdtemp(prefix)
    try:
        yield temp_dir
    finally:
        rmtree(temp_dir)


def main(src,local_package=None):
    """
    @Block 
    :desc: This block bundles a lambda_func into a zipfile for deployment on aws. It installs all of the requirements listed within the requirements.txt file of the directory, and uploads them to a directory called dist within the lambda function 

    :param src: the path to the lambda function
    :type src: string
    :example src: build_lambda_function

    :param local_package: A boolean indicating whether or not to install the local package 
    :type local_package: boolean
    :example local_package: True

    :return: Path to zip file created
    """
    
    # Load and parse the config file.
    if 'ec2-user' or 'Users' not in src:
        src = os.path.join(os.getcwd(), src)


    path_to_config_file = os.path.join(src, 'config.yaml')
    cfg = read(path_to_config_file, loader=yaml.load)

    # Get the absolute path to the output directory and create it if it doesn't
    # already exist.
    dist_directory = cfg.get('dist_directory', 'dist')
    path_to_dist = os.path.join(src, dist_directory)
    mkdir(path_to_dist)

    # Combine the name of the Lambda function with the current timestamp to use
    # for the output filename.



    function_name = cfg.get('function_name')
    output_filename = '{0}-{1}.zip'.format(timestamp(), function_name)
 
    with make_temp_directory(prefix="aws-lambda") as path_to_temp:
        print "PATH TO TEMP {}".format(path_to_temp)
        pip_install_to_target(path_to_temp,src,
                              local_package=local_package)

        # Hack for Zope.
        if 'zope' in os.listdir(path_to_temp):
            print('Zope packages detected; fixing Zope package paths to '
                  'make them importable.')
            # Touch.
            with open(os.path.join(path_to_temp, 'zope/__init__.py'), 'wb'):
                pass

        # Gracefully handle whether ".zip" was included in the filename or not.
        output_filename = ('{0}.zip'.format(output_filename)
                           if not output_filename.endswith('.zip')
                           else output_filename)

        files = []
        dirs = []
        print dist_directory
        print "CURRENT DIRECTORY {}".format(os.getcwd())

        for filename in os.listdir(src):
            if os.path.isdir(filename):
                #print "This is a directory {}".format(filename)
                if filename == dist_directory:
                    continue
                dirs.append(os.path.join(src, filename))
            else:
                if filename == '.DS_Store':
                    continue
                if filename == 'config.yaml':
                    continue
                if 'dist' in filename:
                    continue
                if '.pyc' in filename:
                    continue
                #print "This is a file {}".format(filename)
                files.append(os.path.join(src, filename))

        # "cd" into `temp_path` directory.
        print "PATH TO TEMP {}".format(path_to_temp)

        for f in files:
            print "FILE IN THIS DIRECTORY {}".format(f)
            print "PATH TO TEMP {}".format(path_to_temp)
            print "CURRENT DIRECTORY {}".format(os.getcwd())
            print "LIST DIRECTORY {}".format(os.listdir(src))
           # print "This is the file we are copying {}".format(f)
            _, filename = os.path.split(f)
            #print "THis is the path to the temp directory {}".format(path_to_temp)
           # print "This is the filename we are saving it as {}".format(filename)
            # Copy handler file into root of the packages folder.
            print os.path.join(path_to_temp, filename)

            copyfile(f, os.path.join(path_to_temp, filename))

        for d in dirs:
            print "This is the directory we are interested in {}".format(d)
            _, dirname = os.path.split(d)
            print "This is the name we are copying too {}".format(dirname)
            copytree(d, os.path.join(path_to_temp,dirname))


        # Zip them together into a single file.
        # TODO: Delete temp directory created once the archive has been compiled.
        os.chdir(path_to_temp)
        print "CURRENT DIRECTORY {}".format(os.getcwd())
        path_to_zip_file = archive('./', path_to_dist, output_filename)
        os.chdir(src)
        os.chdir('../..')
        print "CURRENT DIRECTORY {}".format(os.getcwd())
    return path_to_zip_file


def _install_packages(path, packages):
    """Install all packages listed to the target directory.

    Ignores any package that includes Python itself and python-lambda as well
    since its only needed for deploying and not running the code

    :param str path:
        Path to copy installed pip packages to.
    :param list packages:
        A list of packages to be installed via pip.
    """
    def _filter_blacklist(package):
        blacklist = ['-i', '#', 'Python==', 'python-lambda==']
        return all(package.startswith(entry) is False for entry in blacklist)
    filtered_packages = filter(_filter_blacklist, packages)
    for package in filtered_packages:
        if package.startswith('-e '):
            package = package.replace('-e ', '')

        print('Installing {package}'.format(package=package))
        pip.main(['install', package, '-t', path, '--ignore-installed'])


def pip_install_to_target(path, src,  local_package=None):
    """For a given active virtualenv, gather all installed pip packages then
    copy (re-install) them to the path provided.

    :param str path:
        Path to copy installed pip packages to.
    :param bool requirements:
        If set, only the packages in the req.txt file are installed.
        The req.txt file needs to be in the same directory as the
        project which shall be deployed.
        Defaults to false and installs all pacakges found via pip freeze if
        not set.
    :param str local_package:
        The path to a local package with should be included in the deploy as
        well (and/or is not available on PyPi)
    """
    packages = []
    print path
    os.listdir(path)
    os.listdir(src)
    if os.path.exists(os.path.join(src,'requirements.txt')):
        print('Gathering requirement packages')
        data = read(os.path.join(src,'requirements.txt'))
        packages.extend(data.splitlines())
    else:
        print('Please Specify A Requirements.txt file')

    if not packages:
        print('No dependency packages installed!')

    if local_package is not None:
        if not isinstance(local_package, (list, tuple)):
            local_package = [local_package]
        for l_package in local_package:
            packages.append(l_package)
    _install_packages(path, packages)

