Summary:        A collection of modular and reusable compiler and toolchain technologies.
Name:           llvm
Version:        8.0.1
Release:        1%{?dist}
License:        NCSA
URL:            http://lldb.llvm.org
Group:          Development/Tools
Vendor:         VMware, Inc.
Distribution:   Photon
Source0:        http://releases.llvm.org/%{version}/%{name}-%{version}.src.tar.xz
%define sha1    llvm=09964f9eabc364f221a3caefbdaea28557273b4a
BuildRequires:  cmake
BuildRequires:  libxml2-devel
BuildRequires:  libffi-devel
BuildRequires:  python2
Requires:       libxml2

%description
The LLVM Project is a collection of modular and reusable compiler and toolchain technologies. Despite its name, LLVM has little to do with traditional virtual machines, though it does provide helpful libraries that can be used to build them. The name "LLVM" itself is not an acronym; it is the full name of the project.

%package devel
Summary:        Development headers for llvm
Requires:       %{name} = %{version}-%{release}

%description devel
The llvm-devel package contains libraries, header files and documentation
for developing applications that use llvm.

%if "%{_build}" != "%{_host}"
%define cross_compile 1
%endif

%prep
%setup -q -n %{name}-%{version}.src

%build

%if "%{?cross_compile}" != ""

%define cmake_toolchain_file %{_builddir}/%{_arch}-toolchain.cmake
%define llvm_host_install_dir %{_builddir}/LLVMHost

# Configure and build host LLVM for cross compiling
if [ -d %{llvm_host_install_dir} ]
then
    echo "%{llvm_host_install_dir} already exists..."
else
    echo "Building host LLVM..."
    mkdir -p build_host
    cd build_host

    cmake -DCMAKE_INSTALL_PREFIX=/usr           \
          -DLLVM_ENABLE_FFI=ON                  \
          -DCMAKE_BUILD_TYPE=Release            \
          -DLLVM_BUILD_LLVM_DYLIB=ON            \
          -DLLVM_TARGETS_TO_BUILD="host" \
          -DLLVM_INCLUDE_GO_TESTS=No            \
          -Wno-dev ..

    make %{?_smp_mflags}
    make DESTDIR=%{llvm_host_install_dir} install
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

mkdir -p build
cd build

# Configure and build target LLVM
cmake -DCMAKE_INSTALL_PREFIX=/usr           \
      -DLLVM_ENABLE_FFI=ON                  \
      -DCMAKE_BUILD_TYPE=Release            \
      -DLLVM_BUILD_LLVM_DYLIB=ON            \
%ifarch arm
      -DLLVM_TARGETS_TO_BUILD="ARM" \
      -DCMAKE_TOOLCHAIN_FILE=%{cmake_toolchain_file} \
      -DLLVM_TABLEGEN=%{llvm_host_install_dir}/usr/bin/llvm-tblgen \
      -DCMAKE_CROSSCOMPILING=True \
      -DLLVM_DEFAULT_TARGET_TRIPLE=%{_host} \
      -DLLVM_TARGET_ARCH=ARM \
      -DLLVM_TARGETS_TO_BUILD=ARM \
%else
      -DLLVM_TARGETS_TO_BUILD="host;AMDGPU;BPF;ARM" \
%endif
      -DLLVM_INCLUDE_GO_TESTS=No            \
      -Wno-dev ..


make %{?_smp_mflags}
%install
[ %{buildroot} != "/"] && rm -rf %{buildroot}/*
cd build
make DESTDIR=%{buildroot} install

%post   -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%check
# disable security hardening for tests
rm -f $(dirname $(gcc -print-libgcc-file-name))/../specs
cd build
make %{?_smp_mflags} check-llvm

%clean
rm -rf %{buildroot}/*

%files
%defattr(-,root,root)
%{_bindir}/*
%{_libdir}/*.so
%{_libdir}/*.so.*
%dir %{_datadir}/opt-viewer
%{_datadir}/opt-viewer/opt-diff.py
%{_datadir}/opt-viewer/opt-stats.py
%{_datadir}/opt-viewer/opt-viewer.py
%{_datadir}/opt-viewer/optpmap.py
%{_datadir}/opt-viewer/optrecord.py
%{_datadir}/opt-viewer/style.css


%files devel
%{_libdir}/*.a
%{_libdir}/cmake/*
%{_includedir}/*

%changelog
*   Fri Oct 11 2019 Jonathan Chiu <jochi@microsoft.com> 8.0.1-1
-   Update to 8.0.1
*   Wed Jun 26 2019 Keerthana K <keerthanak@vmware.com> 6.0.1-3
-   Enable target BPF
*   Tue Jan 08 2019 Alexey Makhalov <amakhalov@vmware.com> 6.0.1-2
-   Added BuildRequires python2
*   Thu Aug 09 2018 Srivatsa S. Bhat <srivatsa@csail.mit.edu> 6.0.1-1
-   Update to version 6.0.1 to get it to build with gcc 7.3
*   Thu Aug 10 2017 Alexey Makhalov <amakhalov@vmware.com> 4.0.0-3
-   Make check fix
*   Fri Apr 14 2017 Alexey Makhalov <amakhalov@vmware.com> 4.0.0-2
-   BuildRequires libffi-devel
*   Fri Apr 7 2017 Alexey Makhalov <amakhalov@vmware.com> 4.0.0-1
-   Version update
*   Wed Jan 11 2017 Xiaolin Li <xiaolinl@vmware.com>  3.9.1-1
-   Initial build.
