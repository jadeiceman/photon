Summary:        Security client
Name:           nss
Version:        3.39
Release:        1%{?dist}
License:        MPLv2.0
URL:            http://ftp.mozilla.org/pub/security/nss/releases/NSS_3_47_RTM/src/%{name}-%{version}.tar.gz
Group:          Applications/System
Vendor:         VMware, Inc.
Distribution:   Photon
Source0:        %{name}-%{version}.tar.gz
%define sha1    nss=351e0e9607ead50174efe5f5107e2dc97e7358f2
Patch:          nss-standalone-1.patch
Requires:       nspr
BuildRequires:  nspr-devel
BuildRequires:  sqlite-devel
Requires:       nss-libs = %{version}-%{release}

%description
 The Network Security Services (NSS) package is a set of libraries
 designed to support cross-platform development of security-enabled
 client and server applications. Applications built with NSS can
 support SSL v2 and v3, TLS, PKCS #5, PKCS #7, PKCS #11, PKCS #12,
 S/MIME, X.509 v3 certificates, and other security standards.
 This is useful for implementing SSL and S/MIME or other Internet
 security standards into an application.

%package devel
Summary: Development Libraries for Network Security Services
Group: Development/Libraries
Requires: nspr-devel
Requires: nss = %{version}-%{release}
%description devel
Header files for doing development with Network Security Services.

%package libs
Summary: Libraries for Network Security Services
Group:      System Environment/Libraries
Requires:   sqlite-libs
Requires:   nspr
%description libs
This package contains minimal set of shared nss libraries.

%prep
%setup -q
%patch -p1
%build
export CC="%{_host}-gcc"
export CCC="%{_host}-g++"
export AR="%{_host}-ar"
export AS="%{_host}-as"
export RANLIB="%{_host}-ranlib"
export LD="%{_host}-ld"
export STRIP="%{_host}-strip"

cd nss
# -j is not supported by nss
make VERBOSE=1 BUILD_OPT=1 \
    NSPR_INCLUDE_DIR=%{_includedir}/nspr \
    USE_SYSTEM_ZLIB=1 \
    ZLIB_LIBS=-lz \
%if "%{?cross_compile}" != ""
    NATIVE_CC=cc \
    CROSS_COMPILE=1 \
%endif
%ifarch arm %{arm}
    OS_TEST=arm \
%else
    USE_64=1 \
%endif
    $([ -f %{_includedir}/sqlite3.h ] && echo NSS_USE_SYSTEM_SQLITE=1)
%install
cd nss
cd ../dist
install -vdm 755 %{buildroot}%{_bindir}
install -vdm 755 %{buildroot}%{_includedir}/nss
install -vdm 755 %{buildroot}%{_libdir}
install -v -m755 Linux*/lib/*.so %{buildroot}%{_libdir}
%if "%{?cross_compile}" != ""
install -v -m644 Linux*/lib/libcrmf.a %{buildroot}%{_libdir}
%else
install -v -m644 Linux*/lib/{*.chk,libcrmf.a} %{buildroot}%{_libdir}
%endif
cp -v -RL {public,private}/nss/* %{buildroot}%{_includedir}/nss
chmod 644 %{buildroot}%{_includedir}/nss/*
install -v -m755 Linux*/bin/{certutil,nss-config,pk12util} %{buildroot}%{_bindir}
install -vdm 755 %{buildroot}%{_libdir}/pkgconfig
install -vm 644 Linux*/lib/pkgconfig/nss.pc %{buildroot}%{_libdir}/pkgconfig

%check
cd nss/tests
chmod g+w . -R
useradd test -G root -m
HOST=localhost DOMSUF=localdomain BUILD_OPT=1
sudo -u test ./all.sh && userdel test -r -f

%post   -p /sbin/ldconfig

%files
%defattr(-,root,root)
%{_bindir}/*
%if "%{?cross_compile}" == ""
%{_libdir}/*.chk
%endif
%{_libdir}/*.so
%exclude %{_libdir}/libfreeblpriv3.so
%exclude %{_libdir}/libnss3.so
%exclude %{_libdir}/libnssutil3.so
%exclude %{_libdir}/libsoftokn3.so

%files devel
%{_includedir}/*
%{_libdir}/*.a
%{_libdir}/pkgconfig/*.pc

%files libs
%{_libdir}/libfreeblpriv3.so
%{_libdir}/libnss3.so
%{_libdir}/libnssutil3.so
%{_libdir}/libsoftokn3.so

%changelog
*   Mon Sep 10 2018 Him Kalyan Bordoloi <bordoloih@vmware.com> 3.39-1
-   Upgrade to 3.39.
*   Thu Dec 07 2017 Alexey Makhalov <amakhalov@vmware.com> 3.31-5
-   Add static libcrmf.a library to devel package
*   Tue Nov 14 2017 Alexey Makhalov <amakhalov@vmware.com> 3.31-4
-   Aarch64 support
*   Fri Jul 07 2017 Vinay Kulkarni <kulkarniv@vmware.com> 3.31-3
-   Fix buildrequires.
*   Thu Jun 29 2017 Xiaolin Li <xiaolinl@vmware.com> 3.31-2
-   Fix check.
*   Tue Jun 20 2017 Xiaolin Li <xiaolinl@vmware.com> 3.31-1
-   Upgrade to 3.31.
*   Sat Apr 15 2017 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 3.30.1-1
-   Update to 3.30.1
*   Fri Apr 14 2017 Alexey Makhalov <amakhalov@vmware.com> 3.25-4
-   Added libs subpackage to reduce tdnf dependent tree
*   Wed Nov 16 2016 Alexey Makhalov <amakhalov@vmware.com> 3.25-3
-   Use sqlite-libs as runtime dependency
*   Mon Oct 04 2016 ChangLee <changLee@vmware.com> 3.25-2
-   Modified %check
*   Tue Jul 05 2016 Anish Swaminathan <anishs@vmware.com> 3.25-1
-   Upgrade to 3.25
*   Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 3.21-2
-   GA - Bump release of all rpms
*   Thu Jan 21 2016 Xiaolin Li <xiaolinl@vmware.com> 3.21
-   Updated to version 3.21
*   Tue Aug 04 2015 Kumar Kaushik <kaushikk@vmware.com> 3.19-2
-   Version update. Firefox requirement.
*   Fri May 29 2015 Alexey Makhalov <amakhalov@vmware.com> 3.19-1
-   Version update. Firefox requirement.
*   Wed Nov 5 2014 Divya Thaluru <dthaluru@vmware.com> 3.15.4-1
-   Initial build. First version
