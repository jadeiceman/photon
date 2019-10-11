Summary:        C, C++, Objective C and Objective C++ front-end for the LLVM compiler.
Name:           clang
Version:        6.0.1
Release:        1%{?dist}
License:        NCSA
URL:            http://clang.llvm.org
Group:          Development/Tools
Vendor:         VMware, Inc.
Distribution:   Photon
Source0:        http://releases.llvm.org/%{version}/cfe-%{version}.src.tar.xz
%define sha1    cfe=d93d8f3e3d7eb549ac58507383f7fcbdd78804d7
BuildRequires:  cmake
BuildRequires:  llvm-devel = %{version}
BuildRequires:  ncurses-devel
BuildRequires:  zlib-devel
BuildRequires:  libxml2-devel
BuildRequires:  python2-devel
Requires:       libstdc++-devel
Requires:       ncurses
Requires:       llvm
Requires:       zlib
Requires:       libxml2
Requires:       python2

%description
The goal of the Clang project is to create a new C based language front-end: C, C++, Objective C/C++, OpenCL C and others for the LLVM compiler. You can get and build the source today.

%package devel
Summary:        Development headers for clang
Requires:       %{name} = %{version}-%{release}

%description devel
The clang-devel package contains libraries, header files and documentation
for developing applications that use clang.

%prep
%setup -q -n cfe-%{version}.src

%build
%if "%{?cross_compile}" != ""

%define cmake_toolchain_file %{_builddir}/%{_arch}-toolchain.cmake
%define host_install_dir %{_builddir}/ClangHost

# Configure and build host Clang for cross compiling
if [ -d %{host_install_dir} ]
then
    echo "%{host_install_dir} already exists..."
else
    echo "Building host %{name}..."
    mkdir -p build_host
    cd build_host

    cmake -DCMAKE_INSTALL_PREFIX=/usr           \
          -DCMAKE_BUILD_TYPE=Release            \
          -Wno-dev ..

    make %{?_smp_mflags}
    make DESTDIR=%{host_install_dir} install
    cd ..
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

%endif

%ifarch arm
#sed -i 's=include_directories("${LLVM_BINARY_DIR}/include" "${LLVM_MAIN_INCLUDE_DIR}")=include_directories("/target-%{_arch}/${LLVM_BINARY_DIR}/include" "/target-%{_arch}/${LLVM_MAIN_INCLUDE_DIR}")=g' CMakeLists.txt

#sed -i 's=link_directories("${LLVM_LIBRARY_DIR}")=link_directories("/target-arm/${LLVM_LIBRARY_DIR}")=g' CMakeLists.txt
%endif

mkdir -p build
cd build

cmake -DCMAKE_INSTALL_PREFIX=/usr   \
      -DCMAKE_BUILD_TYPE=Release    \
%ifarch arm
      -DCMAKE_TOOLCHAIN_FILE=%{cmake_toolchain_file} \
      -DCLANG_TABLEGEN=%{host_install_dir}/usr/bin/clang-tblgen \
%endif
      -Wno-dev ..

make %{?_smp_mflags}

%install
[ %{buildroot} != "/"] && rm -rf %{buildroot}/*
cd build
make DESTDIR=%{buildroot} install

%post   -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%check
cd build
make clang-check

%clean
rm -rf %{buildroot}/*

%files
%defattr(-,root,root)
%{_bindir}/*
%{_libexecdir}/*
%{_libdir}/*.so.*
%{_datadir}/*

%files devel
%defattr(-,root,root)
%{_libdir}/*.so
%{_libdir}/*.a
%{_libdir}/cmake/*
%{_libdir}/clang/*
%{_includedir}/*

%changelog
*   Thu Aug 09 2018 Srivatsa S. Bhat <srivatsa@csail.mit.edu> 6.0.1-1
-   Update to version 6.0.1 to get it to build with gcc 7.3
*   Wed Jun 28 2017 Chang Lee <changlee@vmware.com> 4.0.0-2
-   Updated %check
*   Fri Apr 7 2017 Alexey Makhalov <amakhalov@vmware.com> 4.0.0-1
-   Version update
*   Wed Jan 11 2017 Xiaolin Li <xiaolinl@vmware.com>  3.9.1-1
-   Initial build.
