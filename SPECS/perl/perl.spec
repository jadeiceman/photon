%global __provides_exclude %{?__provides_exclude:%__provides_exclude|}^perl\\((VMS|Win32|BSD::|DB\\)$)
# unicore::Name - it's needed by perl, maybe problem of rpm
# FCGI is external dependency after install of perl-CGI, remove it during RC releases
%global __requires_exclude %{?__requires_exclude:%__requires_exclude|}^perl\\((VMS|BSD::|Win32|Tk|Mac::|Your::Module::Here|unicore::Name|FCGI)
# Filter dependencies on private modules. Generator:
# for F in $(find lib -type f); do perl -e '$/ = undef; $_ = <>; if (/^package #\R([\w:]*);/m) { print qq{|^perl\\\\($1\\\\)} }' "$F"; done
%global __requires_exclude %{?__requires_exclude:%__requires_exclude|}^perl\\(Locale::Codes::Country_Retired\\)|^perl\\(Locale::Codes::LangFam_Retired\\)|^perl\\(Locale::Codes::Script_Retired\\)|^perl\\(Locale::Codes::LangExt_Codes\\)|^perl\\(Locale::Codes::LangFam_Codes\\)|^perl\\(Locale::Codes::Script_Codes\\)|^perl\\(Locale::Codes::Language_Codes\\)|^perl\\(Locale::Codes::LangExt_Retired\\)|^perl\\(Locale::Codes::Currency_Codes\\)|^perl\\(Locale::Codes::LangVar_Retired\\)|^perl\\(Locale::Codes::Language_Retired\\)|^perl\\(Locale::Codes::Country_Codes\\)|^perl\\(Locale::Codes::LangVar_Codes\\)|^perl\\(Locale::Codes::Currency_Retired\\)

%define perl_cross_version 1.3

Summary:        Practical Extraction and Report Language
Name:           perl
Version:        5.28.0
Release:        2%{?dist}
License:        GPLv1+
URL:            http://www.perl.org/
Group:          Development/Languages
Vendor:         VMware, Inc.
Distribution:   Photon
Source0:        http://www.cpan.org/src/5.0/%{name}-%{version}.tar.gz
%define sha1    perl=0622f86160e8969633cbd21a2cca9e11ae1f8c5a
Source1:        https://github.com/arsv/perl-cross/releases/download/%{perl_cross_version}/perl-cross-%{perl_cross_version}.tar.gz
%define sha1    perl=0622f86160e8969633cbd21a2cca9e11ae1f8c5a
Provides:       perl >= 0:5.003000
Provides:       perl(getopts.pl)
Provides:       perl(s)
Provides:       /bin/perl
BuildRequires:  zlib-devel
BuildRequires:  bzip2-devel
BuildRequires:  gdbm-devel
Requires:       zlib
Requires:       gdbm
Requires:       glibc
Requires:       libgcc
%description
The Perl package contains the Practical Extraction and
Report Language.
%prep
# Check for cross-compile
%if "%{_build}" !=  "%{_host}"
echo "Cross-compile detected (build: %{_build}, host: %{_host})"
%global cross_compile 1
%endif

%setup -q
sed -i 's/-fstack-protector/&-all/' Configure

# Extract perl-cross if cross-compiling
%if %{?cross_compile}
%setup -T -D -q -b 1
cp -r ../perl-cross-%{perl_cross_version}/* . -v
%endif

%build
export BUILD_ZLIB=False
export BUILD_BZIP2=0
CFLAGS="%{_optflags}"

%if %{?cross_compile}
export CC="%{_host}-gcc"
export CXX="%{_host}-g++"
export AR="%{_host}-ar"
export AS="%{_host}-as"
export RANLIB="%{_host}-ranlib"
export LD="%{_host}-ld"
export STRIP="%{_host}-strip"

./configure \
    -Dvendorprefix=%{_prefix} \
    -Dman1dir=%{_mandir}/man1 \
    -Dman3dir=%{_mandir}/man3 \
    -Dpager=%{_bindir}"/less -isR" \
    -Duseshrplib \
    -Dusethreads \
    -DPERL_RANDOM_DEVICE="/dev/erandom" \
    --target=%{_host} \
    --host=%{_host} \
    --build=$MACHTYPE
%else
sh Configure -des \
    -Dprefix=%{_prefix} \
    -Dvendorprefix=%{_prefix} \
    -Dman1dir=%{_mandir}/man1 \
    -Dman3dir=%{_mandir}/man3 \
    -Dpager=%{_bindir}"/less -isR" \
    -Duseshrplib \
    -Dusethreads \
    -DPERL_RANDOM_DEVICE="/dev/erandom"
%endif

make VERBOSE=1 %{?_smp_mflags}
%install
make DESTDIR=%{buildroot} install
unset BUILD_ZLIB BUILD_BZIP2
%check
sed -i '/02zlib.t/d' MANIFEST
sed -i '/cz-03zlib-v1.t/d' MANIFEST
sed -i '/cz-06gzsetp.t/d' MANIFEST
sed -i '/porting\/podcheck.t/d' MANIFEST
make test TEST_SKIP_VERSION_CHECK=1
%post   -p /sbin/ldconfig
%postun -p /sbin/ldconfig
%files
%defattr(-,root,root)
%{_bindir}/*
%dir %{_libdir}/perl5
%dir %{_libdir}/perl5/%{version}
%{_libdir}/perl5/%{version}/*
%{_mandir}/*/*

%changelog
*   Wed Oct 24 2018 Srivatsa S. Bhat (VMware) <srivatsa@csail.mit.edu> 5.28.0-2
-   Add provides perl(s)
*   Fri Sep 21 2018 Dweep Advani <dadvani@vmware.com> 5.28.0-1
-   Upgrade to version 5.28.0
*   Tue Oct 03 2017 Dheeraj Shetty <dheerajs@vmware.com> 5.24.1-4
-   CVE-2017-12837 and CVE-2017-12883 patch from
-   https://perl5.git.perl.org/perl.git/commitdiff/2be4edede4ae226e2eebd4eff28cedd2041f300f#patch1
*   Wed Jul 05 2017 Xiaolin Li <xiaolinl@vmware.com> 5.24.1-3
-   Rebuild perl after adding gdbm-devel package.
*   Thu Jun 15 2017 Chang Lee <changlee@vmware.com> 5.24.1-2
-   Updated %check
*   Mon Apr 3 2017 Robert Qi <qij@vmware.com> 5.24.1-1
-   Update to 5.24.1.
*   Thu Oct 20 2016 Xiaolin Li <xiaolinl@vmware.com> 5.22.1-5
-   CVE-2016-1238 patch from http://perl5.git.perl.org/perl.git/commit/cee96d52c39b1e7b36e1c62d38bcd8d86e9a41ab.
*   Mon Oct 10 2016 ChangLee <changlee@vmware.com> 5.22.1-4
-   Modified %check
*   Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 5.22.1-3
-   GA - Bump release of all rpms
*   Tue Jan 26 2016 Anish Swaminathan <anishs@vmware.com> 5.22.1-2
-   Enable threads
*   Tue Jan 12 2016 Anish Swaminathan <anishs@vmware.com> 5.22.1-1
-   Update version
*   Thu Jun 4 2015 Touseef Liaqat <tliaqat@vmware.com> 5.18.2-2
-   Provide /bin/perl.
*   Wed Nov 5 2014 Divya Thaluru <dthaluru@vmware.com> 5.18.2-1
-   Initial build. First version
