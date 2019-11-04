%global debug_package %{nil}
%global __os_install_post %{nil}
%global _firmwarepath    /lib/firmware
%define _binaries_in_noarch_packages_terminate_build   0

Summary:	Linux Firmware
Name:		linux-firmware
Version:	20191030
Release:	1%{?dist}
License:	GPL+ and GPLv2+ and MIT and Redistributable, no modification permitted
URL:		http://www.kernel.org/
Group:		System Environment/Kernel
Vendor:		VMware, Inc.
Distribution:	Photon
Source0:        %{name}-%{version}.tar.gz
%define sha1 linux=4bcee0f22979c415bbe5c4fe90aa70abc0eea893
BuildArch:	noarch

%description
This package includes firmware files required for some devices to operate.

%prep
%setup -q

%build

%install
mkdir -p %{buildroot}%{_firmwarepath}
# Copy entire tree as is
cp -r * %{buildroot}%{_firmwarepath}

%files
%defattr(-,root,root)
%{_firmwarepath}/*

%changelog
*   Thu Oct 24 2019 Ajay Kaher <akaher@vmware.com> 20191030-1
-   Added Dell 5K Gateway firmware.
*   Fri Aug 30 2019 Alexey Makhalov <amakhalov@vmware.com> 20190830-1
-   Added ath10k firmware for ls1046a.
*   Tue Feb 05 2019 Alexey Makhalov <amakhalov@vmware.com> 20190205-1
-   Added ath10k firmware (for ls1012a).
-   Use 1:1 folder layout for ppfe firmware.
*   Wed Jan 09 2019 Alexey Makhalov <amakhalov@vmware.com> 20190109-1
-   Added Compulab Fitlet2 firmware.
*   Thu Nov 29 2018 Srinidhi Rao <srinidhir@vmware.com> 20181129-1
-   Updated pfe firmware files for NXP LS1012A FRWY board
*   Wed Oct 10 2018 Ajay Kaher <akaher@vmware.com> 20181010-1
-   Updated brcm firmwares for Rpi B and Rpi B+
*   Thu Aug 23 2018 Alexey Makhalov <amakhalov@vmware.com> 20180823-1
-   Initial version. RPi3 and Dell Edge Gateway 3001 support.
