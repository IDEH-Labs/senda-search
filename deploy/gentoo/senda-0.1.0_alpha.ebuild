# Copyright 2026 IDEH Labs
# Distributed under the terms of the GNU General Public License v3 or later
# SPDX-License-Identifier: GPL-3.0-or-later

EAPI=8

PYTHON_COMPAT=( python3_12 python3_13 python3_14 )
DISTUTILS_USE_PEP517=setuptools

inherit distutils-r1 systemd

DESCRIPTION="Senda — The independent, ethical, and sovereign web search engine"
HOMEPAGE="https://codeberg.org/IDEH-Labs/senda-search"
SRC_URI="https://codeberg.org/IDEH-Labs/senda-search/archive/v${PV/_alpha/-alpha}.tar.gz -> ${P}.tar.gz"

LICENSE="GPL-3+"
SLOT="0"
KEYWORDS="~amd64 ~arm64 ~x86"
IUSE="test"
RESTRICT="!test? ( test )"

RDEPEND="
	dev-db/sqlite[secure-delete]
	>=dev-python/fastapi-0.115[${PYTHON_USEDEP}]
	>=dev-python/uvicorn-0.30[${PYTHON_USEDEP}]
	>=dev-python/httpx-0.27[${PYTHON_USEDEP}]
	>=dev-python/beautifulsoup4-4.12[${PYTHON_USEDEP}]
	>=dev-python/pydantic-2.8[${PYTHON_USEDEP}]
	>=dev-python/pydantic-settings-2.4[${PYTHON_USEDEP}]
	>=dev-python/jinja2-3.1[${PYTHON_USEDEP}]
"
BDEPEND="
	test? (
		>=dev-python/pytest-8[${PYTHON_USEDEP}]
		>=dev-python/pytest-asyncio-0.24[${PYTHON_USEDEP}]
		>=dev-python/pytest-cov-5[${PYTHON_USEDEP}]
	)
"

distutils_enable_tests pytest

src_install() {
	distutils-r1_src_install

	# Install OpenRC service and configuration
	newinitd deploy/openrc/senda senda
	newconfd deploy/openrc/senda.conf senda

	# Install systemd unit
	systemd_dounit deploy/systemd/senda.service

	# Create data directory with restricted permissions
	keepdir /var/lib/senda/data
	fowners -R nobody:nobody /var/lib/senda
	fperms 0750 /var/lib/senda
}
