Summary:	Cmake-3.12.1
Name:		cmake
Version:	3.12.1
Release:	4%{?dist}
License:	BSD and LGPLv2+
URL:		http://www.cmake.org/
Source0:	http://www.cmake.org/files/v3.12/%{name}-%{version}.tar.gz
%define sha1 cmake=5359cd2e36051b0746580298d42518b0aef27979
Source1:	macros.cmake
Patch0:         disableUnstableUT.patch
Group:		Development/Tools
Vendor:		VMware, Inc.
Distribution:	Photon
BuildRequires:	ncurses-devel
BuildRequires:  xz
BuildRequires:  xz-devel
BuildRequires:  curl
BuildRequires:  curl-devel
BuildRequires:  expat-libs
BuildRequires:  expat-devel
BuildRequires:  zlib
BuildRequires:  zlib-devel
BuildRequires:  libarchive
BuildRequires:  libarchive-devel
BuildRequires:  bzip2
BuildRequires:  bzip2-devel
Requires:	ncurses
Requires:       expat
Requires:       zlib
Requires:       libarchive
Requires:       bzip2
%description
CMake is an extensible, open-source system that manages the build process in an
operating system and in a compiler-independent manner.

%define cmake_host_install_dir %{_builddir}/CMakeHost
%define cmake_toolchain_file %{_builddir}/%{_arch}-toolchain.cmake

%prep
%setup -q
%patch0 -p1
%build
if [ -d %{cmake_host_install_dir} ]
then
    echo "%{cmake_host_install_dir} exists..."
else
# Bootstrap and make CMake for host
%if %{?cross_compile}
    ncores="$(/usr/bin/getconf _NPROCESSORS_ONLN)"
    mkdir -p build_host
    cd build_host
    ../bootstrap --prefix=%{_prefix} --system-expat --system-zlib --system-libarchive --system-bzip2 --parallel=$ncores
    make %{?_smp_mflags}
    make DESTDIR=%{cmake_host_install_dir} install
    cd ..
%endif
fi

# Create toolchain file for cross compile
rm -f %{cmake_toolchain_file}
cat << EOF >> %{cmake_toolchain_file}
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR %{_arch})

set(CMAKE_SYSROOT /target-%{_arch})

set(CMAKE_C_COMPILER %{_bindir}/%{_host}-gcc)
set(CMAKE_CXX_COMPILER %{_bindir}/%{_host}-g++)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
EOF

# Configure CMake
CMAKE_OPTS="\
    -D CMAKE_TOOLCHAIN_FILE=%{cmake_toolchain_file} \
    -D CMAKE_INSTALL_PREFIX=%{_prefix} \
    -D HAVE_POSIX_STRERROR_R=1 \
    --debug-trycompile \
"
%{cmake_host_install_dir}/%{_bindir}/cmake $CMAKE_OPTS . || \
%{cmake_host_install_dir}/%{_bindir}/cmake $CMAKE_OPTS .

make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install
find %{buildroot} -name '*.la' -delete
install -Dpm0644 %{SOURCE1} %{buildroot}%{_libdir}/rpm/macros.d/macros.cmake

%check
make  %{?_smp_mflags} test

%files
%defattr(-,root,root)
/usr/share/%{name}-*/*
%{_bindir}/*
/usr/doc/%{name}-*/*
/usr/share/aclocal/*
%{_libdir}/rpm/macros.d/macros.cmake

%changelog
*       Thu Jan 17 2019 Ankit Jain <ankitja@vmware.com> 3.12.1-4
-       Removed unnecessary libgcc-devel buildrequires
*       Thu Dec 06 2018 <ashwinh@vmware.com> 3.12.1-3
-       Bug Fix 2243672. Add system provided libs.
*       Sun Sep 30 2018 Bo Gan <ganb@vmware.com> 3.12.1-2
-       smp make (make -jN)
-       specify /usr/lib as CMAKE_INSTALL_LIBDIR
*       Fri Sep 07 2018 Ajay Kaher <akaher@vmware.com> 3.12.1-1
-       Upgrading version to 3.12.1
-       Adding macros.cmake
*       Fri Sep 29 2017 Kumar Kaushik <kaushikk@vmware.com> 3.8.0-4
-       Building using system expat libs.
*       Thu Aug 17 2017 Kumar Kaushik <kaushikk@vmware.com> 3.8.0-3
-       Fixing make check bug # 1632102.
*	Tue May 23 2017 Harish Udaiya Kumar <hudaiyakumar@vmware.com> 3.8.0-2
-	bug 1448414: Updated to build in parallel
*       Fri Apr 07 2017 Anish Swaminathan <anishs@vmware.com>  3.8.0-1
-       Upgrade to 3.8.0
*       Thu Oct 06 2016 ChangLee <changlee@vmware.com> 3.4.3-3
-       Modified %check
*	Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 3.4.3-2
-	GA - Bump release of all rpms
*       Thu Feb 25 2016 Kumar Kaushik <kaushikk@vmware.com> 3.4.3-1
-       Updated version.
*       Wed May 20 2015 Touseef Liaqat <tliaqat@vmware.com> 3.2.1.2
-       Updated group.
*	Mon Apr 6 2015 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 3.2.1-1
-	Update to 3.2.1
*	Tue Nov 25 2014 Divya Thaluru <dthaluru@vmware.com> 3.0.2-1
-	Initial build. First version
