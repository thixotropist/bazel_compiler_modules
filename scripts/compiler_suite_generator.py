#!/usr/bin/python
"""
Generate a Bazel Module from a compiler suite installation directory.

The overall procedure is something like

* configure, build, and install binutils with an appropriate target
* configure, build, and install gcc with the same target
* configure, build, and install glibc with the same target
* edit the version-dependent generator script to select files for inclusion in the module
* execute that generator script to:
    * remove previously imported files from the module source directory
    * rsync selected files into the module source directory
    * strip executables to reduce the size of the module
    * use rdfind to change duplicates into hard links
    * use tar to create a compressed module file in the module tarball directory
    * use openssl to generate a base64 digest of that tarball
* edit the base64 digest into the module file

"""
import sys
import os
import subprocess
import tempfile
import shutil
import logging
logging.basicConfig(level=logging.INFO)
logger = logging

class Generator():
    """
    Convert a compiler suite installation directory into a Bazel module,
    then publish the module in a local file system
    """
    # the directory used as a local module repository
    BZLMOD_DIR = '/opt/bazel/bzlmod'
    # tarballs go here
    TARBALL_DIR = f'{BZLMOD_DIR}/tarballs'
    # source directory for the tarball, to contain
    # the toolsuite, dependencies, and the bazel BUILD files
    MOD_SRC_BASE_DIR = f'{BZLMOD_DIR}/src'
    # packaged modules go here
    MOD_DIR = f'{BZLMOD_DIR}/modules'

    def __init__(self, module_name, mod_version, build_target):
        """
        module_name will be something like 'gcc_riscv_suite'.
        module_version will be something like '15.0.0.x', with the gcc suite version
        number suffixed ith the module patch number
        build_target will be something like 'riscv64-unknown-linux-gnu'
        """
        self.mod_name = module_name
        self.mod_version = mod_version
        self.mod_src_dir = f'{self.MOD_SRC_BASE_DIR}/{module_name}/{mod_version}'
        self.build_target = build_target
        self.digest = ''
        result = subprocess.run(['mkdir', '-p', self.mod_src_dir],
                check=True, capture_output=True, encoding='utf8')
        if result.returncode != 0:
            logger.error('unable to create module source directory: ' + result.stderr)
            sys.exit()

    def set_target_prefix(self, prefix):
        self.target_prefix = prefix

    def clean_mod_src(self):
        """
        Remove all previously imported binary and bazel files
        """
        for sub in ('bin', 'lib', 'include', 'usr', 'lib64', 'libexec', self.build_target):
            target_dir = f'{self.MOD_SRC_BASE_DIR}/{self.mod_name}/{self.mod_version}/{sub}'
            logger.info('Cleaning ' + target_dir)
            result = subprocess.run(['rm', '-rf', target_dir],
                check=True, capture_output=True, encoding='utf8')
            if result.returncode != 0:
                logger.error('removal of existing files failed: ' + result.stderr)
                sys.exit()
            logger.info('cleaned ' + sub)
        for f in ('BUILD', 'MODULE.bazel'):
            result = subprocess.run(['rm', '-rf', f],
                check=True, capture_output=True, encoding='utf8')
            if result.returncode != 0:
                logger.error('removal of existing file failed: ' + result.stderr)
                sys.exit()

    def rsync_to_mod_src(self, src_dir, rsync_data):
        """
        Add selected files to the module
        -ravH --include-from=files --delete src_dir/ mod_src_dir/
        """
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf8', delete_on_close=False) as fp:
            fp.write(rsync_data)
            fp.close()
            logger.info('tempfile name = ' + fp.name)
            result = subprocess.run(['rsync', '-ravH', '--include-from=' + fp.name,
                                     f'{src_dir}/',
                                     f'{self.mod_src_dir}/'],
                    check=True, capture_output=True, encoding='utf8')
            print(result.stdout)
            if result.returncode != 0:
                logger.error('rsync import failed: ' + result.stderr)
                sys.exit()
            logger.info('selectively imported ' + src_dir + ' into ' + self.mod_src_dir)


    def copy_bazel_files(self):
        """
        copy two bazel files into the tarball directory
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = f"{script_dir}/../src/{self.mod_name}/{self.mod_version}"
        shutil.copy(src_dir + "/BUILD", self.mod_src_dir + "/BUILD")
        shutil.copy(src_dir + "/MODULE.bazel", self.mod_src_dir + "/MODULE.bazel")

    def remove_duplicates(self):
        """
        Find duplicates and replace with hard links
        """
        result = subprocess.run(['rdfind', '-makehardlinks', 'true', '-makeresultsfile', 'false', self.mod_src_dir],
                    check=True, capture_output=True, encoding='utf8')
        if result.returncode != 0:
            logger.error('duplicate removal failed: ' + result.stderr)
            sys.exit()
        logger.info('removed duplicates from ' + self.mod_src_dir)

    def strip_binaries(self, strip_data):
        """
        Strip all host binaries for minimal size, using the host computer's strip
        """
        for file in strip_data.splitlines():
            if not file or not file.strip():
                continue
            result = subprocess.run(['strip', f'{self.mod_src_dir}/{file}'],
                    check=False, capture_output=True, encoding='utf8')
            if result.returncode != 0:
                logger.error('host binary stripping failed: ' + result.stderr)
                sys.exit()
            logger.info('stripped binary ' + file)

    def strip_target_binaries(self, strip_data):
        """
        Strip all target binaries for minimal size, using the target's strip
        """
        for file in strip_data.splitlines():
            if not file or not file.strip():
                continue
            result = subprocess.run([self.target_prefix +'strip', f'{self.mod_src_dir}/{file}'],
                    check=False, capture_output=True, encoding='utf8')
            if result.returncode != 0:
                logger.error('target binary stripping failed: ' + result.stderr)
                sys.exit()
            logger.info('stripped binary ' + file)

    def make_tarball(self):
        """
        Create the tarball and update the base64 checksum in the associated source.json file
        """
        tarball_name = f'{self.TARBALL_DIR}/{self.mod_name}-{self.mod_version}.tar.xz'
        if os.path.exists(tarball_name):
            logger.info("Removing previous tarball")
            os.remove(tarball_name)
        logger.info('Generating tarball - this will take a while')
        result = subprocess.run(f'cd {self.mod_src_dir} && tar cJf {self.TARBALL_DIR}/{self.mod_name}-{self.mod_version}.tar.xz .',
                    shell=True, check=True, capture_output=True, encoding='utf8')
        if result.returncode != 0:
            logger.error('tarball generation failed: ' + result.stderr)
            sys.exit()
        logger.info('generated tarball ' + tarball_name)
        result = subprocess.run(f'openssl dgst -binary -sha256 < {tarball_name} | openssl base64 -A',
                    shell=True, check=True, capture_output=True, encoding='utf8')
        if result.returncode != 0:
            logger.error('digest generation failed: ' + result.stderr)
            sys.exit()
        logger.info('generated sha256 digest ' + result.stdout)
        digest = result.stdout.strip()

        source_file = f"""{{
    "url": "file://{tarball_name}",
    "integrity": "sha256-{digest}",
    "strip_prefix": "",
    "patches": [],
    "patch_strip": 0
}}
"""
        if not os.path.exists(f'{self.MOD_DIR}/{self.mod_name}/{self.mod_version}'):
            os.mkdir(f'{self.MOD_DIR}/{self.mod_name}/{self.mod_version}')
        with open(f'{self.MOD_DIR}/{self.mod_name}/{self.mod_version}/source.json', 'w', encoding='utf8') as sf:
            sf.write(source_file)
        logger.info('updated module source.json with new digest ' + digest)

