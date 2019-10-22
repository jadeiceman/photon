%ifarch arm
%global _lib64dir %{_libdir}
%endif

Summary:	Google's C++ gtest framework
Name:		gtest
Version:	1.8.1
Release:	2%{?dist}
License:	ASL 2.0
URL:		https://github.com/google/googletest
Source0:	https://github.com/google/googletest/archive/googletest-%{version}.tar.gz
%define sha1 googletest=152b849610d91a9dfa1401293f43230c2e0c33f8
Group:		Development/Tools
Vendor:		VMware, Inc.
Distribution: 	Photon
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  cmake
BuildRequires:  make
BuildRequires:  gcc

%description
Google's C++ test framework that combines the GoogleTest and GoogleMock projects. This package provides gtest shared libraries.

%package devel
Summary:        libgtest headers
Group:          Development/Tools
%description devel
This contains libgtest header files.

%package static
Summary:        libgtest static lib
Group:          Development/Tools
%description static
This contains libgtest static library.

%package -n gmock
Summary: Google's C++ gmock framework
Group: Development/Tools
%description -n gmock
Google's C++ test framework that combines the GoogleTest and GoogleMock projects. This package provides gmock shared libraries.

%package -n gmock-devel
Summary:        libgmock headers
Group:          Development/Tools
%description -n gmock-devel
This contains libgmock header files.

%package -n gmock-static
Summary:        libgtest static lib
Group:          Development/Tools
%description -n gmock-static
This contains libgmock static library.


%prep
%setup -n googletest-release-%{version}

%build
%ifarch arm
%define cmake_toolchain_file %{_builddir}/%{_arch}-toolchain.cmake

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

%endif

cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DBUILD_SHARED_LIBS=OFF -DCMAKE_TOOLCHAIN_FILE=%{?cmake_toolchain_file} .
make
cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DBUILD_SHARED_LIBS=ON -DCMAKE_TOOLCHAIN_FILE=%{?cmake_toolchain_file} .
make

%install
make DESTDIR=%{buildroot} install
install -p -m 644 -t %{buildroot}/%{_lib64dir} googlemock/libgmock.a
install -p -m 644 -t %{buildroot}/%{_lib64dir} googlemock/libgmock_main.a
install -p -m 644 -t %{buildroot}/%{_lib64dir} googlemock/gtest/libgtest.a
install -p -m 644 -t %{buildroot}/%{_lib64dir} googlemock/gtest/libgtest_main.a
install -vdm 755 %{buildroot}/usr/src/gtest/src/
install -vdm 755 %{buildroot}/usr/src/gmock/src/
cp googletest/src/* %{buildroot}/usr/src/gtest/src/
cp googlemock/src/* %{buildroot}/usr/src/gmock/src/
find %{buildroot} -name '*.la' -delete

%files
%defattr(-,root,root)
%{_lib64dir}/libgtest.so
%{_lib64dir}/libgtest_main.so

%files -n gmock
%{_lib64dir}/libgmock.so
%{_lib64dir}/libgmock_main.so

%files devel
%defattr(-,root,root)
%{_includedir}/gtest/*
/usr/src/gtest/
%{_lib64dir}/cmake/GTest/*.cmake
%{_lib64dir}/pkgconfig/*.pc

%files -n gmock-devel
%{_includedir}/gmock/*
/usr/src/gmock/

%files -n gmock-static
%defattr(-,root,root)
%{_lib64dir}/libgmock.a
%{_lib64dir}/libgmock_main.a

%files static
%defattr(-,root,root)
%{_lib64dir}/libgtest.a
%{_lib64dir}/libgtest_main.a

%changelog
*    Sun Sep 23 2018 Sharath George <anishs@vmware.com> 1.8.1-2
-    Add gmock subpackage
*    Wed Sep 12 2018 Anish Swaminathan <anishs@vmware.com> 1.8.1-1
-    Update version to 1.8.1
*    Thu May 04 2017 Anish Swaminathan <anishs@vmware.com> 1.8.0-2
-    Add gtest sources in devel package
*    Mon Apr 10 2017 Vinay Kulkarni <kulkarniv@vmware.com> 1.8.0-1
-    Initial version of libgtest package for Photon.
