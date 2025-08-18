# Copyright 2025 The StackStorm Authors.

# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional pkg_information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import http.client

import requests
import semver

from st2common import log as logging
from st2common.runners.base_action import Action

__all__ = ["ListPackagesAction"]

LOG = logging.getLogger(__name__)

BASE_URL = "https://%(api_token)s:@packagecloud.io/api/v1/repos/%(repo)s/packages.json"
MAX_PAGE_NUMBER = 100


def format_semver(version, release):
    """
    format_semver() removes "dev" from :version: and replaces it
    with ".0".  This ensures semver's parse() function produces an object
    that can be compared correctly with Python's sorted() function.

    The version field in Packagecloud's package metadata has an
    inconsistent format.  The two formats are shown below:
        "version": "3.9dev-8", "release": "8"
        "version": "3.9dev", "release": "8"

    The trailing "-8" is also dropped when "dev" is removed.

    The :release: argument is appended to the resulting version string
    in the form "+8" which semver parses as the build field.
    """
    if "dev" in version:
        # Figure out what we should replace "dev" with
        if version[version.index("dev") - 1] == ".":
            suffix = "0-beta"
        else:
            suffix = ".0-beta"

        # Rewrite to contain only text before "dev" plus the new suffix
        version = version[: version.index("dev")] + suffix

    return f"{version}+{release}"


def meta_version_to_integer(version, release):
    """
    Despite semver comparing major, minor, and patch numerically, the
    release (aka semver.build) is treated as a string which causes incorrect
    sorting.  A bit wise shift is used to calculate a single numerical
    value for all four version attributes so sorted() performs the ordering
    correctly. 8 bit shift for 256 major/minor/patch leaving 16bits for 65535 build.
    """
    v = semver.Version.parse(format_semver(version, release))
    return (v.major << 32) + (v.minor << 24) + (v.patch << 16) + int(v.build)


class ListPackagesAction(Action):
    def run(
        self,
        repo,
        package,
        distro_version,
        version,
        release,
        api_token,
        per_page=200,
        sort_packages=True,
        sort_type="descending",
    ):
        params = {"per_page": per_page}
        values = {"repo": repo, "api_token": api_token}
        url = BASE_URL % values

        page = 1
        metadata = []

        while page < MAX_PAGE_NUMBER:
            page_url = url + "?page=" + str(page)
            response = requests.get(url=page_url, params=params)

            if response.status_code != http.client.OK:  # pylint: disable=no-member
                raise Exception(response.text)

            metadata += response.json()

            if len(metadata) >= int(response.headers.get("Total", 0)):
                break

            page += 1
        LOG.debug("Processed %s page(s).", page)

        # Filter package list based on package property arguments.
        packages = []
        for pkg_info in metadata:
            if package and pkg_info["name"] != package:
                continue
            if distro_version and pkg_info["distro_version"] != distro_version:
                continue
            if version and not pkg_info["version"].startswith(version):
                continue
            if release and pkg_info["release"] != release:
                continue
            packages.append(pkg_info)

        if sort_packages:
            reverse = sort_type == "descending"
            return sorted(
                packages,
                key=lambda pkgmeta: (meta_version_to_integer(pkgmeta["version"], pkgmeta["release"])),
                reverse=reverse,
            )

        return packages
