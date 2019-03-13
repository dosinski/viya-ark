#!/usr/bin/python

####################################################################
#### get_sas_host_details.py                                    ####
####################################################################
#### Author: SAS Institute Inc.                                 ####
####################################################################

import os
import datetime
import glob
import subprocess
import re
from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['release'],
    'supported_by': 'SAS'
}

DOCUMENTATION = '''
---
module: get_sas_host_details

short_description: Inspects SAS deployment on host.

description: >
    Inspects the details of a SAS deployment on a given host, including installed packages, SAS service information,
    and machine resources.

options:
    hostvars:
        description:
            - The hostvars information for the host on which the module is being run.
        required: true
    include_package_files:
        description: >
            Specifies whether the data returned should include a list of files installed by each package.
            This option will greatly increase the size of the data being returned.
        default: false
        required: false
'''

EXAMPLES = '''
# Get SAS deployment information
- name: Inspect SAS deployment
  get_sas_host_details:
    hostvars: "{{ hostvars[inventory_hostname] }}"
    
# Get SAS deployment information with package file details
- name: Inspect SAS deployment
  get_sas_host_details:
    hostvars: "{{ hostvars[inventory_hostname] }}"
    include_package_files: true
'''

RETURN = '''
results:
    description: A textual representation of the SAS deployment.
    type: dict
'''


# =====
# Class: _AnsibleFactsKeys(object)
# =====
class _AnsibleFactsKeys(object):
    """
    Internal class for static reference to key names in *ansible_facts* (dict)
    within *hostvars* (dict) that is passed in as a parameter to this module.

    A nested class is provided for referencing key names in nested dicts:

    +-------------------+-------------------------------+
    | dict key          | nested key reference class    |
    +===================+===============================+
    | default_ipv4      | DefaultIpv4Keys               |
    +-------------------+-------------------------------+
    | python            | PythonKeys                    |
    +-------------------+-------------------------------+

    :cvar str ARCHITECTURE:   Key referencing *architecture* (str) in *ansible_facts* (dict).
    :cvar str DEFAULT_IPV4:   Key referencing *default_ipv4* (dict) in *ansible_facts* (dict).
    :cvar str DISTRIBUTION:   Key referencing *distribution* (str) in *ansible_facts* (dict).
    :cvar str FQDN:           Key referencing *fqdn* (str) in *ansible_facts* (dict).
    :cvar str OS_FAMILY:      Key referencing *os_family* (str) in *ansible_facts* (dict).
    :cvar str OS_VERSION:     Key referencing *distribution_version* (str) in *ansible_facts* (dict).
    :cvar str PKG_MGR:        Key referencing *pkg_mgr* (str) in *ansible_facts* (dict).
    :cvar str PYTHON:         Key referencing *python* (dict) in *ansible_facts* (dict).
    :cvar str PYTHON_VERSION: Key referencing *python_version* (str) in *ansible_facts* (dict).
    """
    ARCHITECTURE = 'architecture'
    DEFAULT_IPV4 = 'default_ipv4'
    DISTRIBUTION = 'distribution'
    FQDN = 'fqdn'
    OS_FAMILY = 'os_family'
    OS_VERSION = 'distribution_version'
    PKG_MGR = 'pkg_mgr'
    PYTHON = 'python'
    PYTHON_VERSION = 'python_version'

    # =====
    # Class: DefaultIpv4Keys(object)
    # =====
    class DefaultIpv4Keys(object):
        """
        Nested internal class for static reference to key names in *default_ipv4* (dict)
        within *ansible_facts* (dict) from *hostvars* (dict), which is passed as a parameter
        to this module.

        :cvar str ADDRESS: Key referencing *address* (str) in *default_ipv4* (dict).
        """
        ADDRESS = 'address'

    # =====
    # Class: PythonKeys(object)
    # =====
    class PythonKeys(object):
        """
        Nested internal class for static reference to key names in *python* (dict)
        within *ansible_facts* (dict) from *hostvars* (dict), which is passed as a parameter
        to this module.

        :cvar str EXEC: Key referencing *executable* (str) in *python* (dict).
        """
        EXEC = 'executable'


# =====
# Class: _HostDetailsKeys(object)
# =====
class _HostDetailsKeys(object):
    """
    Internal class for static reference to key names in *sas_host_details* (dict),
    which is returned as an ansible_fact at the completion of module execution.

    The top level keys are:

    .. code-block:: yaml

        sas_host_details:
            <hostname>
                _id:
                ansible_host_groups: []
                ipv4: ''
                os: {}
                resource_check: {}
                required_software: {}
                sas_packages: {}
                sas_services: {}

    Nested classes are provided for referencing key names in nested dicts:

    +------------------------------+-------------------------------+
    | dict key                     | nested key reference class    |
    +==============================+===============================+
    | os                           | OSKeys                        |
    +------------------------------+-------------------------------+
    | resource_check               | ResourceCheckKeys             |
    +------------------------------+-------------------------------+
    | required_software            | RequiredSoftwareKeys          |
    +------------------------------+-------------------------------+
    | sas_packages.<package_name>  | SASPackageKeys                |
    +------------------------------+-------------------------------+
    | sas_services                 | SASServicesKeys               |
    +------------------------------+-------------------------------+

    :cvar str ID:             Key referencing *_id* (str) in *sas_host_details* (dict).
    :cvar str IPV4:           Key referencing *ipv4* (str) in *sas_host_details* (dict).
    :cvar str HOST_GROUPS:    Key referencing *ansible_host_groups* (list) in *sas_host_details* (dict).
    :cvar str OS:             Key referencing *os* (dict) in *sas_host_details* (dict).
    :cvar str RESOURCE_CHECK: Key referencing *resource_check* (dict) in *sas_host_details* (dict).
    :cvar str SAS_PACKAGES:   Key referencing *sas_packages* (dict) in *sas_host_details* (dict).
    :cvar str SAS_SERVICES:   Key referencing *sas_services* (dict) in *sas_host_details* (dict).
    :cvar str UNREACHABLE:    Key referencing *_unreachable* (bool) in *sas_host_details* (dict).
    """
    ID = '_id'
    IPV4 = 'ipv4'
    HOST_GROUPS = 'ansible_host_groups'
    OS = 'os'
    RESOURCE_CHECK = 'resource_check'
    REQUIRED_SOFTWARE = 'required_software'
    SAS_PACKAGES = 'sas_packages'
    SAS_SERVICES = 'sas_services'
    UNREACHABLE = '_unreachable'

    # =====
    # Class: OSKeys(object)
    # =====
    class OSKeys(object):
        """
        Nested internal class for static reference to key names in *os* (dict), which
        is returned as part of *sas_host_details* (dict).

        The top level keys are:

        .. code-block:: yaml

            os:
                architecture: ''
                distribution: ''
                family: ''
                package_manager: ''
                version: ''

        :cvar str ARCHITECTURE:    Key referencing *architecture* (str) in *os* (dict).
        :cvar str DISTRIBUTION:    Key referencing *distribution* (str) in *os* (dict).
        :cvar str FAMILY:          Key referencing *family* (str) in *os* (dict).
        :cvar str PACKAGE_MANAGER: Key referencing *package_manager* (str) in *os* (dict).
        :cvar str VERSION:         Key referencing *version* (str) in *os* (dict).
        """
        ARCHITECTURE = 'architecture'
        DISTRIBUTION = 'distribution'
        FAMILY = 'family'
        PACKAGE_MANAGER = 'package_manager'
        VERSION = 'version'

    # =====
    # Class: ResourcesKeys(object)
    # =====
    class ResourceCheckKeys(object):
        """
        Nested internal class for static reference to key names in *resource_check*
        (dict) which is returned as part of *sas_host_details* (dict). Because both
        *filesystems* (dict) and *memory* (dict) have the same internal structure, some
        of their keys are defined in this class (RESULTS, RESULTS_FORMAT, RESULTS_TIMESTAMP,
        and RESULTS_UNIT).

        The top level keys are:

        .. code-block:: yaml

            resource_check:
                filesystems:
                    results: {}
                    results_timestamp: ''
                    results_unit: ''
                memory:
                    results: {}
                    results_format: ''
                    results_timestamp: ''
                    results_unit: ''
                sas_root:
                    results: {}
                    results_format: ''
                    results_timestamp: ''
                    results_unit: ''

        Nested classes are provided for referencing key names in nested dicts:

        +-----------------------------+-------------------------------+
        | dict key                    | nested key reference class    |
        +=============================+===============================+
        | filesystems.results.<index> | FilesystemAttributesKeys      |
        +-----------------------------+-------------------------------+
        | memory.results              | MemoryResultsKeys             |
        +-----------------------------+-------------------------------+
        | sas_root.results            | SASRootResultsKeys            |
        +-----------------------------+-------------------------------+

        :cvar str FILESYSTEMS:       Key referencing *filesystems* (dict) in *resource_check* (dict).
        :cvar str MEMORY:            Key referencing *memory* (dict) in *resource_check* (dict).
        :cvar str SAS_ROOT:          Key referencing *sas_root* (dict) in *resource_check* (dict)
        :cvar str RESULTS:           Key referencing *results* (dict) in *filesystems* (dict) and *memory* (dict).
        :cvar str RESULTS_FORMAT:    Key referencing *results_format* (str) in *memory* (dict).
        :cvar str RESULTS_TIMESTAMP: Key referencing *results_timestamp* (str) in *filesystems* (dict) and *memory*
                                     (dict).
        :cvar str RESULTS_UNIT:      Key referencing *results_unit* (str) in *filesystems* (dict) and *memory* (dict).
        """
        FILESYSTEMS = 'filesystems'
        MEMORY = 'memory'
        SAS_ROOT = 'sas_root'
        RESULTS = 'results'
        RESULTS_FORMAT = 'results_format'
        RESULTS_TIMESTAMP = 'results_timestamp'
        RESULTS_UNIT = 'results_unit'

        # =====
        # Class: FilesystemDetailsKeys(object)
        # =====
        class FilesystemAttributesKeys(object):
            """
            Nested internal class for static reference to key names in the dict of results
            returned for each filesystem as part of *resource_check* (dict). Because filesystems
            do not have consistent names, the key for each result in this dict is the index at
            which the filesystem was returned in the output from the **df** command.

            The top level keys are:

            .. code-block:: yaml

                filesystems:
                    results:
                        '<index>':
                            available: ''
                            filesystem: ''
                            mounted_on: ''
                            size: ''
                            type: ''
                            used: ''
                            used_ratio: ''

            :cvar str AVAILABLE:    Key referencing *available* (str) in a filesystem's results dict.
            :cvar str FILESYSTEM:   Key referencing *filesystem* (str) in a filesystem's results dict.
            :cvar str MOUNTED_ON:   Key referencing *mounted_on* (str) in a filesystem's results dict.
            :cvar str SIZE:         Key referencing *size* (str) in a filesystem's results dict.
            :cvar str TYPE:         Key referencing *type* (str) in a filesystem's results dict.
            :cvar str USED:         Key referencing *used* (str) in a filesystem's results dict.
            :cvar str USED_RATIO:   Key referencing *used_ratio* (str) in a filesystem's results dict.
            """
            AVAILABLE = 'available'
            FILESYSTEM = 'filesystem'
            MOUNTED_ON = 'mounted_on'
            SIZE = 'size'
            TYPE = 'type'
            USED = 'used'
            USED_RATIO = 'used_ratio'

        # =====
        # Class: MemoryKeys(object)
        # =====
        class MemoryResultsKeys(object):
            """
            Nested internal class for static reference to key names in the dict of results
            returned for each memory type as part of *resource_check* (dict).

            The top level keys are:

            .. code-block:: yaml

                memory:
                    results:
                        physical: {}
                        swap: {}

            A nested class is provided for referencing key names in nested dicts:

            +-------------------+-------------------------------+
            | dict key          | nested key reference class    |
            +===================+===============================+
            | physical/swap     | MemoryAttributesKeys          |
            +-------------------+-------------------------------+

            :cvar str PHYSICAL: Key referencing *physical* (dict) in *results* (dict).
            :cvar str SWAP:     Key referencing *swap* (dict) in *results* (dict).
            """
            PHYSICAL = 'physical'
            SWAP = 'swap'

            # =====
            # Class: MemoryDetailsKeys(object)
            # =====
            class MemoryAttributesKeys(object):
                """
                Nested internal class for static reference to key names in *physical* (dict) and *swap*
                (dict) returned as part of *memory.results* (dict) in *resource_check* (dict). Both dicts
                have the same internal structure, so keys in this class can be used to reference values
                in either.

                The top level keys are:

                .. code-block:: yaml

                    physical/swap:
                        available: ''
                        buff_cache: ''
                        buffers: ''
                        cached: ''
                        free: ''
                        shared: ''
                        total: ''
                        used: ''

                :cvar str AVAILABLE:  Key referencing *available* (str) in *physical*/*swap* (dict).
                :cvar str BUFF_CACHE: Key referencing *buff_cache* (str) in *physical*/*swap* (dict).
                :cvar str BUFFERS:    Key referencing *buffers* (str) in *physical*/*swap* (dict).
                :cvar str CACHED:     Key referencing *cached* (str) in *physical*/*swap* (dict).
                :cvar str FREE:       Key referencing *free* (str) in *physical*/*swap* (dict).
                :cvar str SHARED:     Key referencing *shared* (str) in *physical*/*swap* (dict).
                :cvar str TOTAL:      Key referencing *total* (str) in *physical*/*swap* (dict).
                :cvar str USED:       Key referencing *used* (str) in *physical*/*swap* (dict).
                """
                AVAILABLE = 'available'
                BUFF_CACHE = 'buff_cache'
                BUFFERS = 'buffers'
                CACHED = 'cached'
                FREE = 'free'
                SHARED = 'shared'
                TOTAL = 'total'
                USED = 'used'

        # =====
        # Class: SASRootKeys(object)
        # =====
        class SASRootResultsKeys(object):
            """
            Nested internal class for static reference to key names in *sas_root* (dict),
            which is returned as part of *resource_check* (dict).

            The top level keys are:

            .. code-block:: yaml

                sas_root:
                    results:
                        filesystem: ''
                        filesystem_size: ''
                        mount: ''
                        path: ''
                        size: ''
                        used_ratio: ''

            :cvar str FILESYSTEM:       Key referencing *filesystem* (str) in *sas_root* (dict).
            :cvar str FILESYSTEM_TOTAL: Key referencing *filesystem_total* (str) in *sas_root* (dict).
            :cvar str MOUNT:            Key referencing *mount* (str) in *sas_root* (dict).
            :cvar str PATH:             Key referencing *path* (str) in *sas_root* (dict).
            :cvar str SIZE:             Key referencing *size* (str) in *sas_root* (dict).
            :cvar str USED_RATIO:       Key referencing *used_ration* (str) in *sas_root* (dict)
            """
            FILESYSTEM = 'filesystem'
            FILESYSTEM_TOTAL = 'filesystem_total'
            MOUNT = 'mount'
            PATH = 'path'
            SIZE = 'size'
            USED_RATIO = 'used_ratio'

    # =====
    # Class: RequiredSoftwareKeys(object)
    # =====
    class RequiredSoftwareKeys(object):
        """
        Nested internal class for static reference to key names in *required_software*
        (dict), which is returned as part of *sas_host_details* (dict)

        The top level keys are:

        .. code-block:: yaml

            required_software:
                java: {}
                python: {}

        A nested class is provided for referencing key names in nested dicts:

        +-------------------+-------------------------------+
        | dict key          | nested key reference class    |
        +===================+===============================+
        | java/python       | SoftwareAttributesKeys        |
        +-------------------+-------------------------------+

        :cvar str JAVA:   Key referencing *java* in *required_software* (dict).
        :cvar str PYTHON: Key referencing *python* in *required_software* (dict).
        """
        JAVA = 'java'
        PYTHON = 'python'

        # =====
        # Class: SoftwareAttributesKeys
        # =====
        class SoftwareAttributesKeys(object):
            """
            Nested internal class for static reference to key names in *java* (dict) and *python* (dict).

            The top level keys are:

            .. code-block:: yaml

                python/java:
                    path: ''
                    version: ''

            :cvar str PATH: Key referencing *path* (str) in *java*/*python* (dict).
            :cvar str VERSION: Key referencing *version* (str) in *java*/*python* (dict).
            """
            PATH = 'path'
            VERSION = 'version'

    # =====
    # Class: SASPackageKeys(object)
    # =====
    class SASPackageKeys(object):
        """
        Nested internal class for static reference to key names in the dict
        for each SAS package in *sas_packages* (dict), which is returned as
        part of *sas_host_details* (dict).

        The top level keys are:

        .. code-block:: yaml

            sas_packages:
                <package_name>:
                    attributes: {}
                    installed_files: []
                    provided_services: []

        A nested class is provided for referencing key names in nested dicts:

        +----------------------------+-------------------------------+
        | dict key                   | nested key reference class    |
        +============================+===============================+
        | <package_name>.attributes  | PackageAttributesKeys         |
        +----------------------------+-------------------------------+

        :cvar str ATTRIBUTES:        Key referencing *attributes* (dict) in a SAS package dict.
        :cvar str INSTALLED_FILES:   Key referencing *installed_files* (list) in a SAS package dict.
        :cvar str PROVIDED_SERVICES: Key referencing *provided_services* (list) in a SAS package dict.
        """
        ATTRIBUTES = 'attributes'
        INSTALLED_FILES = 'installed_files'
        PROVIDED_SERVICES = 'provided_services'

        # =====
        # Class: PackageAttributesKeys(object)
        # =====
        class PackageAttributesKeys(object):
            """
            Nested internal class for static reference to key names in *attributes* (dict)
            returned for each package in *sas_packages* (dict).

            The top level keys are:

            .. code-block:: yaml

                <package_name>
                    attributes:
                        arch: ''
                        from_repository: ''
                        size: ''
                        summary: ''
                        version: ''

            :cvar str ARCH:      Key referencing *arch* (str) in *attributes* (dict) for a package.
            :cvar str FROM_REPO: Key referencing *from_repository* (str) in  *attributes* (dict) for a package.
            :cvar str SIZE:      Key referencing *size* (str) in *attributes* (dict) for a package.
            :cvar str SUMMARY:   Key referencing *summary* (str) in *attributes* (dict) for a package.
            :cvar str VERSION:   Key referencing *version* (str) in *attributes* (dict) for a package.
            """
            ARCH = 'arch'
            FROM_REPO = 'from_repository'
            SIZE = 'size'
            SUMMARY = 'summary'
            VERSION = 'version'

    # =====
    # Class: SASServicesKeys(object)
    # =====
    class SASServicesKeys(object):
        """
        Nested internal class for static reference to key names in *sas_services* (dict)
        returned as part of *sas_host_details* (dict).

        The top level keys are:

        .. code-block:: yaml

            sas_services:
                installed: {}
                status: {}

        Nested classes are provided for referencing key names in nested dicts:

        +-------------------+-------------------------------+
        | dict key          | nested key reference class    |
        +===================+===============================+
        | installed         | InstalledServiceKeys          |
        +-------------------+-------------------------------+
        | status            | ServicesStatusKeys            |
        +-------------------+-------------------------------+

        :cvar str INSTALLED: Key referencing *installed* (dict) in *sas_services* (dict).
        :cvar str STATUS:    Key referencing *status* (dict) in *sas_services* (dict).
        """
        INSTALLED = 'installed'
        STATUS = 'status'

        # =====
        # Class: ServicesDetailsKeys(object)
        # =====
        class InstalledServiceKeys(object):
            """
            Nested internal class for static reference to key names in the dict returned for
            each service within *installed* (dict).

            The top level keys are:

            .. code-block:: yaml

                <service_name>:
                    attributes: {}
                    installed_by: ''

            A nested class is provided for referencing key names in nested dicts:

            +----------------------------+-------------------------------+
            | dict key                   | nested key reference class    |
            +============================+===============================+
            | <package_name>.attributes  | ServiceAttributesKeys         |
            +----------------------------+-------------------------------+

            :cvar str ATTRIBUTES:   Key referencing *attributes* (dict) in the dict for each installed service.
            :cvar str INSTALLED_BY: Key referencing *installed_by* (str) in the dict for each installed service.
            """
            ATTRIBUTES = 'attributes'
            INSTALLED_BY = 'installed_by'

            # =====
            # Class: ServiceAttributesKeys(object)
            # =====
            class ServiceAttributesKeys(object):
                """
                Nested internal class for static reference to key names in *attributes* (dict), returned
                for each service in *installed* (dict).

                The top level keys are:

                .. code-block:: yaml

                    attributes:
                        port: ''
                        pid: ''
                        status: ''

                :cvar str PORT:   Key referencing *port* (str) in *attributes* (dict).
                :cvar str PID:    Key referencing *pid* (str) in *attributes* (dict).
                :cvar str STATUS: Key referencing *status* (str) in *attributes* (dict).
                """
                PORT = 'port'
                PID = 'pid'
                STATUS = 'status'

        # =====
        # Class: ServicesStatusKeys(object)
        # =====
        class ServicesStatusKeys(object):
            """
            Nested internal class for static reference to key names in *status* (dict) returned
            as part of *sas_services* (dict).

            The top level keys are:

            .. code-block:: yaml

                status:
                    down: ''
                    other: ''
                    up: ''

            :cvar str DOWN:  Key referencing *down* (str) in *status* (dict).
            :cvar str OTHER: Key referencing *other* (str) in *status* (dict).
            :cvar str UP:    Key referencing *up* (str) in *status* (dict).
            """
            DOWN = 'down'
            OTHER = 'other'
            UP = 'up'


# =====
# Class: _HostvarsKeys(object)
# =====
class _HostvarsKeys(object):
    """
    Internal class for static reference to keys in *hostvars* (dict) passed
    as a parameter to this module.

    :cvar str ANSIBLE_FACTS:          Key referencing *ansible_facts* (dict) in *hostvars* (dict).
    :cvar str ANSIBLE_GROUP_NAMES:    Key referencing *group_names* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_ARCHITECTURE:   Key referencing *ansible_architecture* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_DEFAULT_IPV4:   Key referencing *ansible_default_ipv4* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_DISTRIBUTION:   Key referencing *ansible_distribution* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_FQDN:           Key referencing *ansible_fqdn* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_OS_FAMILY:      Key referencing *ansible_os_family* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_OS_VERSION:     Key referencing *ansible_distribution_version* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_PKG_MGR:        Key referencing *ansible_pkg_mgr* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_PYTHON:         Key referencing *ansible_python* (list) in *hostvars* (dict).
    :cvar str ANSIBLE_PYTHON_VERSION: Key referencing *ansible_python_version* (list) in *hostvars* (dict).
    """
    ANSIBLE_FACTS = 'ansible_facts'
    ANSIBLE_GROUP_NAMES = 'group_names'
    ANSIBLE_ARCHITECTURE = 'ansible_architecture'
    ANSIBLE_DEFAULT_IPV4 = 'ansible_default_ipv4'
    ANSIBLE_DISTRIBUTION = 'ansible_distribution'
    ANSIBLE_FQDN = 'ansible_fqdn'
    ANSIBLE_OS_FAMILY = 'ansible_os_family'
    ANSIBLE_OS_VERSION = 'ansible_distribution_version'
    ANSIBLE_PKG_MGR = 'ansible_pkg_mgr'
    ANSIBLE_PYTHON = 'ansible_python'
    ANSIBLE_PYTHON_VERSION = 'ansible_python_version'


# =====
# Class: _ModuleParamKeys(object)
# =====
class _ModuleParamKeys(object):
    """
    Internal class for static reference to keys in *params* (dict) which holds the
    input values defined for this module.

    :cvar str HOSTVARS:       Key referencing *hostvars* (dict) in *params* (dict).
    :cvar str INCL_PKG_FILES: Key referencing *include_package_files* (dict) in *params* (dict).
    """
    HOSTVARS = 'hostvars'
    INCL_PKG_FILES = 'include_package_files'


# =====
# Class: _OSFamilies(object)
# =====
class _OSFamilies(object):
    """
    Internal class for static reference to *os_family* (str) values supported for this module.

    :cvar str REDHAT: RedHat OS family.
    :cvar str SUSE:   Suse OS family.
    """
    REDHAT = 'RedHat'
    SUSE = 'Suse'


# =====
# Class: _PackageManagers(object)
# =====
class _PackageManagers(object):
    """
    Internal class for static reference to *package_manager* (str) values supported for this module.

    :cvar str YUM:    yum package manager.
    :cvar str ZYPPER: zypper package manager.
    """
    YUM = 'yum'
    ZYPPER = 'zypper'


# =====
# Class: _ResourceFormats(object)
# =====
class _ResourceFormats(object):
    """
    Internal class for static reference to the format type for resource checks.
    Currently this helps to distinguish between the format of output from free-3.3.9
    and free-3.3.10 where the output changed and values could be misrepresented without
    knowing which format was returned.

    :cvar str CURRENT: Denotes the resource results are in the current format.
    :cvar str OLD:     Denotes the resource results are in an old format.
    """
    CURRENT = 'current'
    OLD = 'old'


# =====
# Class: _ResourceUnits(object)
# =====
class _ResourceUnits(object):
    """
    Internal class for static reference to the size units used for the *resource_check*
    results.

    :cvar str MB: Megabytes.
    """
    MB = 'MB'


# =====
# Class: _ServiceStatus(object)
# =====
class _ServiceStatus(object):
    """
    Internal class for static reference to service status values.

    :cvar str DOWN: Denotes a service's status as down.
    :cvar str UP:   Denotes a service's status as up.
    """
    DOWN = 'down'
    UP = 'up'


# =====
# Class: _YumInfoKeys(object)
# =====
class _YumInfoKeys(object):
    """
    Internal class for static reference to key names in the output from running
    **yum info** against a package.

    :cvar str ARCH:      The package's architecture.
    :cvar str FROM_REPO: The repo the package was installed from.
    :cvar str NAME:      The package's name.
    :cvar str RELEASE:   The package's release value (used in constructing the full version)
    :cvar str SIZE:      The package's size.
    :cvar str SUMMARY:   The package's summary.
    :cvar str VERSION:   The package's version (used in constructing the full version).
    """
    ARCH = 'Arch'
    FROM_REPO = 'From repo'
    NAME = 'Name'
    RELEASE = 'Release'
    SIZE = 'Size'
    SUMMARY = 'Summary'
    VERSION = 'Version'


# =====
# Class: _ZypperInfoKeys(object)
# =====
class _ZypperInfoKeys(object):
    """
    Internal class for static reference to key names in the output from running
    **zypper info** against a package.

    :cvar str ARCH:      The package's architecture.
    :cvar str FROM_REPO: The repo the package was installed from.
    :cvar str NAME:      The package's name.
    :cvar str RELEASE:   The package's release value.
    :cvar str SIZE:      The package's size.
    :cvar str SUMMARY:   The package's summary.
    :cvar str VERSION:   The package's version.
    """
    ARCH = 'Arch'
    FROM_REPO = 'Repository'
    NAME = 'Name'
    SIZE = 'Installed Size'
    SUMMARY = 'Summary'
    VERSION = 'Version'


# --- Constants --- #
# A group aggregating all groups in a SAS Viya inventory file
GROUP_SAS_ALL = 'sas-all'
# Key name of the dict returned by this module as an ansible_fact
MODULE_RETURN_KEY = 'results'
# Root directory path for SAS install
SAS_ROOT_PATH = '/opt/sas'


# =====
# main() (Entry point for Ansible module execution)
# =====
def main():
    """
    Entry method for Ansible module.
    """

    # the AnsibleModule object will be our abstraction for working with Ansible.
    # This includes instantiation, a couple of common attr that will be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec={_ModuleParamKeys.HOSTVARS: dict(type=dict, required=True),
                       _ModuleParamKeys.INCL_PKG_FILES: dict(type=bool, default=False, required=False)},
        supports_check_mode=True
    )

    # get module parameters
    hostvars = module.params[_ModuleParamKeys.HOSTVARS]
    include_package_files = module.params[_ModuleParamKeys.INCL_PKG_FILES]

    # get dict of ansible_facts
    ansible_facts = hostvars.get(_HostvarsKeys.ANSIBLE_FACTS)

    if ansible_facts is not None:
        hostname = ansible_facts[_AnsibleFactsKeys.FQDN]
        package_manager = ansible_facts[_AnsibleFactsKeys.PKG_MGR]
        ipv4 = ansible_facts[_AnsibleFactsKeys.DEFAULT_IPV4][_AnsibleFactsKeys.DefaultIpv4Keys.ADDRESS]
        os_family = ansible_facts[_AnsibleFactsKeys.OS_FAMILY]
        os_distribution = ansible_facts[_AnsibleFactsKeys.DISTRIBUTION]
        os_arch = ansible_facts[_AnsibleFactsKeys.ARCHITECTURE]
        os_version = ansible_facts[_AnsibleFactsKeys.OS_VERSION]
    else:
        hostname = hostvars[_HostvarsKeys.ANSIBLE_FQDN]
        package_manager = hostvars[_HostvarsKeys.ANSIBLE_PKG_MGR]
        ipv4 = hostvars[_HostvarsKeys.ANSIBLE_DEFAULT_IPV4][_AnsibleFactsKeys.DefaultIpv4Keys.ADDRESS]
        os_family = hostvars[_HostvarsKeys.ANSIBLE_OS_FAMILY]
        os_distribution = hostvars[_HostvarsKeys.ANSIBLE_DISTRIBUTION]
        os_arch = hostvars[_HostvarsKeys.ANSIBLE_ARCHITECTURE]
        os_version = hostvars[_HostvarsKeys.ANSIBLE_OS_VERSION]

    # set up host details dict
    host_details = dict()

    # set host id ('.' replaced with '-' for ease of use in html)
    host_details[_HostDetailsKeys.ID] = hostname.replace('.', '-')

    # set if host was reachable
    # if this script is executing then the host is reachable
    host_details[_HostDetailsKeys.UNREACHABLE] = False

    # set ipv4
    host_details[_HostDetailsKeys.IPV4] = ipv4

    # set required software details
    # host_details[_HostDetailsKeys.REQUIRED_SOFTWARE] = _get_required_software_info(ansible_facts, module)

    # set os details
    host_details[_HostDetailsKeys.OS] = {
        _HostDetailsKeys.OSKeys.FAMILY: os_family,
        _HostDetailsKeys.OSKeys.DISTRIBUTION: os_distribution,
        _HostDetailsKeys.OSKeys.ARCHITECTURE: os_arch,
        _HostDetailsKeys.OSKeys.VERSION: os_version,
        _HostDetailsKeys.OSKeys.PACKAGE_MANAGER: package_manager
    }

    # set Ansible host groups for current host (sas-all is removed since it's just an aggregation of groups)
    ansible_host_groups = hostvars[_HostvarsKeys.ANSIBLE_GROUP_NAMES]
    try:
        ansible_host_groups.remove(GROUP_SAS_ALL)
    except ValueError:
        pass  # do nothing
    host_details[_HostDetailsKeys.HOST_GROUPS] = ansible_host_groups

    # set host resource_check info
    host_details[_HostDetailsKeys.RESOURCE_CHECK] = {
        _HostDetailsKeys.ResourceCheckKeys.FILESYSTEMS: _get_filesystems_info(module),
        _HostDetailsKeys.ResourceCheckKeys.MEMORY: _get_memory_info(module),
        _HostDetailsKeys.ResourceCheckKeys.SAS_ROOT: _get_sas_root_info(module)
    }

    # set host sas deployment info
    host_details[_HostDetailsKeys.SAS_PACKAGES] = _get_sas_package_info(module, package_manager, include_package_files)
    host_details[_HostDetailsKeys.SAS_SERVICES] = _get_sas_service_info(module)

    # map packages to any services they installed
    for package_name, package_data in host_details[_HostDetailsKeys.SAS_PACKAGES].items():
        for service_name in package_data[_HostDetailsKeys.SASPackageKeys.PROVIDED_SERVICES]:
            if service_name in host_details[_HostDetailsKeys.SAS_SERVICES][_HostDetailsKeys.SASServicesKeys.INSTALLED]:
                services = host_details[_HostDetailsKeys.SAS_SERVICES][_HostDetailsKeys.SASServicesKeys.INSTALLED]
                services[service_name][_HostDetailsKeys.SASServicesKeys.InstalledServiceKeys.INSTALLED_BY] = \
                    package_name

    results = {
        hostname: host_details
    }

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    #
    # changed will always be 'False' since we'll never alter state on a host
    module.exit_json(changed=False, results=results)


# =====
# _get_filesystem_info(AnsibleModule)
# =====
def _get_filesystems_info(module):
    """
    Retrieves file system information (via the **df** command) for the current host and returns the data as a dict.

    :param AnsibleModule module: The AnsibleModule object representing the current module.
    :returns: A dict of filesystem indexes mapped to the filesystem attributes.
    :rtype dict:
    """

    # get a timestamp for when this information is being gathered (this can be used for reporting)
    filesystem_timestamp = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M%p")

    # initialize dict with results to be returned
    results = {
        _HostDetailsKeys.ResourceCheckKeys.RESULTS: dict(),
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_FORMAT: _ResourceFormats.CURRENT,
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_TIMESTAMP: filesystem_timestamp,
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_UNIT: _ResourceUnits.MB
    }

    # execute the command to retrieve filesystem information
    cmd_stdout = _execute_command("df --print-type --block-size=MB", module)

    # split stdout by each line
    all_filesystems = cmd_stdout.split('\n')[1:]

    # an index will be used at the key for each filesystem since there is no
    # predictably unique attributes
    filesystem_index = 1
    for filesystem in all_filesystems:

        # split space-delineated information
        filesystem_info = filesystem.split()

        # add the current filesystem to the dict at the current index.
        if len(filesystem_info) == 7:
            results[_HostDetailsKeys.ResourceCheckKeys.RESULTS][filesystem_index] = {
                _HostDetailsKeys.ResourceCheckKeys.FilesystemAttributesKeys.FILESYSTEM: filesystem_info[0],
                _HostDetailsKeys.ResourceCheckKeys.FilesystemAttributesKeys.TYPE: filesystem_info[1],
                _HostDetailsKeys.ResourceCheckKeys.FilesystemAttributesKeys.SIZE: filesystem_info[2],
                _HostDetailsKeys.ResourceCheckKeys.FilesystemAttributesKeys.USED: filesystem_info[3],
                _HostDetailsKeys.ResourceCheckKeys.FilesystemAttributesKeys.AVAILABLE: filesystem_info[4],
                _HostDetailsKeys.ResourceCheckKeys.FilesystemAttributesKeys.USED_RATIO: filesystem_info[5],
                _HostDetailsKeys.ResourceCheckKeys.FilesystemAttributesKeys.MOUNTED_ON: filesystem_info[6]
            }

            # increment index
            filesystem_index += 1

    # return the filesystem information
    return results


# =====
# _get_memory_info(AnsibleModule)
# =====
def _get_memory_info(module):
    """
    Retrieves memory information (via the 'free' command) for the current host and returns the data as a dict.

    :param AnsibleModule module: The AnsibleModule object representing the current module.
    :returns: A dict of memory types mapped to that type's attributes.
    :rtype dict:
    """

    # get a timestamp for when this information is being gathered (this can be used for reporting)
    memory_timestamp = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M%p")

    # initialize dict with results to be returned
    results = {
        _HostDetailsKeys.ResourceCheckKeys.RESULTS: dict(),
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_FORMAT: '',
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_TIMESTAMP: memory_timestamp,
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_UNIT: _ResourceUnits.MB
    }
    mem_results = results[_HostDetailsKeys.ResourceCheckKeys.RESULTS]

    # execute the command to retrieve memory information
    cmd_stdout = _execute_command("free -m", module)

    # split the stdout by new line (each mem type should be on its own line)
    all_mem = cmd_stdout.split('\n')[1:]
    mem = all_mem[0].split()
    swap = all_mem[1].split()

    # check for '-/+ buffer/cache' line that is in older versions for free
    # this output was removed in free-3.3.10
    free_format = _ResourceFormats.CURRENT
    if swap[0] == '-/+':
        swap = all_mem[2].split()
        free_format = _ResourceFormats.OLD

    # add format type to results
    results[_HostDetailsKeys.ResourceCheckKeys.RESULTS_FORMAT] = free_format

    # get attributes of physical memory
    physical_results = dict()
    if len(mem) == 7:
        physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.TOTAL] = mem[1]
        physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.USED] = mem[2]
        physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.FREE] = mem[3]
        physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.SHARED] = mem[4]

        if free_format == _ResourceFormats.CURRENT:
            # current format
            physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.BUFF_CACHE] = \
                mem[5]
            physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.AVAILABLE] = \
                mem[6]
            # old format
            physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.BUFFERS] = ''
            physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.CACHED] = ''
        else:
            # current format
            physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.BUFF_CACHE] = ''
            physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.AVAILABLE] = ''
            # old format
            physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.BUFFERS] = mem[5]
            physical_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.CACHED] = mem[6]

        mem_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.PHYSICAL] = physical_results

    # get attributes of swap space
    swap_results = dict()
    if len(swap) == 4:
        swap_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.TOTAL] = swap[1]
        swap_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.USED] = swap[2]
        swap_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.FREE] = swap[3]
        swap_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.SHARED] = ''
        # current format
        swap_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.BUFF_CACHE] = ''
        swap_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.AVAILABLE] = ''
        # old format
        swap_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.BUFFERS] = ''
        swap_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.MemoryAttributesKeys.CACHED] = ''

        mem_results[_HostDetailsKeys.ResourceCheckKeys.MemoryResultsKeys.SWAP] = swap_results

    # return the memory information
    return results


# =====
# _get_sas_root_info(AnsibleModule)
# =====
def _get_sas_root_info(module):
    """
    Retrieves resource information about the SAS install root and returns a dict of attributes.

    :param AnsibleModule module: The AnsibleModule object representing the current module.
    :return: A dict of attributes for the SAS install root.
    :rtype dict:
    """

    # get a timestamp for when this information is being gathered (this can be used for reporting)
    sas_root_timestamp = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M%p")

    # initialize dict with results to be returned
    results = {
        _HostDetailsKeys.ResourceCheckKeys.RESULTS: dict(),
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_FORMAT: '',
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_TIMESTAMP: sas_root_timestamp,
        _HostDetailsKeys.ResourceCheckKeys.RESULTS_UNIT: _ResourceUnits.MB
    }

    root_results = {
        _HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.FILESYSTEM: '',
        _HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.FILESYSTEM_TOTAL: '',
        _HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.MOUNT: '',
        _HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.PATH: '',
        _HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.SIZE: '',
        _HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.USED_RATIO: '',
    }

    root_du_stdout = _execute_command("du --block-size=MB --summarize " + SAS_ROOT_PATH, module)
    root_du = root_du_stdout.split()

    root_size = ''
    if len(root_du) == 2:
        root_size = root_du[0]
        root_results[_HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.SIZE] = root_size
        root_results[_HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.PATH] = root_du[1]

    root_df_stdout = _execute_command("df --print-type --block-size=MB " + SAS_ROOT_PATH, module)
    root_df = root_df_stdout.split("\n")[1:]

    fs_size = ''
    if len(root_df) > 0:

        root_fs = root_df[0].split()

        if len(root_fs) == 7:
            fs_size = root_fs[2]
            root_results[_HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.FILESYSTEM] = root_fs[0]
            root_results[_HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.FILESYSTEM_TOTAL] = fs_size
            root_results[_HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.MOUNT] = root_fs[6]

    if root_size.endswith(_ResourceUnits.MB) and fs_size.endswith(_ResourceUnits.MB):
        used_ratio = float(root_size[:-2]) / float(fs_size[:-2])
        root_results[_HostDetailsKeys.ResourceCheckKeys.SASRootResultsKeys.USED_RATIO] = \
            str(int(round(used_ratio * 100))) + '%'

    results[_HostDetailsKeys.ResourceCheckKeys.RESULTS] = root_results
    return results


# =====
# _get_sas_service_info(AnsibleModule)
# =====
def _get_sas_service_info(module):
    """
    Retrieves information on SAS services (using the *-all-services' service) for the current host and returns the data
    as a dict.

    :param AnsibleModule module: The AnsibleModule object representing the current module.
    :returns: A dict of SAS services mapped to their attributes.
    :rtype dict:
    """

    # initialize dict with results to be returned
    results = {
        _HostDetailsKeys.SASServicesKeys.INSTALLED: dict(),
        _HostDetailsKeys.SASServicesKeys.STATUS: dict()
    }

    total_up = 0
    total_down = 0
    total_other = 0

    # find all 'all-services' executables
    for service in glob.glob("/etc/init.d/*-all-services"):
        cmd_stdout = _execute_command("{0} status".format(service), module)

        # remove user-friendly output
        status_list = cmd_stdout.split('\n')[2:-3]

        # iterate over status
        for status in status_list:

            # remove leading/trailing whitespace and split by whitespace
            status_values = status.rstrip().split()

            # If line contains all 5 known values, add it to results
            if len(status_values) == 5:

                name = status_values[0]
                status = status_values[1]

                service_attributes = {
                    _HostDetailsKeys.SASServicesKeys.InstalledServiceKeys.ServiceAttributesKeys.STATUS:
                        status,
                    _HostDetailsKeys.SASServicesKeys.InstalledServiceKeys.ServiceAttributesKeys.PORT: status_values[3],
                    _HostDetailsKeys.SASServicesKeys.InstalledServiceKeys.ServiceAttributesKeys.PID: status_values[4]
                }

                # Add up service status totals
                if status == _ServiceStatus.UP:
                    total_up += 1
                elif status == _ServiceStatus.DOWN:
                    total_down += 1
                else:
                    total_other += 1

                results[_HostDetailsKeys.SASServicesKeys.INSTALLED][name] = {
                    _HostDetailsKeys.SASServicesKeys.InstalledServiceKeys.ATTRIBUTES: service_attributes
                }

    # add overall status results to dict
    results[_HostDetailsKeys.SASServicesKeys.STATUS] = {
        _HostDetailsKeys.SASServicesKeys.ServicesStatusKeys.UP: total_up,
        _HostDetailsKeys.SASServicesKeys.ServicesStatusKeys.DOWN: total_down,
        _HostDetailsKeys.SASServicesKeys.ServicesStatusKeys.OTHER: total_other
    }

    # return SAS service information
    return results


# =====
# _get_sas_package_info(AnsibleModule, bool)
# =====
def _get_sas_package_info(module, package_manager, include_package_files=False):
    """
    Retrieves package information for all installed SAS packages and returns the values as a dict.

    :param AnsibleModule module: The AnsibleModule object representing the current module.
    :param bool include_package_files: Toggles whether information about the package's installed files should be
                                       included.
    :return: A dict of package names mapped to a dict containing package attribute names and their values.
    :rtype dict:
    """

    # -- package info -- #
    if package_manager == _PackageManagers.ZYPPER:
        results = _get_sas_package_info_zypper(module)
    else:
        results = _get_sas_package_info_yum(module)

    # -- file info -- #

    # run rpm file list command
    files_cmd_stdout = _execute_command("rpm -qg SAS --queryformat '%{NAME}\n[%{FILENAMES}\n]\n'", module)

    # split output by empty line
    all_package_files = files_cmd_stdout.split("\n\n")[:-1]

    # iterate over each block of output
    services_by_package = dict()
    for package_files in all_package_files:

        # split block by newline
        package_files_list = package_files.split("\n")

        # get the name of the package (first line of output)
        package_name = package_files_list[0]

        if package_name is not None:

            if include_package_files:
                results[package_name][_HostDetailsKeys.SASPackageKeys.INSTALLED_FILES] = package_files_list[1:]

            service_paths = [f for f in package_files_list[1:] if re.match("/etc/.*init.d/.*", f)]
            if len(service_paths) > 0:
                service_names = [os.path.basename(service_path) for service_path in service_paths]
                results[package_name][_HostDetailsKeys.SASPackageKeys.PROVIDED_SERVICES] = service_names

                for service_name in service_names:
                    services_by_package[service_name] = package_name

    # return SAS package information
    return results


# =====
# _get_sas_package_info_yum(AnsibleModule)
# =====
def _get_sas_package_info_yum(module):
    """
    Retrieves package information via yum for all installed SAS packages and returns the values as a dict.

    :param AnsibleModule module: The AnsibleModule object representing the current module.
    :return: A dict of package names mapped to a dict containing package attribute names and their values.
    :rtype dict:
    """
    # define results dict
    results = dict()

    # -- package info -- #

    # run package info command
    info_cmd_stdout = _execute_command("yum -q info $(rpm -qg SAS --queryformat '%{NAME} ')", module)

    # split stdout into an array by empty line, containing package info for all installed packages
    all_package_info = info_cmd_stdout.split("\n\n")

    # iterate over the package info for all installed packages
    for package_info in all_package_info:

        # split single package info into individual lines
        package_info_lines = package_info.split("\n")

        # define a dictionary to map package attributes to their respective key
        package_attrs = dict()

        # iterate over all lines of package info
        for line in package_info_lines:

            # replace multiple consecutive whitespaces with a single whitespace
            line = re.sub(' +', ' ', line)

            # split line by delimiter to get key and value
            attr = str(line).split(" : ")

            if len(attr) == 2:
                key = attr[0]
                value = attr[1]
                package_attrs[key] = value

        # get the package name
        package_name = package_attrs.get(_YumInfoKeys.NAME)

        # add attributes to return value only if a name is found
        if package_name is not None:

            # seed results values
            results[package_name] = {
                _HostDetailsKeys.SASPackageKeys.ATTRIBUTES: dict(),
                _HostDetailsKeys.SASPackageKeys.INSTALLED_FILES: list(),
                _HostDetailsKeys.SASPackageKeys.PROVIDED_SERVICES: list()
            }

            # pull out desired package attributes
            filtered_package_attrs = dict()

            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.ARCH] = \
                package_attrs.get(_YumInfoKeys.ARCH, '')
            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.FROM_REPO] = \
                package_attrs.get(_YumInfoKeys.FROM_REPO, '')
            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.SIZE] = \
                package_attrs.get(_YumInfoKeys.SIZE, '')
            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.SUMMARY] = \
                package_attrs.get(_YumInfoKeys.SUMMARY, '')
            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.VERSION] = \
                package_attrs.get(_YumInfoKeys.VERSION, '') + '-' + package_attrs.get(_YumInfoKeys.RELEASE, '')

            # add package attributes to results
            results[package_name][_HostDetailsKeys.SASPackageKeys.ATTRIBUTES] = filtered_package_attrs

    return results


# =====
# _get_sas_package_info_zypper(AnsibleModule)
# =====
def _get_sas_package_info_zypper(module):
    """
    Retrieves package information via zypper for all installed SAS packages and returns the values as a dict.

    :param AnsibleModule module: The AnsibleModule object representing the current module.
    :return: A dict of package names mapped to a dict containing package attribute names and their values.
    :rtype dict:
    """
    # define results dict
    results = dict()

    # -- package info -- #

    # run package info command
    info_cmd_stdout = _execute_command("zypper -n info $(rpm -qg SAS --queryformat '%{NAME} ')", module)

    # split stdout into an array by empty line, containing package info for all installed packages
    all_package_info = info_cmd_stdout.split("\n\n")[1:]

    # iterate over the package info for all installed packages
    for package_info in all_package_info:

        # split single package info into individual lines
        package_info_lines = package_info.split("\n")[3:]

        # define a dictionary to map package attributes to their respective key
        package_attrs = dict()

        # iterate over all lines of package info
        for line in package_info_lines:

            # replace multiple consecutive whitespaces with a single whitespace
            line = re.sub(' +', ' ', line)

            # split line by delimiter to get key and value
            attr = str(line).split(" : ")

            if len(attr) == 2:
                key = attr[0]
                value = attr[1].strip()
                package_attrs[key] = value

        # get the package name
        package_name = package_attrs.get(_ZypperInfoKeys.NAME)

        # add attributes to return value only if a name is found
        if package_name is not None:
            # seed results values
            results[package_name] = {
                _HostDetailsKeys.SASPackageKeys.ATTRIBUTES: dict(),
                _HostDetailsKeys.SASPackageKeys.INSTALLED_FILES: list(),
                _HostDetailsKeys.SASPackageKeys.PROVIDED_SERVICES: list()
            }

            # pull out desired package attributes
            filtered_package_attrs = dict()

            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.ARCH] = \
                package_attrs.get(_ZypperInfoKeys.ARCH, '')
            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.FROM_REPO] = \
                package_attrs.get(_ZypperInfoKeys.FROM_REPO, '')
            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.SIZE] = \
                package_attrs.get(_ZypperInfoKeys.SIZE, '')
            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.SUMMARY] = \
                package_attrs.get(_ZypperInfoKeys.SUMMARY, '')
            filtered_package_attrs[_HostDetailsKeys.SASPackageKeys.PackageAttributesKeys.VERSION] = \
                package_attrs.get(_ZypperInfoKeys.VERSION, '')

            # add package attributes to results
            results[package_name][_HostDetailsKeys.SASPackageKeys.ATTRIBUTES] = filtered_package_attrs

    return results


# =====
# _execute_command(str, AnsibleModule, bool)
# =====
# def _get_required_software_info(ansible_facts, module):
#    """
#    Retrieves information about software required by SAS and returns a dict of the software's attributes.

#    :param dict ansible_facts:   The *ansible_facts* dict.
#    :param AnsibleModule module: The AnsibleModule object representing the current module.
#    :return: A dict of required software keys mapping to required software attributes.
#    :rtype dict:
#    """

#    results = dict()

#    java_results = {
#        _HostDetailsKeys.RequiredSoftwareKeys.SoftwareAttributesKeys.PATH:
#            _execute_command('which java', module).strip(),
#        _HostDetailsKeys.RequiredSoftwareKeys.SoftwareAttributesKeys.VERSION:
#            _execute_command("java -version 2>&1 | head -n 1 | awk -F '\"' '{print $2}'", module).strip()
#    }

#    results[_HostDetailsKeys.RequiredSoftwareKeys.JAVA] = java_results

#    python_results = {
#        _HostDetailsKeys.RequiredSoftwareKeys.SoftwareAttributesKeys.PATH:
#            ansible_facts[_AnsibleFactsKeys.PYTHON][_AnsibleFactsKeys.PythonKeys.EXEC],
#        _HostDetailsKeys.RequiredSoftwareKeys.SoftwareAttributesKeys.VERSION:
#            ansible_facts[_AnsibleFactsKeys.PYTHON_VERSION]
#    }

#    results[_HostDetailsKeys.RequiredSoftwareKeys.PYTHON] = python_results

#    return results


# =====
# _execute_command(str, AnsibleModule, bool)
# =====
def _execute_command(command, module, shell=True):
    """
    Returns the stdout of the given command.

    :param str command: The command to execute.
    :param AnsibleModule module: The AnsibleModule object representing the current module.
    :param bool shell: (default: True) Whether to use the shell as the program to execute.
    :return: The stdout returned by executing the process or None if an OSError is encountered.
    :rtype str:
    """

    proc = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1)

    try:
        stdout, stderr = proc.communicate()
    except OSError:
        proc.kill()
        stdout, stderr = proc.communicate()
        message = "Command {0} failed.".format(command)
        module.fail_json(msg=message, command_stderr=stderr)

    if proc.returncode != 0:
        message = "Command {0} failed.".format(command)
        module.fail_json(msg=message, command_stderr=stderr)

    return stdout


# =====
# Script entry point
# =====
if __name__ == '__main__':
    main()