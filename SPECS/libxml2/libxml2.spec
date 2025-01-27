%{!?python2_sitelib: %define python2_sitelib %(python2 -c "from distutils.sysconfig import get_python_lib;print(get_python_lib())")}
%{!?python3_sitelib: %define python3_sitelib %(python3 -c "from distutils.sysconfig import get_python_lib;print(get_python_lib())")}

%{!?python2_inc: %define python2_inc %(python2 -c "from distutils.sysconfig import get_python_inc;print(get_python_inc())")}
%{!?python3_inc: %define python3_inc %(python3 -c "from distutils.sysconfig import get_python_inc;print(get_python_inc())")}

%if "%{_build}" != "%{_host}"
%define __strip %{_host}-strip
%define __objdump %{_host}-objdump
%define cross_compile 1
%else
%define cross_compile 0
%endif

Summary:        Libxml2
Name:           libxml2
Version:        2.9.8
Release:        2%{?dist}
License:        MIT
URL:            http://xmlsoft.org/
Group:          System Environment/General Libraries
Vendor:         VMware, Inc.
Distribution:   Photon
Source0:        ftp://xmlsoft.org/libxml2/%{name}-%{version}.tar.gz
Patch0:         Fix_nullptr_deref_with_XPath_logic_ops.patch
Patch1:         custom_python_params.patch
Patch2:         libtool-2.4.6-fixinstall_trailingslash.patch
%define sha1    libxml2=66bcefd98a6b7573427cf66f9d3841b59eb5b8c3
BuildRequires:  python2-devel
BuildRequires:  python2-libs
BuildRequires:  python3-devel
Provides:       pkgconfig(libxml-2.0)

%description
The libxml2 package contains libraries and utilities used for parsing XML files.

%package python
Summary:        The libxml2 python module
Group:          Development/Languages/Python
Requires:       %{name} = %{version}
Requires:       python2
Requires:       python2-libs

%description    python
The libxml2 python module

%package -n     python3-libxml2
Summary:        Python 3 bindings for libxml2.
Group:          Development/Libraries
Requires:       %{name} = %{version}
Requires:       python3

%description -n python3-libxml2
Python3 libxml2.

%package devel
Summary:    Libraries and header files for libxml
Requires:   %{name} = %{version}

%description devel
Static libraries and header files for the support library for libxml

%prep
%setup -q
%patch0 -p1
%patch1 -p1

%build
# Rebuild configure so that PYTHON_INCLUDES can be defined externally
autoreconf configure.ac
%ifarch arm %{arm}
export PYTHON_CROSS_PREFIX=/target-%{_arch}
%endif

%configure \
    --disable-static \
    --with-history

make %{?_smp_mflags}

# Patch libtool
patch libtool < %{_sourcedir}/libtool-2.4.6-fixinstall_trailingslash.patch

%install
[ %{buildroot} != "/"] && rm -rf %{buildroot}/*
make DESTDIR=%{buildroot} install
find %{buildroot}/%{_libdir} -name '*.la' -delete
%{_fixperms} %{buildroot}/*

make clean

%ifarch arm %{arm}
export PYTHON_CROSS_PREFIX=/target-%{_arch}
%endif

%configure \
    --disable-static \
    --with-python=/usr/bin/python3
make %{?_smp_mflags}

# Patch again
patch libtool < %{_sourcedir}/libtool-2.4.6-fixinstall_trailingslash.patch
make install DESTDIR=%{buildroot}

%check
make %{?_smp_mflags} check

%post   -p /sbin/ldconfig
%postun -p /sbin/ldconfig
%clean
rm -rf %{buildroot}/*
%files
%defattr(-,root,root)
%{_docdir}/*
%{_libdir}/libxml*
%{_libdir}/xml2Conf.sh
%{_bindir}/*
%{_datadir}/aclocal/*
%{_datadir}/gtk-doc/*
%{_mandir}/man1/*

%files python
%defattr(-,root,root)
%{python2_sitelib}/*

%files -n python3-libxml2
%defattr(-,root,root)
%{python3_sitelib}/*

%files devel
%defattr(-,root,root)
%{_includedir}/*
%{_mandir}/man3/*
%{_libdir}/pkgconfig/libxml-2.0.pc
%{_libdir}/cmake/libxml2/libxml2-config.cmake

%changelog
*   Fri Dec 07 2018 Dweep Advani <dadvani@vmware.com> 2.9.8-2
-   Fix CVE-2018-14404 and improve build and install sections
*   Tue Sep 11 2018 Keerthana K <keerthanak@vmware.com> 2.9.8-1
-   Update to version 2.9.8
*   Mon Feb 12 2018 Xiaolin Li <xiaolinl@vmware.com> 2.9.7-1
-   Update to version 2.9.7
*   Wed Oct 18 2017 Xiaolin Li <xiaolinl@vmware.com> 2.9.6-1
-   Update to version 2.9.6
*   Mon Oct 2 2017 Anish Swaminathan <anishs@vmware.com> 2.9.4-12
-   Remove call to _PyVerify_fd
*   Wed Aug 09 2017 Dheeraj Shetty <dheerajs@vmware.com> 2.9.4-11
-   Apply patch for CVE-2017-8872
*   Mon Aug 07 2017 Danut Moraru <dmoraru@vmware.com> 2.9.4-10
-   Change expected parsing error for test for upstream bug 781205 introduced by CVE-2017-9049
*   Mon Jul 10 2017 Divya Thaluru <dthaluru@vmware.com> 2.9.4-9
-   Apply patch for CVE-2017-9047, CVE-2017-9048, CVE-2017-9049 and CVE-2017-9050
*   Thu May 18 2017 Xiaolin Li <xiaolinl@vmware.com> 2.9.4-8
-   Move python2 requires to python subpackage.
*   Wed Apr 26 2017 Siju Maliakkal <smaliakkal@vmware.com> 2.9.4-7
-   Modified python3 version in configure
*   Thu Apr 13 2017 Xiaolin Li <xiaolinl@vmware.com> 2.9.4-6
-   Added python3-libxml2 package.
*   Tue Jan 3 2017 Alexey Makhalov <amakhalov@vmware.com> 2.9.4-5
-   Fix for CVE-2016-9318
*   Wed Dec 07 2016 Xiaolin Li <xiaolinl@vmware.com> 2.9.4-4
-   Moved man3 to devel subpackage.
*   Thu Oct 20 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 2.9.4-3
-   Apply patch for CVE-2016-5131
*   Mon Oct 03 2016 Chang Lee <changlee@vmware.com> 2.9.4-2
-   Modified check
*   Wed Jun 01 2016 Anish Swaminathan <anishs@vmware.com> 2.9.4-1
-   Upgrade to 2.9.4
*   Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 2.9.3-2
-   GA - Bump release of all rpms
*   Tue Feb 23 2016 Harish Udaiya Kumar <hudaiyakumar@vmware.com> 2.9.3-1
-   Upgraded to version 2.9.3
*   Thu Jan 28 2016 Xiaolin Li <xiaolinl@vmware.com> 2.9.2-1
-   Downgrade to version 2.9.2
-   libxml 2.9.3 has been found to have major functional issues.
-   Until these are resolved, please roadmap updating to 2.9.2.
*   Wed Dec 2 2015 Xiaolin Li <xiaolinl@vmware.com> 2.9.3-1
-   Update to version 2.9.3
*   Thu Jul 2 2015 Mahmoud Bassiouny <mbassiouny@vmware.com> 2.9.1-3
-   Seperate the python module from the main library
*   Thu Jun 11 2015 Alexey Makhalov <amakhalov@vmware.com> 2.9.1-2
-   Moved 'Provides: pkgconfig(...)' into base package
*   Mon Oct 13 2014 Divya Thaluru <dthaluru@vmware.com> 2.9.1-1
-   Initial build.  First version
